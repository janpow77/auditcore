"""Estimation of the contract value with lots under § 3 VgV, by reference date.

Two parts:

- :func:`check_small_lots` checks the exception for small lots in § 3 Abs. 9
  VgV: a lot may be awarded outside the EU procedure if its estimated net value
  is below 80 000 EUR (supplies and services) or below 1 million EUR (works)
  and the lots so awarded together do not exceed 20 % of the total value of
  all lots. The comparison follows the wording: "unter" is strictly below,
  "nicht übersteigt" allows exactly 20 %.
- :func:`estimation_hints` returns the verbatim provisions of § 3 VgV on
  options and premiums, framework agreements, lots and similar supplies.

Only § 3 VgV (public contracts) is modelled; SektVO, KonzVgV and VSVgV are not.
Before 18.04.2016 the provision did not exist in this form: "not recorded".
Whether the total value of all lots reaches the EU threshold is a separate
question (:func:`auditcore_procurement.check_eu_threshold`).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .precheck_common import PASS, REVIEW_REQUIRED, CheckResult, result

_CHECK = ("precheck_small_lots", "Ausnahme für kleine Lose (§ 3 Abs. 9 VgV)")
#: Lot limits of § 3 Abs. 9 VgV in EUR (net), unchanged in all versions.
LOT_LIMITS = {"supplies_services": Decimal("80000"), "works": Decimal("1000000")}
SHARE_LIMIT_PERCENT = 20
_VGV_2016 = "Art. 1 Vergaberechtsmodernisierungsverordnung vom 12.04.2016, BGBl. I S. 624"
_VGV_2023 = "Art. 1 Verordnung vom 17.08.2023, BGBl. 2023 I Nr. 222"
_VGV_2024 = (
    "Art. 1 Verordnung zur Änderung vergaberechtlicher Vorschriften vom 07.02.2024, "
    "BGBl. 2024 I Nr. 39"
)


@dataclass(frozen=True)
class VgvProvision:
    """One paragraph of § 3 VgV in one version, with verbatim wording."""

    provision: str
    topic: str
    valid_from: date
    valid_to: date | None
    wording: str
    reference: str

    def covers(self, on: date) -> bool:
        """Whether this version is in force on ``on``."""
        return self.valid_from <= on and (self.valid_to is None or on <= self.valid_to)

    def to_dict(self) -> dict[str, str | None]:
        """JSON view (``valid_to`` ``None`` = in force until amended)."""
        return {
            "provision": self.provision,
            "topic": self.topic,
            "valid_from": self.valid_from.isoformat(),
            "valid_to": None if self.valid_to is None else self.valid_to.isoformat(),
            "wording": self.wording,
            "reference": self.reference,
        }


@dataclass(frozen=True)
class Lot:
    """One lot of the project: estimated net value, kind and whether it is to be exempted."""

    value: Decimal
    kind: str
    exempt: bool = False


_START, _MID, _NEW = date(2016, 4, 18), date(2023, 8, 24), date(2024, 2, 14)
_ABS9 = (
    "Der öffentliche Auftraggeber kann bei der Vergabe einzelner Lose von Absatz 7 Satz {} "
    "sowie Absatz 8 abweichen, wenn der geschätzte Nettowert des betreffenden Loses bei "
    "Liefer- und Dienstleistungen unter 80 000 Euro und bei Bauleistungen unter 1 Million "
    "Euro liegt und die Summe der Nettowerte dieser Lose 20 Prozent des Gesamtwertes aller "
    "Lose nicht übersteigt."
)
_ABS7_HEAD = (
    "Kann das beabsichtigte Bauvorhaben oder die vorgesehene Erbringung einer Dienstleistung "
    "zu einem Auftrag führen, der in mehreren Losen vergeben wird, ist der geschätzte "
    "Gesamtwert aller Lose zugrunde zu legen. "
)
_ABS7_TAIL = (
    "Erreicht oder überschreitet der geschätzte Gesamtwert den maßgeblichen Schwellenwert, "
    "gilt diese Verordnung für die Vergabe jedes Loses."
)
_LOTS = "Lose (Bau- und Dienstleistungen)"
_SMALL = "Ausnahme für kleine Lose"

#: § 3 VgV, verbatim (gesetze-im-internet.de; earlier versions: buzer.de, 23.11.2026).
PROVISIONS: tuple[VgvProvision, ...] = (
    VgvProvision(
        "§ 3 Abs. 1 VgV",
        "Gesamtwert, Optionen, Vertragsverlängerungen, Prämien und Zahlungen",
        _START,
        None,
        "Bei der Schätzung des Auftragswerts ist vom voraussichtlichen Gesamtwert der "
        "vorgesehenen Leistung ohne Umsatzsteuer auszugehen. Zudem sind etwaige Optionen oder "
        "Vertragsverlängerungen zu berücksichtigen. Sieht der öffentliche Auftraggeber Prämien "
        "oder Zahlungen an den Bewerber oder Bieter vor, sind auch diese zu berücksichtigen.",
        _VGV_2016,
    ),
    VgvProvision(
        "§ 3 Abs. 4 VgV",
        "Rahmenvereinbarungen und dynamische Beschaffungssysteme",
        _START,
        None,
        "Der Wert einer Rahmenvereinbarung oder eines dynamischen Beschaffungssystems wird auf "
        "der Grundlage des geschätzten Gesamtwertes aller Einzelaufträge berechnet, die während "
        "der gesamten Laufzeit einer Rahmenvereinbarung oder eines dynamischen "
        "Beschaffungssystems geplant sind.",
        _VGV_2016,
    ),
    VgvProvision(
        "§ 3 Abs. 7 VgV",
        _LOTS,
        _START,
        date(2023, 8, 23),
        _ABS7_HEAD
        + "Bei Planungsleistungen gilt dies nur für Lose über gleichartige Leistungen. "
        + _ABS7_TAIL,
        _VGV_2016,
    ),
    VgvProvision("§ 3 Abs. 7 VgV", _LOTS, _MID, None, _ABS7_HEAD + _ABS7_TAIL, _VGV_2023),
    VgvProvision(
        "§ 3 Abs. 8 VgV",
        "Lose über gleichartige Lieferungen",
        _START,
        None,
        "Kann ein Vorhaben zum Zweck des Erwerbs gleichartiger Lieferungen zu einem Auftrag "
        "führen, der in mehreren Losen vergeben wird, ist der geschätzte Gesamtwert aller Lose "
        "zugrunde zu legen.",
        _VGV_2016,
    ),
    VgvProvision("§ 3 Abs. 9 VgV", _SMALL, _START, date(2024, 2, 13), _ABS9.format(3), _VGV_2016),
    VgvProvision("§ 3 Abs. 9 VgV", _SMALL, _NEW, None, _ABS9.format(2), _VGV_2024),
)
_REDACTION_NOTE = (
    "Vom 24.08.2023 bis 13.02.2024 verwies § 3 Abs. 9 VgV noch auf „Absatz 7 Satz 3“, obwohl "
    "Absatz 7 seit der Änderung vom 17.08.2023 nur zwei Sätze hatte; gemeint ist der Satz, "
    "nach dem die Verordnung für jedes Los gilt (berichtigt ab 14.02.2024)."
)


def estimation_hints(on: date) -> list[dict[str, str | None]]:
    """Verbatim provisions of § 3 VgV on value estimation in force on ``on``.

    Empty before 18.04.2016 (not recorded). The wording is guidance for the
    reviewer; nothing is evaluated.
    """
    return [p.to_dict() for p in PROVISIONS if p.covers(on)]


def small_lots_rule(on: date) -> VgvProvision | None:
    """Version of § 3 Abs. 9 VgV in force on ``on``; ``None`` if not recorded."""
    return next((p for p in PROVISIONS if p.provision == "§ 3 Abs. 9 VgV" and p.covers(on)), None)


def _lot_findings(lots: Sequence[Lot]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for number, lot in enumerate(lots, start=1):
        if lot.kind not in LOT_LIMITS:
            raise ValueError(f"Los {number}: kind muss eine von {tuple(LOT_LIMITS)} sein.")
        if lot.value < 0:
            raise ValueError(f"Los {number}: Wert darf nicht negativ sein.")
        if lot.exempt:
            limit = LOT_LIMITS[lot.kind]
            below = lot.value < limit
            findings.append(
                {"lot": number, "value": str(lot.value), "limit": str(limit), "below_limit": below}
            )
    return findings


def check_small_lots(lots: Sequence[Lot], *, reference_date: date | None) -> CheckResult:
    """Whether the lots marked ``exempt`` meet § 3 Abs. 9 VgV on the reference date.

    ``lots`` are all lots of the project (the total value is their sum).
    ``PASS`` carries ``exemption_possible``; the exception is a permission of
    the contracting authority, not an obligation. ``REVIEW_REQUIRED`` means the
    date is missing or no version is recorded for it.

    Raises:
        ValueError: unknown lot kind, negative value, no lot marked ``exempt``.
    """
    findings = _lot_findings(lots)
    if not findings:
        raise ValueError("Kein Los ist als exempt markiert.")
    if reference_date is None:
        return result(*_CHECK, REVIEW_REQUIRED, "Stichtag fehlt (Datum der Bekanntmachung).")
    rule = small_lots_rule(reference_date)
    if rule is None:
        return result(
            *_CHECK,
            REVIEW_REQUIRED,
            f"Für den {reference_date:%d.%m.%Y} ist § 3 Abs. 9 VgV nicht hinterlegt "
            "(gilt erst ab dem 18.04.2016).",
        )
    total = sum((lot.value for lot in lots), Decimal(0))
    exempt = sum((lot.value for lot in lots if lot.exempt), Decimal(0))
    share_ok = exempt * 100 <= total * SHARE_LIMIT_PERCENT
    lots_ok = all(f["below_limit"] for f in findings)
    possible = share_ok and lots_ok
    message = (
        f"Ausnahme nach § 3 Abs. 9 VgV {'möglich' if possible else 'nicht möglich'}: "
        f"ausgenommene Lose zusammen {exempt} EUR von {total} EUR "
        f"({'höchstens' if share_ok else 'mehr als'} 20 %); "
        f"{'jedes' if lots_ok else 'nicht jedes'} ausgenommene Los unter seiner Losgrenze."
    )
    return result(
        *_CHECK,
        PASS,
        message,
        exemption_possible=possible,
        exempt_total=str(exempt),
        lots_total=str(total),
        share_within_limit=share_ok,
        lots=findings,
        rule=rule.to_dict(),
        note=_REDACTION_NOTE if _MID <= reference_date < _NEW else None,
    )
