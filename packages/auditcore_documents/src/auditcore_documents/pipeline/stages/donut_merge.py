"""Zusammenführung der Donut-Felder mit Pflicht-Plausibilitätsprüfung (Plan 2a).

Ein Donut-Wert wird nur übernommen, wenn er die Plausibilitätsprüfung besteht
**und** entweder seine Feldkonfidenz den Profilschwellwert erreicht oder der
gleiche Wert im Tesseract-Text vorkommt (Zwei-Motoren-Abgleich). Beträge
brauchen zusätzlich die Summenprüfung ``netto + USt = brutto``; ist sie mangels
Angaben nicht rechenbar, muss der Betrag im Tesseract-Text bestätigt sein. Ein
Betrag aus Donut führt damit nie ungeprüft zu ``OK``.

Sonst bleibt der Regex-Wert aus ``PostprocessStage`` (bzw. das Feld leer) und
die Regeln ``VAL_DONUT_PLAUSIBILITY``/``VAL_DONUT_DISAGREEMENT`` setzen
``REVIEW_NEEDED``. Der Entscheidungsbericht steht in
``normalized_json["donut_merge"]``.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

from auditcore_documents.pipeline.context import PipelineContext
from auditcore_documents.pipeline.stages.base import PipelineStage
from auditcore_documents.pipeline.stages.postprocess import parse_amount
from auditcore_documents.pipeline.stages.validation import (
    VAT_ID_PATTERNS,
    ValidationRule,
    validate_iban,
)

ALLOWED_VAT_RATES = {
    "DE": frozenset({Decimal(19), Decimal(7), Decimal(0)}),
    "AT": frozenset({Decimal(20), Decimal(13), Decimal(10), Decimal(0)}),
}
MONTHS = {
    name: number
    for number, names in enumerate(
        (
            ("januar", "jänner", "january"),
            ("februar", "february"),
            ("märz", "maerz", "march"),
            ("april",),
            ("mai", "may"),
            ("juni", "june"),
            ("juli", "july"),
            ("august",),
            ("september",),
            ("oktober", "october"),
            ("november",),
            ("dezember", "december"),
        ),
        1,
    )
    for name in names
}
#: Kernfelder: ein unbestätigter oder widersprüchlicher Wert führt zur Prüfung.
TEXT_CONFIRMED_FIELDS = (
    "invoice_number",
    "date",
    "net_amount",
    "vat_amount",
    "total",
    "iban",
    "vat_id",
)
CORE_FIELDS = (*TEXT_CONFIRMED_FIELDS, "vat_rates")
AMOUNTS = ("net_amount", "vat_amount", "total")
CENT = Decimal("0.01")


# --------------------------------------------------------------------------- Normalisierung
def clean_amount(raw: str) -> str:
    """Währung und Leerzeichen-Tausendergruppen entfernen (``1 234,56 €`` → ``1234,56``)."""
    text = raw.replace("EUR", "").replace("€", "").replace("\u00a0", " ").strip()
    sign = "-" if text.startswith("-") else ""
    text = text.lstrip("-").strip()
    if re.fullmatch(r"\d{1,3}(?: \d{3})+(?:[.,]\d{2})?", text):
        text = text.replace(" ", "")
    return sign + text


def amount(raw: str) -> Decimal | None:
    """Betrag gebietsschemabewusst (D5) als ``Decimal`` auf den Cent; mehrdeutig → ``None``."""
    text = clean_amount(raw)
    negative = text.startswith("-")
    value, state = parse_amount(text.lstrip("-"))
    if value is None or state != "ok":
        return None
    result = Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)
    return -result if negative else result


def iso_date(raw: str) -> str | None:
    text = " ".join(raw.strip().split())
    for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    match = re.fullmatch(r"(\d{1,2})\.\s*([A-Za-zÄÖÜäöü]+)\s+(\d{4})", text) or re.fullmatch(
        r"([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})", text
    )
    if match:
        groups = match.groups()
        day_text, month_text = (groups[0], groups[1]) if groups[0].isdigit() else groups[1::-1]
        month = MONTHS.get(month_text.casefold())
        if month:
            try:
                return date(int(groups[2]), month, int(day_text)).isoformat()
            except ValueError:
                return None
    return None


def rate(raw: str) -> Decimal | None:
    match = re.fullmatch(r"(\d{1,2})(?:[.,](\d))?\s*%?", raw.strip())
    if not match:
        return None
    value = Decimal(match[1] + ("." + match[2] if match[2] else ""))
    return value.quantize(Decimal(1)) if value == value.to_integral() else value


def compact(raw: str) -> str:
    return "".join(raw.split()).upper()


def de_vat_check_digit(first_eight: str) -> int:
    product = 10
    for char in first_eight:
        total = (int(char) + product) % 10 or 10
        product = (2 * total) % 11
    check = 11 - product
    return 0 if check == 10 else check


def at_uid_check_digit(first_seven: str) -> int:
    digits = [int(c) for c in first_seven]
    total = sum(d if i % 2 == 0 else (2 * d) // 10 + (2 * d) % 10 for i, d in enumerate(digits))
    return (10 - (total + 4) % 10) % 10


def vat_id_check(vat_id: str) -> str | None:
    """Fehlertext oder ``None``: Format je Land, Prüfziffer für DE und AT."""
    country = vat_id[:2]
    pattern = VAT_ID_PATTERNS.get(country)
    if pattern is None:
        return f"USt-IdNr.-Land unbekannt: {country}"
    if not re.match(pattern, vat_id):
        return "USt-IdNr.-Format ungültig"
    if country == "DE" and de_vat_check_digit(vat_id[2:10]) != int(vat_id[10]):
        return "USt-IdNr.-Prüfziffer ungültig"
    if country == "AT" and at_uid_check_digit(vat_id[3:10]) != int(vat_id[10]):
        return "UID-Prüfziffer ungültig"
    return None


# --------------------------------------------------------------------------- Seiten
def combine_pages(pages: list[dict[str, Any]]) -> dict[str, Any]:
    """Kopffelder: erste Fundstelle; Summen/Bankfelder: letzte Seite mit ``total``."""
    combined: dict[str, Any] = {}
    sums_page = next((p for p in reversed(pages) if "total" in p.get("fields", {})), None)
    for page in pages:
        for key, value in page.get("fields", {}).items():
            if isinstance(value, dict) and isinstance(combined.get(key), dict):
                for child, child_value in value.items():
                    combined[key].setdefault(child, child_value)
            else:
                combined.setdefault(key, value)
    if sums_page is not None:
        for key in ("net_amount", "vat_lines", "total", "iban", "bic"):
            if key in sums_page["fields"]:
                combined[key] = sums_page["fields"][key]
    return combined


def combine_confidence(pages: list[dict[str, Any]]) -> dict[str, float]:
    result: dict[str, float] = {}
    for page in pages:
        for key, value in (page.get("field_confidence") or {}).items():
            result[key] = min(result.get(key, 1.0), float(value))
    return result


# --------------------------------------------------------------------------- Textabgleich
def text_amounts(text: str) -> set[Decimal]:
    found: set[Decimal] = set()
    for token in re.findall(r"\d{1,3}(?:[ .,]\d{3})*(?:[.,]\d{2})|\d+[.,]\d{2}", text):
        value = amount(token)
        if value is not None:
            found.add(value)
    return found


def text_dates(text: str) -> set[str]:
    found = set()
    patterns = (
        r"\d{1,2}\.\d{1,2}\.\d{2,4}",
        r"\d{4}-\d{2}-\d{2}",
        r"\d{1,2}\.\s*[A-Za-zÄÖÜäöü]+\s+\d{4}",
        r"[A-Za-z]+\s+\d{1,2},\s*\d{4}",
    )
    for pattern in patterns:
        for token in re.findall(pattern, text):
            value = iso_date(token)
            if value:
                found.add(value)
    return found


def confirmed_in_text(name: str, value: Any, text: str, parts: list[Any] | None = None) -> bool:
    """Kommt der Wert (bzw. jede Steuerzeile) im unabhängig gelesenen Text vor?"""
    if not text:
        return False
    if name == "vat_amount" and parts:
        found = text_amounts(text)
        return all(part is not None and part in found for part in parts)
    if name in AMOUNTS:
        return Decimal(str(value)).quantize(CENT) in text_amounts(text)
    if name in {"date", "supply_date", "due_date"}:
        return value in text_dates(text)
    if name in {"iban", "vat_id", "bic"}:
        return str(value) in compact(text)
    if name == "vat_rates":
        rates = {rate(token) for token in re.findall(r"\d{1,2}(?:[.,]\d)?\s*%", text)}
        return bool(value) and all(r in rates for r in value)
    return bool(value) and str(value) in " ".join(text.split())


# --------------------------------------------------------------------------- Stufe
class DonutFieldMergeStage(PipelineStage):
    """Nach ``PostprocessStage``: Donut-Werte prüfen, abgleichen und übernehmen."""

    name = "donut_merge"
    description = "Merge Donut fields after mandatory plausibility checks"

    def __init__(
        self,
        *args: object,
        min_field_confidence: float = 0.90,
        today: Callable[[], date] = date.today,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.min_field_confidence = min_field_confidence
        self.today = today

    async def execute(self, context: PipelineContext) -> PipelineContext:
        self.validate_context(context)
        raw = context.artifacts.ocr_raw_json or {}
        if raw.get("engine") != "donut":
            return context
        pages = list(raw.get("pages") or [])
        donut = combine_pages(pages)
        confidence = combine_confidence(pages)
        text = str((raw.get("tesseract") or {}).get("text") or "")
        normalized = dict(context.artifacts.normalized_json or {})
        extracted = dict(context.artifacts.extracted_fields or {})
        report = self.merge(donut, confidence, text, normalized, extracted)
        report.update(
            {
                "model_id": raw.get("model_id"),
                "model_sha256": raw.get("model_sha256"),
                "threshold": self.min_field_confidence,
                "tesseract_text": bool(text),
            }
        )
        normalized["donut_merge"] = report
        context.artifacts.normalized_json = normalized
        context.artifacts.extracted_fields = extracted
        return context

    # -- Kandidaten ----------------------------------------------------------
    @staticmethod
    def candidates(donut: dict[str, Any]) -> dict[str, tuple[str, Any]]:
        """Pipeline-Feld → (gedruckter Rohwert, normalisierter Wert oder ``None``)."""
        result: dict[str, tuple[str, Any]] = {}
        supplier = donut.get("supplier") if isinstance(donut.get("supplier"), dict) else {}
        simple = {
            "invoice_number": donut.get("invoice_number"),
            "date": donut.get("invoice_date"),
            "net_amount": donut.get("net_amount"),
            "total": donut.get("total"),
            "iban": donut.get("iban"),
            "vat_id": supplier.get("vat_id") if supplier else None,
            "supplier_name": supplier.get("name") if supplier else None,
            "supply_date": donut.get("supply_date"),
            "due_date": donut.get("due_date"),
            "bic": donut.get("bic"),
        }
        for name, value in simple.items():
            if not isinstance(value, str) or not value.strip():
                continue
            if name in AMOUNTS:
                parsed: Any = amount(value)
            elif name in {"date", "supply_date", "due_date"}:
                parsed = iso_date(value)
            elif name in {"iban", "vat_id", "bic"}:
                parsed = compact(value)
            else:
                parsed = " ".join(value.split())
            result[name] = (value, parsed)
        lines = donut.get("vat_lines")
        if isinstance(lines, list) and lines:
            amounts = [amount(str(line.get("amount", ""))) for line in lines]
            raw_text = " + ".join(str(line.get("amount", "")) for line in lines)
            total = (
                sum((a for a in amounts if a is not None), Decimal(0))
                if all(a is not None for a in amounts)
                else None
            )
            result["vat_amount"] = (raw_text, total)
            result["vat_rates"] = (
                " + ".join(str(line.get("rate", "")) for line in lines),
                [rate(str(line.get("rate", ""))) for line in lines],
            )
            result["_vat_lines"] = (
                "",
                [
                    (
                        rate(str(line.get("rate", ""))),
                        amount(str(line.get("base", ""))) if line.get("base") else None,
                        amount(str(line.get("amount", ""))),
                    )
                    for line in lines
                ],
            )
        return result

    # -- Plausibilität -------------------------------------------------------
    def plausibility(self, values: dict[str, tuple[str, Any]]) -> dict[str, list[str]]:
        """Fehlgeschlagene Pflichtprüfungen je Feld (leere Liste = plausibel)."""
        failed: dict[str, list[str]] = {name: [] for name in values if not name.startswith("_")}
        for name, (_raw, parsed) in values.items():
            if name.startswith("_"):
                continue
            if parsed is None or (isinstance(parsed, list) and None in parsed):
                failed[name].append("nicht eindeutig lesbar")
        number = values.get("invoice_number")
        if number and number[1] is not None:
            text = number[1]
            if not 1 <= len(text) <= 40:
                failed["invoice_number"].append("Länge außerhalb 1–40")
            elif iso_date(text) or amount(text) is not None:
                failed["invoice_number"].append("sieht aus wie Datum oder Betrag")
        invoice_date = values.get("date", ("", None))[1]
        if invoice_date:
            if date.fromisoformat(invoice_date) > self.today() + timedelta(days=366):
                failed["date"].append("mehr als ein Jahr in der Zukunft")
            due = values.get("due_date", ("", None))[1]
            if due and due < invoice_date:
                failed["due_date"].append("Fälligkeit vor Rechnungsdatum")
        iban = values.get("iban", ("", None))[1]
        if iban:
            valid, message = validate_iban(iban)
            if not valid:
                failed["iban"].append(message)
        vat_id = values.get("vat_id", ("", None))[1]
        if vat_id:
            problem = vat_id_check(vat_id)
            if problem:
                failed["vat_id"].append(problem)
        country = (vat_id or iban or "DE")[:2]
        rates = values.get("vat_rates", ("", []))[1] or []
        allowed = ALLOWED_VAT_RATES.get(country)
        if allowed is not None and any(r is not None and r not in allowed for r in rates):
            failed["vat_rates"].append(f"Steuersatz in {country} nicht zulässig")
            failed.setdefault("vat_amount", []).append("Steuersatz unzulässig")
        for line_rate, base, line_amount in values.get("_vat_lines", ("", []))[1]:
            if None in (line_rate, base, line_amount):
                continue
            expected = (base * line_rate / 100).quantize(CENT, rounding=ROUND_HALF_UP)
            if abs(expected - line_amount) > CENT:
                failed.setdefault("vat_amount", []).append("Steuerzeile ≠ Basis × Satz")
        net = values.get("net_amount", ("", None))[1]
        if net is not None and net < 0:
            failed["net_amount"].append("negativer Nettobetrag")
        vat = values.get("vat_amount", ("", None))[1]
        total = values.get("total", ("", None))[1]
        if net is not None and vat is not None and total is not None:
            lines = max(1, len(rates))
            if abs(net + vat - total) > CENT * lines:
                for name in AMOUNTS:
                    failed[name].append("netto + USt ≠ brutto")
        return failed

    # -- Zusammenführung -----------------------------------------------------
    def merge(
        self,
        donut: dict[str, Any],
        confidence: dict[str, float],
        text: str,
        normalized: dict[str, Any],
        extracted: dict[str, Any],
    ) -> dict[str, Any]:
        values = self.candidates(donut)
        failed = self.plausibility(values)
        sum_checked = all(values.get(n, ("", None))[1] is not None for n in AMOUNTS)
        confidence_keys = {
            "date": "invoice_date",
            "vat_id": "supplier.vat_id",
            "supplier_name": "supplier.name",
        }
        fields: dict[str, Any] = {}
        for name, (raw, parsed) in values.items():
            if name.startswith("_"):
                continue
            if name == "vat_amount":
                keys = [
                    k for k in confidence if k.startswith("vat_lines.") and k.endswith("amount")
                ]
                conf = min((confidence[k] for k in keys), default=None)
            elif name == "vat_rates":
                keys = [k for k in confidence if k.startswith("vat_lines.") and k.endswith("rate")]
                conf = min((confidence[k] for k in keys), default=None)
            else:
                conf = confidence.get(confidence_keys.get(name, name))
            line_amounts = [a for _, _, a in values.get("_vat_lines", ("", []))[1]]
            match = parsed is not None and confirmed_in_text(name, parsed, text, line_amounts)
            # Ohne Tesseract-Text stammen Regex-Werte aus der Donut-Darstellung selbst.
            regex_value = normalized.get(name) if text else None
            entry: dict[str, Any] = {
                "donut": raw,
                "confidence": conf,
                "text_match": match,
                "checks": failed.get(name, []),
                "regex": regex_value,
            }
            final = self._value(name, parsed)
            if failed.get(name):
                entry["decision"] = "rejected"
            elif (
                regex_value is not None
                and name in TEXT_CONFIRMED_FIELDS
                and not match
                and not _same(name, regex_value, final)
            ):
                entry["decision"] = "disagreement"
            elif name in AMOUNTS and not sum_checked and not match:
                entry["decision"] = "unconfirmed"
            elif (conf is not None and conf >= self.min_field_confidence) or match:
                entry["decision"] = "accepted"
            else:
                entry["decision"] = "unconfirmed" if name in CORE_FIELDS else "not_taken"
            if entry["decision"] == "accepted":
                normalized[name] = final
                if name in AMOUNTS:
                    extracted[name] = clean_amount(raw) if name != "vat_amount" else f"{parsed}"
                elif name in extracted or name in TEXT_CONFIRMED_FIELDS:
                    extracted[name] = raw.strip()
            entry["value"] = normalized.get(name)
            fields[name] = entry
        return {"fields": fields, "sum_checked": sum_checked}

    @staticmethod
    def _value(name: str, parsed: Any) -> Any:
        if name in AMOUNTS and parsed is not None:
            return float(parsed)
        if name == "vat_rates" and parsed is not None:
            return [float(r) for r in parsed if r is not None]
        return parsed


def _same(name: str, left: Any, right: Any) -> bool:
    if name in AMOUNTS:
        try:
            return Decimal(str(left)).quantize(CENT) == Decimal(str(right)).quantize(CENT)
        except (InvalidOperation, ValueError):
            return False
    if name in {"iban", "vat_id"}:
        return compact(str(left)) == compact(str(right))
    return str(left).strip() == str(right).strip()


# --------------------------------------------------------------------------- Regeln
def _report(context: PipelineContext) -> dict[str, Any] | None:
    report = (context.artifacts.normalized_json or {}).get("donut_merge")
    return report if isinstance(report, dict) else None


class DonutPlausibilityRule(ValidationRule):
    def __init__(self) -> None:
        super().__init__(
            rule_id="VAL_DONUT_PLAUSIBILITY",
            name="donut_plausibility",
            description="Donut-Werte bestehen die Pflicht-Plausibilitätsprüfung",
        )

    async def evaluate(self, context: PipelineContext) -> Any:
        report = _report(context)
        if report is None:
            if (context.artifacts.ocr_raw_json or {}).get("engine") == "donut":
                return self.result(self.severity, "REVIEW", "Donut ohne Zusammenführungsbericht")
            return self.result("INFO", "PASS", "No Donut result")
        rejected = {
            name: entry["checks"]
            for name, entry in report["fields"].items()
            if entry["decision"] == "rejected"
        }
        if not rejected:
            return self.result("INFO", "PASS", "Donut values plausible")
        return self.result(
            self.severity,
            "FAIL",
            "Donut-Werte unplausibel: " + ", ".join(sorted(rejected)),
            evidence=rejected,
        )


class DonutDisagreementRule(ValidationRule):
    def __init__(self) -> None:
        super().__init__(
            rule_id="VAL_DONUT_DISAGREEMENT",
            name="donut_disagreement",
            description=(
                "Donut-Werte bestätigt (Konfidenz oder Tesseract-Text) und widerspruchsfrei"
            ),
        )

    async def evaluate(self, context: PipelineContext) -> Any:
        report = _report(context)
        if report is None:
            return self.result("INFO", "PASS", "No Donut result")
        open_fields = {
            name: entry["decision"]
            for name, entry in report["fields"].items()
            if entry["decision"] in {"disagreement", "unconfirmed"}
        }
        if not open_fields:
            return self.result("INFO", "PASS", "Donut values confirmed")
        return self.result(
            self.severity,
            "REVIEW",
            "Donut-Werte unbestätigt oder widersprüchlich: " + ", ".join(sorted(open_fields)),
            evidence=open_fields,
        )


def donut_rules() -> list[ValidationRule]:
    return [DonutPlausibilityRule(), DonutDisagreementRule()]
