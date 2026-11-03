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
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from .numbers import PrintedNumber, format_de, read_number, relative_deviation, same_value
from .units import PLAIN, Unit, conversion_exponent, unit_of
from .verdict import Finding, GateResult, Verdict, decide

NEIGHBOURHOOD = Decimal("0.10")
"""Relative distance up to which an unequal value counts as the meant value."""

UNIT_INHERITANCE_DISTANCE = 40
"""Characters within which a number without unit takes the unit of the next one."""

YEAR_RANGE = (1900, 2100)

_NUMBER = re.compile(
    r"(?:(?<![\w\d])(?P<sign>[-–−])\s?)?"
    r"(?P<number>\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?)"
    r"(?:\s?(?P<unit>%|Prozentpunkte|Prozentpunkt|Prozent|Pp\.|Mio\.|Mrd\.|Tsd\."
    r"|Millionen|Milliarden))?"
)
_MASKS = (
    re.compile(r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b"),
    re.compile(r"\*\s?\d+"),
    re.compile(
        r"\b(?:Tabelle|Abbildung|Kapitel|Abschnitt|Ziffer|Nummer|Anhang|Anlage)\s+\d+(?:\.\d+)*"
    ),
    re.compile(r"\bArt\.\s?\d+|\bNr\.\s?\d+|§\s?\d+|\bAbs\.\s?\d+"),
    re.compile(r"\b(?:je|pro)\s+\d[\d.]*"),
    re.compile(r"(?<=[A-Za-zÄÖÜäöüß])\d{1,3}(?=[A-Za-zÄÖÜäöüß])"),
)
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

    @property
    def is_year(self) -> bool:
        """Integer in the year range without own or inherited unit."""
        low, high = YEAR_RANGE
        value = self.number.value
        return (
            not self.unit_stated
            and self.number.decimals == 0
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


def _masked(text: str) -> str:
    for pattern in _MASKS:
        text = pattern.sub(lambda m: " " * len(m.group()), text)
    return text


def _raw_claims(source: str) -> list[tuple[Claim, int]]:
    found: list[tuple[Claim, int]] = []
    for match in _NUMBER.finditer(source):
        number = read_number(match["number"])
        if number is None:
            continue
        if match["sign"]:
            number = PrintedNumber(-number.value, number.decimals, match.group().strip())
        token = match["unit"] or ""
        unit = unit_of(token) if token else PLAIN
        claim = Claim(number, unit, match.start(), bool(token))
        found.append((claim, match.end()))
    return found


def _inherited(source: str, end: int, following: Sequence[tuple[Claim, int]]) -> Unit | None:
    for claim, _ in following:
        gap = source[end : claim.position]
        if len(gap) > UNIT_INHERITANCE_DISTANCE:
            return None
        if _SENTENCE_END.search(_ABBREVIATION.sub("  ", gap)):
            return None
        if claim.unit_stated:
            return claim.unit
    return None


def extract_claims(text: str) -> list[Claim]:
    """All numbers of a paragraph; dates, footnotes and cross references are masked.

    A number without unit inherits the unit of the next number in the same
    sentence (``"8,4 bzw. 8,5 %"``); year-like integers never inherit.
    """
    source = _masked(text)
    raw = _raw_claims(source)
    claims: list[Claim] = []
    for index, (claim, end) in enumerate(raw):
        if claim.unit_stated or claim.is_year:
            claims.append(claim)
            continue
        unit = _inherited(source, end, raw[index + 1 :])
        claims.append(claim if unit is None else Claim(claim.number, unit, claim.position, True))
    return claims


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
) -> GateResult:
    """Gate result for one paragraph.

    ``not_run`` with reason ``ohne_pruefbare_zahl`` when the paragraph states
    no number besides years, ``not_run`` with ``keine_werte`` when numbers are
    stated but no value is bound to the paragraph.
    """
    claims = [claim for claim in extract_claims(text) if not claim.is_year]
    if not claims:
        return GateResult(gate, Verdict.NOT_RUN, NO_CLAIMS)
    if not values:
        return GateResult(gate, Verdict.NOT_RUN, "keine_werte")
    checks = [check_claim(claim, values, neighbourhood=neighbourhood) for claim in claims]
    findings = [_finding(c, location) for c in checks if c.status is not ClaimStatus.MATCH]
    return decide(gate, len(checks), findings)


NO_CLAIMS = "ohne_pruefbare_zahl"
"""Reason of a paragraph without numbers; neutral for :func:`combine`."""


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
