"""IBAN-/USt-IdNr.-Grundlagen und Regelbasis der Validierung (aus ``stages/validation.py``)."""

from __future__ import annotations

from typing import Any

from auditcore_documents.pipeline.context import PipelineContext, ValidationResult

IBAN_COUNTRY_LENGTHS = {
    "DE": 22,
    "AT": 20,
    "CH": 21,
    "FR": 27,
    "IT": 27,
    "ES": 24,
    "NL": 18,
    "BE": 16,
    "GB": 22,
}
VAT_ID_PATTERNS = {
    "DE": r"^DE\d{9}$",
    "AT": r"^ATU\d{8}$",
    "FR": r"^FR[A-Z0-9]{2}\d{9}$",
    "IT": r"^IT\d{11}$",
    "ES": r"^ES[A-Z0-9]\d{7}[A-Z0-9]$",
    "NL": r"^NL\d{9}B\d{2}$",
    "BE": r"^BE0?\d{9,10}$",
    "GB": r"^GB\d{9}$|^GB\d{12}$|^GBGD\d{3}$|^GBHA\d{3}$",
}


def validate_iban(iban: str) -> tuple[bool, str]:
    """Längen- und Modulo-97-Prüfung nach ISO 13616 (Meldungen wie im Original)."""
    iban = iban.replace(" ", "").upper()
    if len(iban) < 15 or len(iban) > 34:
        return False, f"Invalid IBAN length: {len(iban)}"
    country = iban[:2]
    expected = IBAN_COUNTRY_LENGTHS.get(country)
    if expected is not None and len(iban) != expected:
        return False, f"Invalid IBAN length for {country}: expected {expected}, got {len(iban)}"
    rearranged = iban[4:] + iban[:4]
    numeric = "".join(char if char.isdigit() else str(ord(char) - 55) for char in rearranged)
    try:
        if int(numeric) % 97 != 1:
            return False, "IBAN checksum invalid"
    except ValueError:
        return False, "IBAN contains invalid characters"
    return True, ""


class ValidationRule:
    rule_id: str
    name: str
    description: str
    severity: str = "WARN"
    action_on_fail: str = "REVIEW_NEEDED"

    def __init__(
        self,
        rule_id: str,
        name: str,
        description: str = "",
        severity: str = "WARN",
        action_on_fail: str = "REVIEW_NEEDED",
        threshold: float | None = None,
    ) -> None:
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.severity = severity
        self.action_on_fail = action_on_fail
        self.threshold = threshold

    async def evaluate(self, context: PipelineContext) -> ValidationResult:
        raise NotImplementedError

    def result(self, severity: Any, outcome: Any, message: str, **extra: Any) -> ValidationResult:
        return ValidationResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            severity=severity,
            outcome=outcome,
            message=message,
            **extra,
        )
