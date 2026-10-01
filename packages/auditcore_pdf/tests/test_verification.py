"""Tests für die unabhängige Nachprüfung von Schwärzungen."""

from __future__ import annotations

from auditcore_pdf import (
    verify_redaction,
)


def test_verify_redaction_clean(sample_pdf: bytes) -> None:
    res = verify_redaction(sample_pdf, forbidden_terms=["NICHT_VORHANDEN"])
    assert res.clean is True
    assert len(res.violations) == 0


def test_verify_redaction_detects_violation(sensitive_pdf: bytes) -> None:
    res = verify_redaction(sensitive_pdf, forbidden_terms=["STRENG_GEHEIM"])
    assert res.clean is False
    assert len(res.violations) > 0
    # Verletzungen in Text, Titel, Anmerkung oder Anhang
    violation_texts = " ".join(res.violations)
    assert "STRENG_GEHEIM" in violation_texts
