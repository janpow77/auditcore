"""EU procurement thresholds by legal regime, contract type, authority type and date.

Model and validation of the ``eu_regimes`` block of profile schema 3
(``procurement.hvtg`` from 2026.10.1). A regime is one directive (public
contracts, utilities, concessions, defence and security); every threshold row
names the official text it was read in, and that text's wording is part of the
profile (``sources[...]["quote"]``). The block is independent of the national
tiers of the profile, so the EU thresholds can be queried on their own.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta

#: Decoded JSON object of the profile block.
Json = Mapping[str, object]
COMPARISON = "reached_or_exceeded"
_SOURCE_FIELDS = (
    "regulation",
    "official_journal",
    "celex",
    "url",
    "retrieved_from",
    "retrieved_sha256",
    "retrieved_on",
    "quote",
)


class RegimeError(ValueError):
    """The ``eu_regimes`` block is incomplete or contradictory."""


@dataclass(frozen=True)
class Label:
    """German and English wording (terms of the directives)."""

    de: str
    en: str

    def to_dict(self) -> dict[str, str]:
        """JSON view."""
        return {"de": self.de, "en": self.en}


@dataclass(frozen=True)
class ThresholdRow:
    """One threshold valid from/to (inclusive), read in the official text ``source``."""

    valid_from: date
    valid_to: date
    value: int
    source: str
    provision: str


@dataclass(frozen=True)
class Series:
    """Thresholds over time of one contract type or of one authority type within it."""

    id: str
    label: Label
    legal_basis: str
    note: Label | None
    thresholds: tuple[ThresholdRow, ...]


@dataclass(frozen=True)
class ContractType:
    """Contract type of a regime; either own thresholds or one series per authority type."""

    series: Series
    authority_types: tuple[Series, ...]

    @property
    def id(self) -> str:
        """Identifier within the regime."""
        return self.series.id


@dataclass(frozen=True)
class Regime:
    """One directive with its contract types."""

    id: str
    directive: str
    celex: str
    label: Label
    buyer: Label
    legal_basis: str
    national_reference: str
    note: Label | None
    contract_types: tuple[ContractType, ...]


@dataclass(frozen=True)
class RegimeTable:
    """All regimes of a profile with their sources and the link to the prechecks."""

    comparison: str
    comparison_reference: str
    regimes: tuple[Regime, ...]
    sources: Mapping[str, Mapping[str, str]]
    precheck_regime: str
    precheck_categories: Mapping[str, str]
    not_entered: str

    def regime(self, regime_id: str) -> Regime:
        """Regime by identifier.

        Raises:
            ValueError: unknown regime.
        """
        for regime in self.regimes:
            if regime.id == regime_id:
                return regime
        known = tuple(r.id for r in self.regimes)
        raise ValueError(f"regime muss eine von {known} sein.")


def find_series(regime: Regime, contract_type: str, authority_type: str | None) -> Series | None:
    """Series of a contract type; ``None`` when the authority type decides and is missing.

    Raises:
        ValueError: unknown contract type or authority type.
    """
    for candidate in regime.contract_types:
        if candidate.id != contract_type:
            continue
        if not candidate.authority_types:
            return candidate.series
        if authority_type is None:
            return None
        for series in candidate.authority_types:
            if series.id == authority_type:
                return series
        known = tuple(s.id for s in candidate.authority_types)
        raise ValueError(f"authority_type muss eine von {known} oder None sein.")
    known = tuple(c.id for c in regime.contract_types)
    raise ValueError(f"contract_type muss eine von {known} sein.")


def row_on(series: Series, on: date) -> ThresholdRow | None:
    """Row valid on ``on``; no fallback to a neighbouring row."""
    for row in series.thresholds:
        if row.valid_from <= on <= row.valid_to:
            return row
    return None


def row_for_year(series: Series, year: int) -> ThresholdRow | None:
    """Row of 31 December if one value holds gaplessly for the whole calendar year."""
    first, last = date(year, 1, 1), date(year, 12, 31)
    rows = [r for r in series.thresholds if r.valid_from <= last and r.valid_to >= first]
    if not rows or rows[0].valid_from > first or rows[-1].valid_to < last:
        return None
    gapless = all(
        after.valid_from == before.valid_to + timedelta(days=1)
        for before, after in zip(rows, rows[1:], strict=False)
    )
    return rows[-1] if gapless and len({r.value for r in rows}) == 1 else None


def spaced_amount(value: int) -> str:
    """Amount as printed in the Official Journal (``5 186 000 EUR``)."""
    return f"{value:,}".replace(",", " ") + " EUR"


def _obj(value: object, what: str) -> Json:
    if not isinstance(value, Mapping):
        raise RegimeError(f"{what} ist kein Objekt.")
    return value


def _items(value: object, what: str) -> Sequence[object]:
    if not isinstance(value, list) or not value:
        raise RegimeError(f"{what} fehlt oder ist leer.")
    return value


def _text(row: Json, key: str, what: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RegimeError(f"{what}: '{key}' fehlt.")
    return value


def _label(row: Json, key: str, what: str) -> Label:
    label = _obj(row.get(key), f"{what}: '{key}'")
    return Label(_text(label, "de", f"{what}: '{key}'"), _text(label, "en", f"{what}: '{key}'"))


def _note(row: Json, what: str) -> Label | None:
    return None if row.get("note") is None else _label(row, "note", what)


def _sources(block: Json) -> dict[str, Mapping[str, str]]:
    sources: dict[str, Mapping[str, str]] = {}
    for celex, raw in _obj(block.get("sources"), "sources").items():
        entry = _obj(raw, f"Quelle {celex}")
        fields = {key: _text(entry, key, f"Quelle {celex}") for key in _SOURCE_FIELDS}
        if fields["celex"] != celex or len(fields["retrieved_sha256"]) != 64:
            raise RegimeError(f"Quelle {celex}: CELEX-Nummer oder Prüfsumme ist fehlerhaft.")
        extra = {k: v for k, v in entry.items() if isinstance(v, str) and k not in fields}
        sources[str(celex)] = {**fields, **extra}
    return sources


def _row(raw: object, sources: Mapping[str, Mapping[str, str]], what: str) -> ThresholdRow:
    row = _obj(raw, what)
    start = date.fromisoformat(_text(row, "valid_from", what))
    end = date.fromisoformat(_text(row, "valid_to", what))
    value, source = row.get("value"), _text(row, "source", what)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0 or end < start:
        raise RegimeError(f"{what}: Wert oder Zeitraum ist fehlerhaft.")
    if source not in sources:
        raise RegimeError(f"{what}: EU-Schwellenwert ohne amtliche Fundstelle.")
    if spaced_amount(value) not in sources[source]["quote"]:
        raise RegimeError(f"{what}: {value} EUR steht nicht im Wortlaut der Quelle {source}.")
    return ThresholdRow(start, end, value, source, _text(row, "provision", what))


def _series(raw: object, sources: Mapping[str, Mapping[str, str]], what: str) -> Series:
    row = _obj(raw, what)
    name = f"{what} '{_text(row, 'id', what)}'"
    rows = [_row(r, sources, name) for r in _items(row.get("thresholds"), f"{name}: thresholds")]
    rows.sort(key=lambda r: r.valid_from)
    for before, after in zip(rows, rows[1:], strict=False):
        if after.valid_from <= before.valid_to:
            raise RegimeError(f"{name}: Zeiträume überschneiden sich.")
    return Series(
        _text(row, "id", what),
        _label(row, "label", name),
        _text(row, "legal_basis", name),
        _note(row, name),
        tuple(rows),
    )


def _contract_type(
    raw: object, sources: Mapping[str, Mapping[str, str]], what: str
) -> ContractType:
    row = _obj(raw, what)
    if ("thresholds" in row) == ("authority_types" in row):
        raise RegimeError(f"{what}: entweder thresholds oder authority_types angeben.")
    if "thresholds" in row:
        return ContractType(_series(row, sources, what), ())
    name = f"{what} '{_text(row, 'id', what)}'"
    types = tuple(
        _series(r, sources, f"{name}: Auftraggeberart")
        for r in _items(row.get("authority_types"), f"{name}: authority_types")
    )
    head = Series(
        _text(row, "id", what),
        _label(row, "label", name),
        _text(row, "legal_basis", name),
        _note(row, name),
        (),
    )
    _unique([s.id for s in types], name)
    return ContractType(head, types)


def _regime(raw: object, sources: Mapping[str, Mapping[str, str]]) -> Regime:
    row = _obj(raw, "Regime")
    name = f"Regime '{_text(row, 'id', 'Regime')}'"
    types = tuple(
        _contract_type(r, sources, f"{name}: Auftragsart")
        for r in _items(row.get("contract_types"), f"{name}: contract_types")
    )
    _unique([c.id for c in types], name)
    return Regime(
        _text(row, "id", "Regime"),
        _text(row, "directive", name),
        _text(row, "celex", name),
        _label(row, "label", name),
        _label(row, "buyer", name),
        _text(row, "legal_basis", name),
        _text(row, "national_reference", name),
        _note(row, name),
        types,
    )


def _unique(names: Sequence[str], what: str) -> None:
    if len(set(names)) != len(names):
        raise RegimeError(f"{what}: Kennungen sind nicht eindeutig.")


def parse_regimes(raw: object) -> RegimeTable:
    """Validate the ``eu_regimes`` block; nothing is defaulted silently.

    Raises:
        RegimeError: missing source, value not in the quoted wording, overlapping
            periods, unknown references or duplicate identifiers.
    """
    block = _obj(raw, "eu_regimes")
    try:
        sources = _sources(block)
        regimes = tuple(_regime(r, sources) for r in _items(block.get("regimes"), "regimes"))
    except ValueError as exc:
        raise RegimeError(str(exc)) from exc
    _unique([r.id for r in regimes], "eu_regimes")
    if _text(block, "comparison", "eu_regimes") != COMPARISON:
        raise RegimeError("eu_regimes: unbekannte Vergleichsregel.")
    view = _obj(block.get("precheck_view"), "precheck_view")
    categories = {str(k): str(v) for k, v in _obj(view.get("categories"), "precheck_view").items()}
    table = RegimeTable(
        COMPARISON,
        _text(block, "comparison_reference", "eu_regimes"),
        regimes,
        sources,
        _text(view, "regime", "precheck_view"),
        categories,
        _text(block, "not_entered", "eu_regimes"),
    )
    try:
        known = {c.id for c in table.regime(table.precheck_regime).contract_types}
    except ValueError as exc:
        raise RegimeError("precheck_view: unbekanntes Regime.") from exc
    if not set(categories.values()) <= known:
        raise RegimeError("precheck_view: unbekannte Auftragsart.")
    return table
