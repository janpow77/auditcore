"""In-memory list index: flat name/alias forms, rapidfuzz search and evidence-bearing hits."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from types import ModuleType
from typing import Protocol

from auditcore_common.optional import require_module
from auditcore_entity_matching import classify

from ._screening_rules import (
    Adjustment,
    ScreeningSettings,
    adjust_score,
    birth_years,
    split_multivalue,
)
from ._types import JsonObject
from .errors import DependencyError

_FUZZY = "Für den Namensabgleich ist 'auditcore_registry_sources[fuzzy]' zu installieren."


def _rapidfuzz() -> tuple[ModuleType, ModuleType]:
    return (
        require_module("rapidfuzz.fuzz", DependencyError, _FUZZY),
        require_module("rapidfuzz.process", DependencyError, _FUZZY),
    )


class EntryLike(Protocol):
    """What the index needs of an entry (``ListEntry`` or a legacy record)."""

    @property
    def entry_id(self) -> str:
        """Stable id within the list."""
        ...

    @property
    def schema(self) -> str:
        """Entity type (``Person``, ``Organization`` …)."""
        ...

    @property
    def name(self) -> str:
        """Spelling of the list."""
        ...

    @property
    def aliases(self) -> Sequence[str]:
        """Alternative spellings."""
        ...

    @property
    def birth_date(self) -> str:
        """Birth date field as listed."""
        ...

    @property
    def countries(self) -> str:
        """Country field as listed."""
        ...


@dataclass(frozen=True)
class ScreeningHit:
    """A hit: indication for review with the evidence needed to retrace it."""

    list_key: str
    list_name: str
    source_key: str | None
    entry: EntryLike
    matched_name: str
    matched_field: str
    matched_form: str
    raw_score: float
    score: float
    confidence: str
    adjustments: tuple[Adjustment, ...]
    dob_conflict: bool
    country_conflict: bool
    below_min_score: bool
    indicators: tuple[str, ...]
    aliases: tuple[str, ...]

    def to_dict(self) -> JsonObject:
        """JSON view."""
        entry = self.entry
        return {
            "list_key": self.list_key,
            "list_name": self.list_name,
            "source_key": self.source_key,
            "entry_id": entry.entry_id,
            "schema": entry.schema,
            "name": entry.name,
            "aliases": list(self.aliases),
            "birth_date": entry.birth_date,
            "countries": entry.countries,
            "matched_name": self.matched_name,
            "matched_field": self.matched_field,
            "raw_score": self.raw_score,
            "score": self.score,
            "confidence": self.confidence,
            "adjustments": [a.to_dict() for a in self.adjustments],
            "dob_conflict": self.dob_conflict,
            "country_conflict": self.country_conflict,
            "below_min_score": self.below_min_score,
            "indicators": list(self.indicators),
        }


class ListIndex:
    """In-memory comparison index of one list: names and aliases as flat forms."""

    def __init__(
        self,
        settings: ScreeningSettings,
        entries: Sequence[EntryLike],
        *,
        list_key: str,
        list_name: str,
        source_key: str | None,
    ) -> None:
        self.settings = settings
        self.list_key = list_key
        self.list_name = list_name
        self.source_key = source_key
        self.entries = list(entries)
        self.forms: list[str] = []
        self._owner: list[int] = []
        self._field: list[str] = []
        self._original: list[str] = []
        for position, entry in enumerate(self.entries):
            name_form = settings.norm(entry.name)
            if name_form:
                self._add(name_form, position, "name", entry.name)
            for alias in entry.aliases:
                alias_form = settings.norm(alias)
                if alias_form and alias_form != name_form:
                    self._add(alias_form, position, "alias", alias)

    def _add(self, form: str, owner: int, field_name: str, original: str) -> None:
        self.forms.append(form)
        self._owner.append(owner)
        self._field.append(field_name)
        self._original.append(original)

    def search(
        self,
        query: str,
        *,
        limit: int,
        min_score: float,
        schema: str | None = None,
        birth_date: str | None = None,
        country: str | None = None,
    ) -> list[ScreeningHit]:
        """Best form per entry at or above ``min_score`` (raw), adjusted, sorted, limited."""
        hits, _ = self.search_detailed(
            query,
            limit=limit,
            min_score=min_score,
            schema=schema,
            birth_date=birth_date,
            country=country,
        )
        return hits

    def search_detailed(
        self,
        query: str,
        *,
        limit: int,
        min_score: float,
        schema: str | None = None,
        birth_date: str | None = None,
        country: str | None = None,
    ) -> tuple[list[ScreeningHit], bool]:
        """Like :meth:`search`; the flag says whether hits were cut (limit or candidate cap)."""
        query_form = self.settings.norm(query)
        if not query_form or not self.forms:
            return [], False
        cap = self.settings.extract_limit.apply(limit)
        raw = self._extract(query_form, cap, min_score)
        hits = [
            self._hit(owner, value, position, query_form, min_score, birth_date, country)
            for owner, (value, position) in self._best_per_entry(raw).items()
            if not (schema and self.entries[owner].schema != schema)
        ]
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:limit], len(raw) >= cap or len(hits) > limit

    def _extract(self, query_form: str, cap: int, min_score: float) -> list[tuple[str, float, int]]:
        """rapidfuzz candidates ``(form, score, position)`` at or above ``min_score``."""
        fuzz, process = _rapidfuzz()
        found: list[tuple[str, float, int]] = process.extract(
            query_form,
            self.forms,
            scorer=fuzz.token_set_ratio,
            limit=cap,
            score_cutoff=min_score,
        )
        return found

    def _best_per_entry(
        self, raw: Sequence[tuple[str, float, int]]
    ) -> dict[int, tuple[float, int]]:
        """Highest score and its form position per entry, in first-seen order."""
        best: dict[int, tuple[float, int]] = {}
        for _form, value, position in raw:
            owner = self._owner[position]
            current = best.get(owner)
            if current is None or value > current[0]:
                best[owner] = (float(value), position)
        return best

    def _hit(
        self,
        owner: int,
        value: float,
        position: int,
        query_form: str,
        min_score: float,
        birth_date: str | None,
        country: str | None,
    ) -> ScreeningHit:
        """Adjust, classify and document one entry's best form."""
        settings = self.settings
        entry = self.entries[owner]
        adjusted, dob_conflict, country_conflict, adjustments = adjust_score(
            value,
            settings,
            entry_birth_date=entry.birth_date,
            entry_countries=entry.countries,
            birth_date=birth_date,
            country=country,
        )
        form = self.forms[position]
        confidence = classify(adjusted, settings.normalization, query_form, form)
        return ScreeningHit(
            list_key=self.list_key,
            list_name=self.list_name,
            source_key=self.source_key,
            entry=entry,
            matched_name=self._original[position],
            matched_field=self._field[position],
            matched_form=form,
            raw_score=value,
            score=round(adjusted, 1),
            confidence=confidence,
            adjustments=adjustments,
            dob_conflict=dob_conflict,
            country_conflict=country_conflict,
            below_min_score=adjusted < min_score,
            indicators=self._indicators(
                entry, value, adjusted, confidence, position, min_score, birth_date, country
            ),
            aliases=tuple(entry.aliases[: settings.alias_output_cap]),
        )

    def _indicators(
        self,
        entry: EntryLike,
        value: float,
        adjusted: float,
        confidence: str,
        position: int,
        min_score: float,
        birth_date: str | None,
        country: str | None,
    ) -> tuple[str, ...]:
        """Uncertainty indicators of a hit, in their fixed order."""
        rules = self.settings.normalization.classification
        assert rules is not None
        indicators = []
        if value >= rules.exact_from and confidence != "exact":
            indicators.append("token_subset")
        if self._field[position] == "alias":
            indicators.append("alias_match")
        if not (birth_date and birth_years(birth_date) and birth_years(entry.birth_date)):
            indicators.append("date_of_birth_not_compared")
        if not (country and split_multivalue(country) and split_multivalue(entry.countries)):
            indicators.append("country_not_compared")
        if adjusted < min_score:
            indicators.append("below_min_score_after_adjustment")
        return tuple(indicators)
