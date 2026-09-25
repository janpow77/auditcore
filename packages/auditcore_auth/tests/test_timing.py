"""Timing-safe comparisons: every secret comparison goes through a constant-time primitive."""

from __future__ import annotations

import ast
import hmac
from pathlib import Path

import pytest

import auditcore_auth
from auditcore_auth import constant_time_equals

PACKAGE = Path(auditcore_auth.__file__).parent


def test_constant_time_equals_delegates_to_compare_digest(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[bytes, bytes]] = []
    original = hmac.compare_digest

    def spy(a: bytes, b: bytes) -> bool:
        calls.append((a, b))
        return original(a, b)

    monkeypatch.setattr(hmac, "compare_digest", spy)
    assert constant_time_equals("Prüfung", "Prüfung".encode())
    assert not constant_time_equals("a", "ab")
    assert calls[0] == ("Prüfung".encode(), "Prüfung".encode())


def test_non_text_is_refused() -> None:
    with pytest.raises(TypeError):
        constant_time_equals(1, "1")  # type: ignore[arg-type]


def test_no_plain_equality_on_secret_material() -> None:
    """Hashes, signatures and keys are never compared with == / != in the library."""
    sensitive = {"stored", "secret", "signature", "digest", "key", "password", "expected"}
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare) and any(
                isinstance(op, ast.Eq | ast.NotEq) for op in node.ops
            ):
                names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
                assert not names & sensitive, f"{path.name}:{node.lineno}"
