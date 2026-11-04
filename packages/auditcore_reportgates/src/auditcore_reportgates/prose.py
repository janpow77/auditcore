"""Prose number gate: every number in a paragraph must be bound to a report value.

A claim is checked against the values of the objects the paragraph refers to.
It *matches* within printed rounding (after unit conversion), it
*contradicts* when the nearest compatible value lies within the neighbourhood
(default 10 %), and it is *unbound* otherwise. Contradicted and unbound
claims both fail the gate: a number that is not in the object is not
verified. Context numbers that are deliberately not in the object are
declared by the caller as ``context`` values and bind like object values.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, replace
from decimal import Decimal
from enum import StrEnum

from .numbers import PrintedNumber, format_de, read_number, relative_deviation, same_value
from .syntax import DEFAULT_SYNTAX, ClaimSyntax, masked, number_pattern
from .units import PLAIN, Unit, conversion_exponent, unit_of
from .verdict import Finding, GateResult, Verdict, decide

NEIGHBOURHOOD = Decimal("0.10")
"""Relative distance up to which an unequal value counts as the meant value."""

UNIT_INHERITANCE_DISTANCE = 40
"""Characters within which a number without unit takes the unit of the next one."""

YEAR_RANGE = (1900, 2100)

NO_CLAIMS = "ohne_pruefbare_zahl"
"""Reason of a paragraph without numbers; neutral for :func:`combine`."""

_YEAR_CONTEXT = re.compile(
    r"\b(?:im|seit|Jahre?s?n?|Zeitraum|Zeitraums|Haushaltsjahr|Berichtsjahr|Förderjahr)"
    r"\s+(?:dem\s+|den\s+|Jahre?n?\s+)?$",
    re.IGNORECASE,
)
"""Strong year context: a year word or ``im``/``seit`` directly before the number."""
_WEAK_YEAR_CONTEXT = re.compile(
    r"\b(?:bis|ab|vor|nach|von|vom|zwischen)\s+(?:dem\s+|den\s+)?$", re.IGNORECASE
)
"""Short prepositions: a year only without counter-evidence (``bis 2050 Vorhaben``)."""
_COUNT_AFTER = re.compile(
    r"^\s?(?:Vorhaben|Projekt\w*|Teilnehm\w*|Person\w*|Unternehm\w*|Beschäftigt\w*"
    r"|Begünstigt\w*|Förderf\w*|Fälle\w*|Anträge\w*|Arbeitsplätze\w*|Stellen"
    r"|Einrichtung\w*|Kommunen|Gemeinden|Betriebe\w*|Haushalte\w*|Schüler\w*"
    r"|Studierend\w*|Euro|EUR)\b",
)
"""A count word or currency after the number is counter-evidence against a year."""
_SENTENCE_START = re.compile(r"(?:^|[.;:!?]\s+)\s*$")
_VERB_OR_COMMA_AFTER = re.compile(r"^\s?(?:,|[a-zäöüß]\w*\b)")
"""At sentence start, ``2023 stieg`` / ``2023,`` reads as a year; nouns are capitalised."""
_YEAR_LINK = re.compile(r"^\s*(?:[-–]|und|bis|bzw\.|oder|sowie|,)\s*$")
_YEAR_RANGE_AFTER = re.compile(r"^\s?[-–]\s?\d{4}(?!\d)")
_ABBREVIATION = re.compile(
    r"\b(?:bzw|ca|rd|ggf|inkl|zzgl|evtl|Mio|Mrd|Tsd|Nr|Abs|Art|vgl|z|B|d|h|u|a)\."
)
_SENTENCE_END = re.compile(r"[.;:!?]\s+[A-ZÄÖÜ]")


@dataclass(frozen=True)
class Claim:
    """A number printed in prose with its unit and position."""

    number: PrintedNumber
    unit: Unit
    position: int
    unit_stated: bool
    year: bool = False
    unit_text: str = ""
    """Unit token as printed (``"Mio. Euro"``), inherited tokens included."""
    unit_inherited: bool = False
    """Unit taken from the next number in the sentence (``"8,4 bzw. 8,5 %"``)."""
    token: str = ""
    """Printed claim with sign and its own unit, stripped (``"– 5,1 %"``)."""

    @property
    def is_year(self) -> bool:
        """Read as a year: decided at extraction from context or ``allowed_years``."""
        return self.year


def _year_like(claim: Claim) -> bool:
    """Integer 1900..2100 without unit and without thousands point (``2.024`` is no year)."""
    low, high = YEAR_RANGE
    value = claim.number.value
    return (
        not claim.unit_stated
        and claim.number.decimals == 0
        and "." not in claim.number.text
        and value >= 0
        and value == value.to_integral_value()
        and low <= value <= high
    )


@dataclass(frozen=True)
class BoundValue:
    """A value a claim may refer to: object value or declared context value."""

    number: PrintedNumber
    unit: Unit
    source: str


class ClaimStatus(StrEnum):
    """Outcome for one claim."""

    MATCH = "match"
    CONTRADICTION = "contradiction"
    UNBOUND = "unbound"


@dataclass(frozen=True)
class ClaimCheck:
    """Status of a claim and the value it was compared with."""

    claim: Claim
    status: ClaimStatus
    nearest: BoundValue | None = None
    deviation: Decimal | None = None


def _read(match: re.Match[str]) -> PrintedNumber | None:
    groups = match.groupdict()
    if groups.get("ambiguous"):
        return None
    point = groups.get("point")
    if point:
        return PrintedNumber(Decimal(point), len(point.split(".", 1)[1]), point)
    return read_number(match["number"])


def _raw_claims(source: str, syntax: ClaimSyntax) -> tuple[list[tuple[Claim, int]], list[str]]:
    found: list[tuple[Claim, int]] = []
    ambiguous: list[str] = []
    for match in number_pattern(syntax).finditer(source):
        token = match.group().strip()
        number = _read(match)
        if number is None:
            ambiguous.append(token)
            continue
        if match["sign"]:
            number = PrintedNumber(-number.value, number.decimals, token)
        unit_text = match["unit"] or ""
        unit = unit_of(unit_text) if unit_text else PLAIN
        claim = Claim(
            number, unit, match.start(), bool(unit_text), unit_text=unit_text, token=token
        )
        found.append((claim, match.end()))
    return found, ambiguous


def _counter_evidence(source: str, raw: Sequence[tuple[Claim, int]], index: int) -> bool:
    """Count word after the number, or a range partner that carries a unit or count word."""
    end = raw[index][1]
    if _COUNT_AFTER.match(source[end:]):
        return True
    if index + 1 < len(raw):
        partner, partner_end = raw[index + 1]
        if _YEAR_LINK.match(source[end : partner.position]) and (
            partner.unit_stated or _COUNT_AFTER.match(source[partner_end:])
        ):
            return True
    return False


def _year_context(source: str, raw: Sequence[tuple[Claim, int]], index: int) -> bool:
    claim, end = raw[index]
    before, after = source[: claim.position], source[end:]
    if _counter_evidence(source, raw, index):
        return False
    return (
        _YEAR_CONTEXT.search(before) is not None
        or _YEAR_RANGE_AFTER.match(after) is not None
        or _WEAK_YEAR_CONTEXT.search(before) is not None
        or (
            _SENTENCE_START.search(before) is not None
            and _VERB_OR_COMMA_AFTER.match(after) is not None
        )
    )


def _years(source: str, raw: Sequence[tuple[Claim, int]], allowed: frozenset[int]) -> list[bool]:
    """Year flags: year-like and either in ``allowed`` or in year context.

    Counter-evidence (count word or unit after the number or after its range
    partner) beats every context, but not ``allowed_years``.
    """
    flags: list[bool] = []
    for index, (claim, _) in enumerate(raw):
        if not _year_like(claim):
            flags.append(False)
            continue
        linked = (
            index > 0
            and flags[index - 1]
            and _YEAR_LINK.match(source[raw[index - 1][1] : claim.position]) is not None
            and not _COUNT_AFTER.match(source[raw[index][1] :])
        )
        flags.append(
            int(claim.number.value) in allowed or linked or _year_context(source, raw, index)
        )
    return flags


def _inherited(source: str, end: int, following: Sequence[tuple[Claim, int]]) -> Claim | None:
    for claim, _ in following:
        gap = source[end : claim.position]
        if len(gap) > UNIT_INHERITANCE_DISTANCE:
            return None
        if _SENTENCE_END.search(_ABBREVIATION.sub("  ", gap)):
            return None
        if claim.unit_stated:
            return claim
    return None


def extract_claims(
    text: str, *, allowed_years: Iterable[int] = (), syntax: ClaimSyntax = DEFAULT_SYNTAX
) -> list[Claim]:
    """All numbers of a paragraph; dates, footnotes and cross references are masked.

    An integer 1900..2100 is a year only in year context or when listed in
    ``allowed_years``. Context is a year word or ``im``/``seit`` before it, a
    range ``2022–2024``, a year list ``2021 und 2022``, a short preposition
    (``bis``, ``ab``, ``von``, ``vor``, ``nach``, ``zwischen``) or the start of a
    sentence followed by a verb or comma (``2023 stieg …``). A unit (``Euro``,
    ``%``) or count word (``Vorhaben``, ``Teilnehmende``) after the number or
    its range partner is counter-evidence and beats the context
    (``bis 2050 Vorhaben``, ``zwischen 1950 und 2100 Euro``); only
    ``allowed_years`` overrides it. With a thousands point it is never a year.
    A number without unit inherits the unit of the next number in the same
    sentence (``"8,4 bzw. 8,5 %"``); years never inherit.

    ``syntax`` sets the unit set, the reading of a lone point and the masks
    (:class:`~.syntax.ClaimSyntax`); the default is the strict reading.
    """
    source = masked(text, syntax)
    raw, _ = _raw_claims(source, syntax)
    flags = _years(source, raw, frozenset(allowed_years))
    raw = [(replace(c, year=flag), end) for (c, end), flag in zip(raw, flags, strict=True)]
    claims: list[Claim] = []
    for index, (claim, end) in enumerate(raw):
        if claim.unit_stated or claim.is_year:
            claims.append(claim)
            continue
        donor = _inherited(source, end, raw[index + 1 :])
        if donor is not None:
            claim = replace(
                claim,
                unit=donor.unit,
                unit_stated=True,
                unit_text=donor.unit_text,
                unit_inherited=True,
            )
        claims.append(claim)
    return claims


def ambiguous_numbers(text: str, *, syntax: ClaimSyntax = DEFAULT_SYNTAX) -> list[str]:
    """Numbers that cannot be read unambiguously (``"2.5 Mio."``); never split into parts.

    Empty for :attr:`~.syntax.PointReading.SPLIT`, which splits instead.
    """
    return _raw_claims(masked(text, syntax), syntax)[1]


def _converted(value: BoundValue, claim: Claim) -> PrintedNumber | None:
    exponent = conversion_exponent(value.unit, claim.unit)
    if exponent is None:
        return None
    decimals = value.number.decimals
    shifted = None if decimals is None else decimals - exponent
    return PrintedNumber(value.number.value.scaleb(exponent), shifted, value.number.text)


def check_claim(
    claim: Claim, values: Iterable[BoundValue], *, neighbourhood: Decimal = NEIGHBOURHOOD
) -> ClaimCheck:
    """Compare one claim with all unit-compatible values."""
    nearest: tuple[Decimal, BoundValue] | None = None
    for value in values:
        converted = _converted(value, claim)
        if converted is None:
            continue
        if same_value(converted, claim.number):
            return ClaimCheck(claim, ClaimStatus.MATCH, value, Decimal(0))
        deviation = relative_deviation(converted.value, claim.number.value)
        if deviation is not None and (nearest is None or deviation < nearest[0]):
            nearest = (deviation, value)
    if nearest is not None and nearest[0] <= neighbourhood:
        return ClaimCheck(claim, ClaimStatus.CONTRADICTION, nearest[1], nearest[0])
    if nearest is not None:
        return ClaimCheck(claim, ClaimStatus.UNBOUND, nearest[1], nearest[0])
    return ClaimCheck(claim, ClaimStatus.UNBOUND)


def _finding(check: ClaimCheck, location: str) -> Finding:
    nearest = check.nearest
    expected = "" if nearest is None else f"{nearest.number.text} ({nearest.source})"
    deviation = (
        "" if check.deviation is None else f", Abweichung {format_de(check.deviation * 100, 1)} %"
    )
    messages = {
        ClaimStatus.CONTRADICTION: "Zahl widerspricht dem gemeinten Objektwert",
        ClaimStatus.UNBOUND: "Zahl ist an keinen Objekt- oder Kontextwert gebunden",
    }
    return Finding(
        code=check.status.value,
        message=messages[check.status] + deviation,
        location=location,
        expected=expected,
        actual=check.claim.number.text,
    )


def check_paragraph(
    text: str,
    values: Sequence[BoundValue],
    *,
    location: str = "",
    gate: str = "prose_numbers",
    neighbourhood: Decimal = NEIGHBOURHOOD,
    allowed_years: Iterable[int] = (),
    syntax: ClaimSyntax = DEFAULT_SYNTAX,
) -> GateResult:
    """Gate result for one paragraph.

    ``not_run`` with reason ``ohne_pruefbare_zahl`` when the paragraph states
    no number besides years, ``not_run`` with ``keine_werte`` when numbers are
    stated but no value is bound to the paragraph. An ambiguous number
    (``"2.5"``) is a finding ``zahl_mehrdeutig``.
    """
    claims = extract_claims(text, allowed_years=allowed_years, syntax=syntax)
    claims = [c for c in claims if not c.is_year]
    unreadable = [
        Finding("zahl_mehrdeutig", "Zahl nicht eindeutig lesbar", location, "", token)
        for token in ambiguous_numbers(text, syntax=syntax)
    ]
    if not claims and not unreadable:
        return GateResult(gate, Verdict.NOT_RUN, NO_CLAIMS)
    if not values and not unreadable:
        return GateResult(gate, Verdict.NOT_RUN, "keine_werte")
    checks = [check_claim(claim, values, neighbourhood=neighbourhood) for claim in claims]
    findings = [_finding(c, location) for c in checks if c.status is not ClaimStatus.MATCH]
    return decide(gate, len(checks) + len(unreadable), unreadable + findings)


def combine(gate: str, parts: Iterable[GateResult]) -> GateResult:
    """Combine paragraph results; paragraphs without numbers are neutral.

    Any failed paragraph fails, any other paragraph that did not run keeps the
    gate ``not_run``; a document without any checked number is ``not_run``.
    """
    relevant = [part for part in parts if part.reason != NO_CLAIMS]
    findings = [finding for part in relevant for finding in part.findings]
    checked = sum(part.checked for part in relevant)
    if findings:
        return decide(gate, checked, findings)
    if any(part.verdict is Verdict.NOT_RUN for part in relevant):
        return GateResult(gate, Verdict.NOT_RUN, "teilweise_nicht_pruefbar", checked)
    return decide(gate, checked, [])
