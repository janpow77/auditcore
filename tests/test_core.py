"""Core model and rule semantics."""

from decimal import Decimal

import pytest

from auditcore.models import CheckResult, CheckStatus, ValidationResult
from auditcore.provenance import ProvenanceRecord, SourceReference
from auditcore.rules import RuleSet, RuleSetMetadata


def test_unknown_or_empty_checks_do_not_pass():
    assert not ValidationResult().valid
    assert not ValidationResult((CheckResult("x", CheckStatus.NOT_EXECUTED, "absent"),)).valid
    assert ValidationResult((CheckResult("x", CheckStatus.PASS, "observed"),)).valid


def test_rules_are_explicit_not_invented():
    rules = RuleSet(
        RuleSetMetadata("synthetic", "1", "synthetic fixture", "2026-01-01"),
        (("threshold", Decimal("0.25")),),
    )
    assert rules.value("threshold") == Decimal("0.25")
    with pytest.raises(KeyError):
        rules.value("unknown")


def test_multiple_provenance_sources():
    sources = (SourceReference("a", "x.py", "f", "one"), SourceReference("b", "y.py", "g", "two"))
    record = ProvenanceRecord("auditcore.reporting.f", sources, "0.1.0", "golden", "license")
    assert len(record.sources) == 2
