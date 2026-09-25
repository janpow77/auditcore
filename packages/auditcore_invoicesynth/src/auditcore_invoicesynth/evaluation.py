"""Bewertungswerkzeug (Plan 2d): gleiche Kennzahlen für alle Kandidaten.

Verglichen wird nach Normalisierung: Beträge als ``Decimal`` auf den Cent,
Datum ISO, Kennungen groß ohne Leerzeichen, Steuersatz als Zahl, übrige Felder
mit zusammengefasstem Leerraum. Ein **falscher** Wert zählt getrennt von
einem **fehlenden** (falsch ist schlimmer). Die maßgebliche Kennzahl ist die
Falschwert-Quote der Werte, die eine Plausibilitätsprüfung durchlässt.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from auditcore_invoicesynth.formats import (
    normalize_identifier,
    parse_date,
    parse_money,
    parse_rate,
)
from auditcore_invoicesynth.schema import REQUIRED_FIELDS

AMOUNT_KEYS = ("net_amount", "vat_amount", "total")
DATE_KEYS = ("invoice_date", "supply_date", "due_date")
ID_KEYS = ("iban", "bic", "supplier.vat_id")
EVALUATED_FIELDS = (
    "invoice_number",
    "invoice_date",
    "supply_date",
    "due_date",
    "supplier.name",
    "supplier.vat_id",
    "net_amount",
    "vat_amount",
    "vat_rates",
    "total",
    "iban",
    "bic",
)

#: Abnahmeschwellen (Entscheidung E6 vom 24.09.2026) für T2 und T3.
ACCEPTANCE_THRESHOLDS: dict[str, float] = {
    "total": 0.98,
    "invoice_date": 0.98,
    "invoice_number": 0.95,
    "iban": 0.97,
    "supplier.vat_id": 0.97,
}
MAX_WRONG_RATE_AFTER_PLAUSIBILITY = 0.005


def flatten(parse: Mapping[str, Any]) -> dict[str, str]:
    """Ziel-JSON → flache Felder; ``vat_amount`` = Summe der Steuerzeilen (wie gedruckt)."""
    flat: dict[str, str] = {}
    for key, value in parse.items():
        if key == "vat_lines" and isinstance(value, list):
            amounts = [parse_money(str(line.get("amount", ""))) for line in value]
            rates = [str(line.get("rate", "")) for line in value if line.get("rate")]
            if amounts and all(a is not None for a in amounts):
                flat["vat_amount"] = f"{sum(a for a in amounts if a is not None):.2f}"
            if rates:
                flat["vat_rates"] = "+".join(rates)
        elif isinstance(value, Mapping):
            for child, child_value in value.items():
                if isinstance(child_value, str):
                    flat[f"{key}.{child}"] = child_value
        elif isinstance(value, str):
            flat[key] = value
    return flat


def canonical(key: str, value: str) -> str | None:
    """Vergleichbare Normalform eines Feldwerts; ``None`` = nicht lesbar."""
    if key in AMOUNT_KEYS:
        amount = parse_money(value)
        return None if amount is None else f"{amount:.2f}"
    if key in DATE_KEYS:
        return parse_date(value)
    if key in ID_KEYS:
        return normalize_identifier(value) or None
    if key == "vat_rates":
        rates = [parse_rate(part) for part in value.split("+")]
        if any(rate is None for rate in rates):
            return None
        return "+".join(
            str(rate) for rate in sorted((r for r in rates if r is not None), reverse=True)
        )
    text = " ".join(value.split())
    return text or None


@dataclass
class FieldScore:
    expected: int = 0
    correct: int = 0
    wrong: int = 0
    missing: int = 0
    spurious: int = 0
    hallucinated: int = 0
    accepted: int = 0
    accepted_wrong: int = 0

    @property
    def accuracy(self) -> float:
        return self.correct / self.expected if self.expected else 1.0

    @property
    def wrong_rate(self) -> float:
        return self.wrong / self.expected if self.expected else 0.0

    @property
    def missing_rate(self) -> float:
        return self.missing / self.expected if self.expected else 0.0

    @property
    def wrong_rate_after_plausibility(self) -> float:
        return self.accepted_wrong / self.accepted if self.accepted else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "expected": self.expected,
            "correct": self.correct,
            "wrong": self.wrong,
            "missing": self.missing,
            "spurious": self.spurious,
            "hallucinated": self.hallucinated,
            "accuracy": round(self.accuracy, 6),
            "wrong_rate": round(self.wrong_rate, 6),
            "missing_rate": round(self.missing_rate, 6),
            "accepted": self.accepted,
            "accepted_wrong": self.accepted_wrong,
            "wrong_rate_after_plausibility": round(self.wrong_rate_after_plausibility, 6),
        }


@dataclass
class EvaluationReport:
    documents: int = 0
    documents_all_required_correct: int = 0
    fields: dict[str, FieldScore] = field(default_factory=dict)

    @property
    def document_rate(self) -> float:
        return self.documents_all_required_correct / self.documents if self.documents else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "documents": self.documents,
            "document_rate": round(self.document_rate, 6),
            "fields": {name: score.to_dict() for name, score in sorted(self.fields.items())},
        }


Acceptor = Callable[[dict[str, str]], set[str]]


def evaluate(
    pairs: Iterable[tuple[Mapping[str, Any], Mapping[str, Any]]],
    *,
    accept: Acceptor | None = None,
    fields: tuple[str, ...] = EVALUATED_FIELDS,
) -> EvaluationReport:
    """Paare (Ziel-JSON, Vorhersage) bewerten.

    ``accept`` erhält die flache Vorhersage und liefert die Felder, die eine
    Plausibilitätsprüfung automatisch übernehmen würde (z. B. die
    Zusammenführung aus ``auditcore_documents``); daraus entsteht die
    Falschwert-Quote nach Plausibilität.
    """
    report = EvaluationReport(fields={name: FieldScore() for name in fields})
    for truth, prediction in pairs:
        report.documents += 1
        if _score_document(report, fields, truth, prediction, accept):
            report.documents_all_required_correct += 1
    return report


def _score_document(
    report: EvaluationReport,
    fields: tuple[str, ...],
    truth: Mapping[str, Any],
    prediction: Mapping[str, Any],
    accept: Acceptor | None,
) -> bool:
    """Felder eines Belegs zählen; ``True``, wenn alle Pflichtfelder stimmen."""
    expected = {k: canonical(k, v) for k, v in flatten(truth).items() if k in fields}
    predicted_raw = {k: v for k, v in flatten(prediction).items() if k in fields}
    predicted = {k: canonical(k, v) for k, v in predicted_raw.items()}
    accepted = accept(predicted_raw) if accept is not None else set()
    truth_values = {v for v in expected.values() if v is not None}
    all_required = True
    for name in fields:
        present = name in predicted_raw
        want, got = expected.get(name), predicted.get(name)
        if present and got not in truth_values:
            report.fields[name].hallucinated += 1
        if not _score_field(report.fields[name], name, want, got, present, name in accepted):
            all_required = False
    return all_required


def _score_field(
    score: FieldScore,
    name: str,
    want: str | None,
    got: str | None,
    present: bool,
    accepted: bool,
) -> bool:
    """Ein Feld zählen; ``False``, wenn es den Beleg als nicht vollständig richtig markiert."""
    if want is None:
        if present:
            score.spurious += 1
            return name not in REQUIRED_FIELDS
        return True
    score.expected += 1
    if not present:
        score.missing += 1
    elif got == want:
        score.correct += 1
    else:
        score.wrong += 1
    if accepted and present:
        score.accepted += 1
        score.accepted_wrong += int(got != want)
    return not (name in REQUIRED_FIELDS and got != want)


@dataclass(frozen=True)
class AcceptanceResult:
    passed: bool
    failures: tuple[str, ...]


def check_acceptance(report: EvaluationReport) -> AcceptanceResult:
    """Schwellen aus E6 prüfen (Feldgenauigkeit, Falschwert-Quote nach Plausibilität)."""
    failures = []
    for name, threshold in ACCEPTANCE_THRESHOLDS.items():
        score = report.fields.get(name)
        if score is None or score.expected == 0:
            failures.append(f"{name}: keine Erwartungswerte")
            continue
        if score.accuracy < threshold:
            failures.append(f"{name}: Genauigkeit {score.accuracy:.4f} < {threshold}")
    for name, score in report.fields.items():
        if score.wrong_rate_after_plausibility > MAX_WRONG_RATE_AFTER_PLAUSIBILITY:
            failures.append(
                f"{name}: Falschwert-Quote nach Plausibilität "
                f"{score.wrong_rate_after_plausibility:.4f} > {MAX_WRONG_RATE_AFTER_PLAUSIBILITY}"
            )
    return AcceptanceResult(not failures, tuple(failures))
