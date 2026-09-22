"""De-minimis cumulation as a separate, versioned calculation contract.

The source (``de_minimis.berechne_kumulierung``) sums register amounts in a
three-year window ending on the reference date and compares them with the
ceiling of the general regime. :func:`legacy_cumulation` reproduces that
output exactly. :func:`calculate` is the corrected contract:

* the rule profile (ceiling, window rule, regimes without ceiling, legal
  basis, validity) is explicit, versioned and marked ``REVIEW_REQUIRED``;
* the reference date must be given (the source defaulted to "today");
* the undertaking is explicit: which beneficiary references the caller treats
  as one single undertaking; other references are excluded with a reason;
* every award is classified (considered, outside window, no date, no amount,
  negative amount, other undertaking) and returned with the reason;
* a comparison with the ceiling is only produced when every considered award
  belongs to the general regime and nothing is unclear; the result is an
  arithmetic statement, never a free reserve, an approval or a decision.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from .deminimis import as_amount, as_date
from .profiles import load_profile, reference

PROFILE_ID = "designer.deminimis.cumulation"
CALCULATION = "auditcore_funding_sources.cumulation/1"


def window_start(reference_date: date, years: int) -> date:
    """``reference_date`` minus ``years`` calendar years; 29 February becomes 28 February."""
    try:
        return reference_date.replace(year=reference_date.year - years)
    except ValueError:
        return reference_date.replace(year=reference_date.year - years, day=28)


def legacy_cumulation_values(
    records: Iterable[Mapping[str, Any]], *, reference_date: date
) -> dict[str, Any]:
    """Field values of the source dataclass ``Kumulierung`` (Decimal amounts)."""
    profile = load_profile(PROFILE_ID)
    start = window_start(reference_date, 3)
    records = list(records)
    inside: list[Mapping[str, Any]] = []
    without_date = 0
    for record in records:
        granted = as_date(record.get("grantingDate"))
        if granted is None:
            without_date += 1
            continue
        if start <= granted <= reference_date:
            inside.append(record)
    per_type: dict[str, Decimal] = {}
    without_amount = 0
    for record in inside:
        kind = str(record.get("deMinimisType") or "UNBEKANNT")
        amount = as_amount(record.get("amountEur"))
        per_type.setdefault(kind, Decimal("0"))
        if amount is None:
            without_amount += 1
            continue
        per_type[kind] += amount
    total = sum(per_type.values(), Decimal("0"))
    ceiling: Decimal | None = None
    difference: Decimal | None = None
    if set(per_type) == {"GENERAL"} and not (without_date or without_amount):
        ceiling = Decimal(profile["ceiling_eur"])
        difference = ceiling - total
    return {
        "stichtag": reference_date,
        "fenster_von": start,
        "saetze_gesamt": len(records),
        "saetze_im_fenster": len(inside),
        "summe_im_fenster": total,
        "summe_je_art": per_type,
        "hoechstbetrag": ceiling,
        "verbleibend": None,
        "ohne_datum": without_date,
        "ohne_betrag": without_amount,
        "rechnerische_differenz": difference,
    }


def legacy_cumulation(records: Iterable[Mapping[str, Any]], *, reference_date: date) -> dict[str, Any]:
    """``berechne_kumulierung(...).to_dict()`` of the source, exactly (floats included)."""
    profile = load_profile(PROFILE_ID)
    v = legacy_cumulation_values(records, reference_date=reference_date)
    ceiling, difference = v["hoechstbetrag"], v["rechnerische_differenz"]
    return {
        "stichtag": v["stichtag"].isoformat(),
        "fenster_von": v["fenster_von"].isoformat(),
        "fenster_bis": v["stichtag"].isoformat(),
        "saetze_gesamt": v["saetze_gesamt"],
        "saetze_im_fenster": v["saetze_im_fenster"],
        "summe_im_fenster_eur": float(v["summe_im_fenster"]),
        "summe_je_art_eur": {k: float(x) for k, x in v["summe_je_art"].items()},
        "hoechstbetrag_eur": float(ceiling) if ceiling is not None else None,
        "verbleibend_eur": None,
        "ohne_datum": v["ohne_datum"],
        "ohne_betrag": v["ohne_betrag"],
        "summe_vollstaendig": not (v["ohne_datum"] or v["ohne_betrag"]),
        "rechnerische_differenz_eur": float(difference) if difference is not None else None,
        "methodenfassung": profile["legacy_method_version"],
        "fensterregel": profile["window"]["rule"],
        "foerderreserve_beurteilt": False,
    }


@dataclass(frozen=True)
class ClassifiedAward:
    """One register record with the reason why it is or is not in the sum."""

    reference_number: str | None
    beneficiary_reference: str | None
    granting_date: date | None
    amount_eur: Decimal | None
    de_minimis_type: str
    status: str
    reason: str


@dataclass(frozen=True)
class CumulationResult:
    """Arithmetic view of the registered de-minimis aid of one undertaking; no decision."""

    profile: Mapping[str, str]
    profile_status: str
    calculation: str
    reference_date: date
    window_from: date
    window_to: date
    undertaking_references: tuple[str, ...] | None
    awards: tuple[ClassifiedAward, ...]
    sum_per_type_eur: Mapping[str, Decimal]
    sum_considered_eur: Decimal
    ceiling_eur: Decimal | None
    arithmetic_difference_eur: Decimal | None
    exceeds_ceiling: bool | None
    complete: bool
    reasons_without_comparison: tuple[str, ...]
    notices: tuple[str, ...]
    decision: None = field(default=None)

    def to_dict(self) -> dict[str, Any]:
        """JSON form with Decimal amounts as strings."""
        return {
            "calculation": self.calculation,
            "profile": dict(self.profile),
            "profile_status": self.profile_status,
            "reference_date": self.reference_date.isoformat(),
            "window_from": self.window_from.isoformat(),
            "window_to": self.window_to.isoformat(),
            "undertaking_references": list(self.undertaking_references)
            if self.undertaking_references is not None else None,
            "awards": [
                {
                    "reference_number": a.reference_number,
                    "beneficiary_reference": a.beneficiary_reference,
                    "granting_date": a.granting_date.isoformat() if a.granting_date else None,
                    "amount_eur": str(a.amount_eur) if a.amount_eur is not None else None,
                    "de_minimis_type": a.de_minimis_type,
                    "status": a.status,
                    "reason": a.reason,
                }
                for a in self.awards
            ],
            "sum_per_type_eur": {k: str(v) for k, v in self.sum_per_type_eur.items()},
            "sum_considered_eur": str(self.sum_considered_eur),
            "ceiling_eur": str(self.ceiling_eur) if self.ceiling_eur is not None else None,
            "arithmetic_difference_eur": str(self.arithmetic_difference_eur)
            if self.arithmetic_difference_eur is not None else None,
            "exceeds_ceiling": self.exceeds_ceiling,
            "complete": self.complete,
            "reasons_without_comparison": list(self.reasons_without_comparison),
            "notices": list(self.notices),
            "decision": None,
        }


def calculate(
    awards: Iterable[Mapping[str, Any]],
    *,
    reference_date: date,
    undertaking_references: Iterable[str] | None = None,
    profile_id: str = PROFILE_ID,
    version: str = "2026.09.1",
) -> CumulationResult:
    """Classify and sum register records of one undertaking in the profile window.

    Args:
        awards: records in the register field names (``grantingDate``,
            ``amountEur``, ``deMinimisType``, ``beneficiaryReferenceNumber``).
        reference_date: explicit reference date; no implicit "today".
        undertaking_references: beneficiary references the caller treats as
            one single undertaking (Art. 2 Abs. 2). ``None`` means the caller
            asserts that all records belong to it; the result says so.
    """
    if not isinstance(reference_date, date):
        raise TypeError("reference_date muss ein Datum sein.")
    profile = load_profile(profile_id, version)
    years = int(profile["window"]["years"])
    start = window_start(reference_date, years)
    general = profile["ceiling_applies_to_type"]
    group = None if undertaking_references is None else tuple(sorted(set(undertaking_references)))
    classified: list[ClassifiedAward] = []
    per_type: dict[str, Decimal] = {}
    unclear: list[str] = []
    for record in awards:
        kind = str(record.get("deMinimisType") or "UNBEKANNT")
        granted = as_date(record.get("grantingDate"))
        amount = as_amount(record.get("amountEur"))
        beneficiary = record.get("beneficiaryReferenceNumber")
        base = {
            "reference_number": record.get("referenceNumber"),
            "beneficiary_reference": beneficiary,
            "granting_date": granted,
            "amount_eur": amount,
            "de_minimis_type": kind,
        }
        if group is not None and beneficiary not in group:
            status, reason = "excluded", "Begünstigtenreferenz gehört nicht zum angegebenen Unternehmen."
        elif granted is None:
            status, reason = "unclear", "Gewährungsdatum fehlt oder ist nicht lesbar."
            unclear.append("no_date")
        elif not start <= granted <= reference_date:
            status, reason = "excluded", "Gewährung außerhalb des Betrachtungszeitraums."
        elif amount is None:
            status, reason = "unclear", "Betrag fehlt oder ist nicht lesbar."
            unclear.append("no_amount")
            per_type.setdefault(kind, Decimal("0"))
        elif amount < 0:
            status, reason = "unclear", "Negativer Betrag; fachlich zu klären (Rückforderung?)."
            unclear.append("negative_amount")
            per_type.setdefault(kind, Decimal("0"))
        else:
            status, reason = "considered", "Im Zeitraum gewährt und berücksichtigt."
            per_type[kind] = per_type.get(kind, Decimal("0")) + amount
        classified.append(ClassifiedAward(**base, status=status, reason=reason))
    total = sum(per_type.values(), Decimal("0"))
    reasons: list[str] = []
    if not per_type:
        reasons.append("Keine Meldung im Betrachtungszeitraum.")
    if set(per_type) - {general}:
        reasons.append(
            "Nicht ausschließlich Meldungen der allgemeinen Regelung; kein gemeinsamer Höchstbetrag."
        )
    if unclear:
        reasons.append(f"{len(unclear)} Meldung(en) mit ungeklärtem Datum oder Betrag.")
    ceiling = difference = None
    exceeds: bool | None = None
    if not reasons:
        ceiling = Decimal(profile["ceiling_eur"])
        difference = ceiling - total
        exceeds = total > ceiling
    notices = [profile["notices"]["company"], profile["notices"]["period"], profile["notices"]["deadline"]]
    if group is None:
        notices.append(
            "Die Zugehörigkeit aller übergebenen Meldungen zu einem einzigen Unternehmen wurde "
            "vom Aufrufer vorausgesetzt und nicht geprüft."
        )
    notices.append(
        "Rechenfenster: drei Kalenderjahre bis zum Stichtag, beide Randtage eingeschlossen. Die "
        "Differenz zur Vergleichsgrenze ist keine verfügbare Förderreserve."
    )
    return CumulationResult(
        profile=reference(profile),
        profile_status=profile["status"],
        calculation=CALCULATION,
        reference_date=reference_date,
        window_from=start,
        window_to=reference_date,
        undertaking_references=group,
        awards=tuple(classified),
        sum_per_type_eur=per_type,
        sum_considered_eur=total,
        ceiling_eur=ceiling,
        arithmetic_difference_eur=difference,
        exceeds_ceiling=exceeds,
        complete=not unclear,
        reasons_without_comparison=tuple(reasons),
        notices=tuple(notices),
    )
