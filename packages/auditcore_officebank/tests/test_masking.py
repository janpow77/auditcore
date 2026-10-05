"""Ausgabe-Maskierung: Secrets erscheinen nie im Klartext (synthetische Werte)."""

from __future__ import annotations

import re

import pytest

from auditcore_officebank import mask_secrets


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Authorization: Bearer abc.DEF-123", "Authorization: ****"),
        ("curl -H 'bearer abc123'", "curl -H 'bearer ****'"),
        (
            "Server=db;Database=x;User Id=app;Password=geheim1;",
            "Server=db;Database=x;User Id=app;Password=****;",
        ),
        ("Pwd = 'mit leer';", "Pwd = ****;"),
        ('SA_PASSWORD="A b"', "SA_PASSWORD=****"),
        ("token: t0k3n, weiter", "token: ****, weiter"),
        ("ohne Geheimnis", "ohne Geheimnis"),
    ],
    ids=["authorization", "bearer", "password", "pwd", "sa-password", "token", "neutral"],
)
def test_builtin_patterns(text: str, expected: str) -> None:
    assert mask_secrets(text) == expected


def test_extra_patterns_from_project() -> None:
    pattern = re.compile(r"AZ-\d{4}")
    assert mask_secrets("Vorgang AZ-1234 geprüft", [pattern]) == "Vorgang **** geprüft"
