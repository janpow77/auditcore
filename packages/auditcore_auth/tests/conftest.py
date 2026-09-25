"""Shared fixtures: the executed legacy observations and fast test profiles."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from functools import cache
from pathlib import Path

from auditcore_auth import HashScheme, PasswordProfile, TokenProfile

FIXTURES = Path(__file__).parent / "fixtures"
KEY = "unit-test-secret-0123456789abcdefghij"
NOW = datetime(2026, 9, 25, 12, 0, 0, tzinfo=UTC)

# Fast profiles for unit tests (the characterisation uses the real cost factors).
FAST_BCRYPT = PasswordProfile("fast-bcrypt", HashScheme.BCRYPT, bcrypt_rounds=4)
FAST_TOKEN = TokenProfile("unit", lifetime=timedelta(minutes=10))


@cache
def observed() -> dict[str, object]:
    data: dict[str, object] = json.loads(
        (FIXTURES / "legacy_auth_observed.json").read_text(encoding="utf-8")
    )
    return data


def observed_app(app: str) -> dict[str, object]:
    apps = observed()["apps"]
    assert isinstance(apps, dict)
    record = apps[app]
    assert isinstance(record, dict)
    return record
