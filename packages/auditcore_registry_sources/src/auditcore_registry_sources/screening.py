"""Name screening against sanctions list snapshots (optional extra ``fuzzy``).

Reproduces the characterized method of audit_designer and flowworkshop as
explicit profiles: normalisation through ``auditcore_entity_matching``
(profile named in the screening profile), ``rapidfuzz`` token-set ratio over
names *and* aliases, the best comparison form per entry, a deterministic
date-of-birth/country adjustment and the score classes of the normalisation
profile.

**A hit is an indication for manual review, never a finding.** Every hit
carries the matched spelling, the raw and the adjusted score, the
adjustments with reasons and uncertainty indicators. Every requested list
has a finding: a list without inventory is *not searched* and must not look
like a list without hits. A result without hits proves nothing about lists
that were not searched (status ``INCOMPLETE``).
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from auditcore_entity_matching import Profile as NormalizationProfile
from auditcore_entity_matching import classify, normalize
from auditcore_entity_matching import load_profile as load_normalization

from .errors import DependencyError, ProfileError, QueryError
from .model import ListSnapshot
from .profiles import RegistryProfile

_MULTI = re.compile(r"[;,]")
_YEAR = re.compile(r"\b(\d{4})\b")

NOT_SEARCHED_NOTE = (
    "Für diese Liste liegt kein Bestand vor. Sie wurde nicht abgefragt; das Ergebnis "
    "sagt über sie nichts aus."
)


def _rapidfuzz() -> tuple[Any, Any]:
    try:
        from rapidfuzz import fuzz, process
    except ImportError as exc:  # pragma: no cover - exercised in the installed smoke test
        raise DependencyError(
            "Für den Namensabgleich ist 'auditcore_registry_sources[fuzzy]' zu installieren."
        ) from exc
    return fuzz, process


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
class LimitRule:
    """``max(value, floor) * factor`` (``floor`` ``None``: ``value * factor``)."""

    floor: int | None
    factor: int

    def apply(self, value: int) -> int:
        """Apply the rule."""
        base = value if self.floor is None else max(value, self.floor)
        return base * self.factor


@dataclass(frozen=True)
class ScreeningSettings:
    """Typed view of a ``screening`` profile using the rapidfuzz method."""

    profile: RegistryProfile
    normalization: NormalizationProfile
    default_min_score: float
    min_score_range: tuple[float, float]
    min_query_length: int
    per_list_limit: LimitRule
    extract_limit: LimitRule
    alias_output_cap: int
    dob_bonus: float
    dob_malus: float
    country_bonus: float
    country_malus: float
    score_range: tuple[float, float]
    entity_schemas: tuple[str, ...]
    notice: str
    limitations: tuple[str, ...]

    @classmethod
    def from_profile(cls, profile: RegistryProfile) -> ScreeningSettings:
        """Validate and type a screening profile; nothing is defaulted."""
        profile.require_kind("screening")
        if profile.setting("algorithm") != "rapidfuzz_token_set":
            raise ProfileError(f"Profil {profile.id} nutzt nicht den rapidfuzz-Abgleich.")
        ref = profile.setting("normalization")
        normalization = load_normalization(ref["id"], ref["version"])
        if normalization.classification is None:
            raise ProfileError("Das Normalisierungsprofil enthält keine Klassengrenzen.")
        low, high = profile.setting("min_score_range")
        dob = profile.setting("date_of_birth")
        if dob["compare"] != "year":
            raise ProfileError("Nur der Jahresabgleich des Geburtsdatums ist charakterisiert.")
        country = profile.setting("country")
        per_list = profile.setting("per_list_limit")
        extract = profile.setting("extract_limit")
        score_low, score_high = profile.setting("score_range")
        return cls(
            profile=profile,
            normalization=normalization,
            default_min_score=float(profile.setting("default_min_score")),
            min_score_range=(float(low), float(high)),
            min_query_length=int(profile.setting("min_query_length")),
            per_list_limit=LimitRule(per_list["floor"], int(per_list["factor"])),
            extract_limit=LimitRule(extract["floor"], int(extract["factor"])),
            alias_output_cap=int(profile.setting("alias_output_cap")),
            dob_bonus=float(dob["bonus"]),
            dob_malus=float(dob["malus"]),
            country_bonus=float(country["bonus"]),
            country_malus=float(country["malus"]),
            score_range=(float(score_low), float(score_high)),
            entity_schemas=tuple(profile.setting("entity_schemas")),
            notice=str(profile.setting("notice")),
            limitations=tuple(profile.setting("limitations")),
        )

    def norm(self, text: str | None) -> str:
        """Comparison form under the profile's normalisation."""
        return normalize(text, self.normalization)


def split_multivalue(raw: str | None) -> list[str]:
    """Multi-valued list field (separators ``;`` and ``,``) → stripped parts."""
    if not raw:
        return []
    return [part.strip() for part in _MULTI.split(raw) if part.strip()]


def birth_years(raw: str | None) -> set[str]:
    """Four-digit years of a birth date field; only the year is compared."""
    years = set()
    for part in split_multivalue(raw):
        found = _YEAR.search(part)
        if found:
            years.add(found.group(1))
    return years


@dataclass(frozen=True)
class Adjustment:
    """One deterministic change of the raw score, with its reason."""

    kind: str
    points: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        """JSON view."""
        return {"kind": self.kind, "points": self.points, "reason": self.reason}


def adjust_score(
    score: float,
    settings: ScreeningSettings,
    *,
    entry_birth_date: str,
    entry_countries: str,
    birth_date: str | None,
    country: str | None,
) -> tuple[float, bool, bool, tuple[Adjustment, ...]]:
    """Date-of-birth/country bonus and malus; returns score, conflicts and adjustments.

    Only applied when both sides state a value; the score stays within the
    profile's score range.
    """
    dob_conflict = country_conflict = False
    adjustments: list[Adjustment] = []
    if birth_date:
        asked, listed = birth_years(birth_date), birth_years(entry_birth_date)
        if asked and listed:
            if asked & listed:
                score += settings.dob_bonus
                adjustments.append(
                    Adjustment("date_of_birth", settings.dob_bonus, "Geburtsjahr stimmt überein.")
                )
            else:
                score -= settings.dob_malus
                dob_conflict = True
                adjustments.append(
                    Adjustment(
                        "date_of_birth",
                        -settings.dob_malus,
                        "Geburtsjahr widerspricht dem Eintrag.",
                    )
                )
    if country:
        asked_c = {n for part in split_multivalue(country) if (n := settings.norm(part))}
        listed_c = {n for part in split_multivalue(entry_countries) if (n := settings.norm(part))}
        if asked_c and listed_c:
            if asked_c & listed_c:
                score += settings.country_bonus
                adjustments.append(
                    Adjustment("country", settings.country_bonus, "Land stimmt überein.")
                )
            else:
                score -= settings.country_malus
                country_conflict = True
                adjustments.append(
                    Adjustment("country", -settings.country_malus, "Land widerspricht dem Eintrag.")
                )
    low, high = settings.score_range
    return max(low, min(high, score)), dob_conflict, country_conflict, tuple(adjustments)


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

    def to_dict(self) -> dict[str, Any]:
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
        settings = self.settings
        query_form = settings.norm(query)
        if not query_form or not self.forms:
            return [], False
        fuzz, process = _rapidfuzz()
        cap = settings.extract_limit.apply(limit)
        raw = process.extract(
            query_form,
            self.forms,
            scorer=fuzz.token_set_ratio,
            limit=cap,
            score_cutoff=min_score,
        )
        best: dict[int, tuple[float, int]] = {}
        for _form, value, position in raw:
            owner = self._owner[position]
            current = best.get(owner)
            if current is None or value > current[0]:
                best[owner] = (float(value), position)
        hits: list[ScreeningHit] = []
        rules = settings.normalization.classification
        assert rules is not None
        for owner, (value, position) in best.items():
            entry = self.entries[owner]
            if schema and entry.schema != schema:
                continue
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
            hits.append(
                ScreeningHit(
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
                    indicators=tuple(indicators),
                    aliases=tuple(entry.aliases[: settings.alias_output_cap]),
                )
            )
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:limit], len(raw) >= cap or len(hits) > limit


@dataclass(frozen=True)
class ListFinding:
    """What one requested list contributed; ``searched`` is the decisive value."""

    list_key: str
    list_name: str
    source_key: str | None
    searched: bool
    entry_count: int
    as_of: str | None
    retrieved_at: str | None
    hit_count: int
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """JSON view."""
        return {
            "list_key": self.list_key,
            "list_name": self.list_name,
            "source_key": self.source_key,
            "searched": self.searched,
            "entry_count": self.entry_count,
            "as_of": self.as_of,
            "retrieved_at": self.retrieved_at,
            "hit_count": self.hit_count,
            "note": self.note,
        }


@dataclass(frozen=True)
class ScreeningResult:
    """Screening result contract (``auditcore_registry_sources.screening/1``)."""

    status: str
    query: str
    normalized_query: str
    min_score: float
    limit: int
    profile: Mapping[str, str]
    normalization: Mapping[str, str]
    findings: tuple[ListFinding, ...]
    hits: tuple[ScreeningHit, ...]
    total_hits: int
    truncated: bool
    notice: str
    limitations: tuple[str, ...]
    decisions: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)

    @property
    def coverage_complete(self) -> bool:
        """True only if every requested list was searched."""
        return all(f.searched for f in self.findings)

    def to_dict(self) -> dict[str, Any]:
        """JSON view."""
        return {
            "contract": "auditcore_registry_sources.screening/1",
            "status": self.status,
            "query": self.query,
            "normalized_query": self.normalized_query,
            "min_score": self.min_score,
            "limit": self.limit,
            "profile": dict(self.profile),
            "normalization": dict(self.normalization),
            "coverage_complete": self.coverage_complete,
            "findings": [f.to_dict() for f in self.findings],
            "hits": [h.to_dict() for h in self.hits],
            "total_hits": self.total_hits,
            "truncated": self.truncated,
            "notice": self.notice,
            "limitations": list(self.limitations),
            "decisions": [dict(d) for d in self.decisions],
        }


def validate_query(
    settings: ScreeningSettings,
    name: str,
    *,
    min_score: float | None,
    schema: str | None,
) -> tuple[str, float, str | None]:
    """Check the input against the profile; return name, minimum score and schema."""
    if not isinstance(name, str) or not name.strip():
        raise QueryError("Pflichtangabe fehlt: Name.")
    stripped = name.strip()
    if len(stripped) < settings.min_query_length:
        raise QueryError(
            f"Bitte mindestens {settings.min_query_length} Zeichen angeben; kürzere Eingaben "
            "treffen so viele Einträge, dass das Ergebnis nichts aussagt."
        )
    value = settings.default_min_score if min_score is None else float(min_score)
    low, high = settings.min_score_range
    if not low <= value <= high:
        raise QueryError(f"Der Mindestwert liegt zwischen {low:g} und {high:g}.")
    chosen = None
    if schema:
        allowed = {s.casefold(): s for s in settings.entity_schemas}
        chosen = allowed.get(schema.casefold())
        if chosen is None:
            raise QueryError(
                f"Unbekannter Eintragstyp; zulässig: {', '.join(settings.entity_schemas)}."
            )
    return stripped, value, chosen


def screen(
    name: str,
    snapshots: Sequence[ListSnapshot],
    profile: RegistryProfile,
    *,
    limit: int = 15,
    min_score: float | None = None,
    schema: str | None = None,
    birth_date: str | None = None,
    country: str | None = None,
) -> ScreeningResult:
    """Screen a name against list snapshots under an explicitly chosen profile."""
    settings = ScreeningSettings.from_profile(profile)
    if limit < 1:
        raise QueryError("Das Trefferlimit muss mindestens 1 sein.")
    query, value, chosen_schema = validate_query(settings, name, min_score=min_score, schema=schema)
    per_list = settings.per_list_limit.apply(limit)
    list_truncated = False
    findings: list[ListFinding] = []
    hits: list[ScreeningHit] = []
    for snapshot in snapshots:
        sanctions_list = snapshot.list
        if not snapshot.entries:
            findings.append(
                ListFinding(
                    sanctions_list.key,
                    sanctions_list.name,
                    sanctions_list.source_key,
                    searched=False,
                    entry_count=0,
                    as_of=snapshot.as_of,
                    retrieved_at=snapshot.retrieved_at,
                    hit_count=0,
                    note=snapshot.note or NOT_SEARCHED_NOTE,
                )
            )
            continue
        index = ListIndex(
            settings,
            snapshot.entries,
            list_key=sanctions_list.key,
            list_name=sanctions_list.name,
            source_key=sanctions_list.source_key,
        )
        found, cut = index.search_detailed(
            query,
            limit=per_list,
            min_score=value,
            schema=chosen_schema,
            birth_date=birth_date,
            country=country,
        )
        list_truncated = list_truncated or cut
        findings.append(
            ListFinding(
                sanctions_list.key,
                sanctions_list.name,
                sanctions_list.source_key,
                searched=True,
                entry_count=len(snapshot.entries),
                as_of=snapshot.as_of,
                retrieved_at=snapshot.retrieved_at,
                hit_count=len(found),
                note=snapshot.note,
            )
        )
        hits.extend(found)
    hits.sort(key=lambda h: h.score, reverse=True)
    searched = [f for f in findings if f.searched]
    if hits:
        status = "HITS"
    elif not searched:
        status = "NOT_SEARCHED"
    elif len(searched) < len(findings):
        status = "INCOMPLETE"
    else:
        status = "NO_HITS"
    limitations = list(settings.limitations)
    if status in ("NO_HITS", "INCOMPLETE"):
        limitations.append(
            "Ein Ergebnis ohne Treffer belegt keine Unbedenklichkeit; es bezieht sich nur auf "
            "die abgefragten Listen in ihrem angegebenen Stand."
        )
    return ScreeningResult(
        status=status,
        query=query,
        normalized_query=settings.norm(query),
        min_score=value,
        limit=limit,
        profile=profile.reference,
        normalization=settings.normalization.reference,
        findings=tuple(findings),
        hits=tuple(hits[:limit]),
        total_hits=len(hits),
        truncated=list_truncated or len(hits) > limit,
        notice=settings.notice,
        limitations=tuple(limitations),
        decisions=profile.decisions,
    )
