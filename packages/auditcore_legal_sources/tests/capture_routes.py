"""Synthetic DIP items identical to ``tools/capture_legacy_harvesters.py:drucksache``."""

from __future__ import annotations

from typing import Any


def drucksache(n: int, **extra: Any) -> dict[str, Any]:
    """Synthetic DIP ``drucksache`` item in the documented API response shape."""
    base: dict[str, Any] = {
        "id": str(270000 + n),
        "titel": f"Synthetische Drucksache {n} zur EFRE-Förderung",
        "dokumentnummer": f"20/{1000 + n}",
        "wahlperiode": 20,
        "datum": "2024-03-15",
        "drucksachetyp": "Kleine Anfrage",
        "fundstelle": {"pdf_url": f"https://example.invalid/btd/20/{n}.pdf"},
        "urheber": [{"titel": "Fraktion X"}],
        "autoren_anzeige": [],
        "vorgangsbezug": [],
        "abstract": "",
    }
    base.update(extra)
    return base
