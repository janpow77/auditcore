"""Tests für die Textmaskierung mit Schutzpunkten."""

from __future__ import annotations

from auditcore_privacy import mask_text


def test_mask_empty_and_whitespace() -> None:
    """Leere Texte oder reine Leerzeichen liefern leeren String."""
    assert mask_text("") == ""
    assert mask_text("   ") == ""


def test_mask_short_text() -> None:
    """Kurze Zeichenfolgen werden vollständig überdeckt."""
    # Standard: prefix_len=4, suffix_len=2 -> Schwelle: 4 + 2 + 2 = 8
    assert mask_text("12345") == "•••••"
    assert mask_text("12345678") == "••••••••"


def test_mask_longer_text() -> None:
    """Längere Zeichenfolgen behalten Anfang und Ende, Maskierung in der Mitte."""
    result = mask_text("DE12345678901234567890")
    assert result.startswith("DE12")
    assert result.endswith("90")
    assert "•" in result
    # Länge bleibt unverändert
    assert len(result) == len("DE12345678901234567890")


def test_mask_custom_lengths() -> None:
    """Benutzerdefinierte Randlängen."""
    res = mask_text("Max Mustermann", prefix_len=3, suffix_len=4)
    assert res.startswith("Max")
    assert res.endswith("mann")
