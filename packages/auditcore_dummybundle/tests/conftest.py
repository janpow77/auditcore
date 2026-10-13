"""Gemeinsame Hilfen der Tests: Konfigurationen und Bündel aus synthetischen Parametern."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal
from typing import Any

from auditcore_dummybundle import BundleConfig
from auditcore_dummybundle.model import Row, amount

BASE_DATE = date(2026, 1, 1)


def config(seed: int = 42, **changes: Any) -> BundleConfig:
    """Standardkonfiguration mit Änderungen."""
    return replace(BundleConfig(seed=seed, base_date=BASE_DATE), **changes)


def total(rows: list[Row], key: str) -> Decimal:
    """Summe einer Betragsspalte."""
    return sum((amount(row, key) for row in rows), Decimal("0.00"))
