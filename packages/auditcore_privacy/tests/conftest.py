"""Gemeinsame Fixtures und Testdaten für auditcore_privacy."""

from __future__ import annotations

import pytest

from auditcore_privacy import MappingStore, PseudonymEngine


@pytest.fixture
def sample_salt() -> str:
    """Fester Salt für deterministische Testläufe."""
    return "0123456789abcdef0123456789abcdef"


@pytest.fixture
def alternate_salt() -> str:
    """Abweichender Salt zur Prüfung von Scope-Unterschieden."""
    return "fedcba9876543210fedcba9876543210"


@pytest.fixture
def engine(sample_salt: str) -> PseudonymEngine:
    """PseudonymEngine mit Test-Scope und festem Salt."""
    return PseudonymEngine(scope_key="test-scope-2026", salt=sample_salt)


@pytest.fixture
def store() -> MappingStore:
    """Frischer MappingStore für Tests."""
    return MappingStore()
