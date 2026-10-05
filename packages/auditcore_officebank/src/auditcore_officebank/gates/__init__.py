"""Gates vor jeder Weitergabe von Code: ascii, lint-vba, lint-sql, datenschutz, mcp.

Geplant für Etappe 1 (Plan, Kap. 2.8). Reihenfolge in ``gate alle``: ascii →
lint → datenschutz → mcp, Abbruch beim ersten Rot. Statische Prüfungen setzen
``native_office_compile`` immer auf ``not_run``.
"""

from __future__ import annotations

from typing import Final

GATE_ORDER: Final = ("ascii", "lint", "datenschutz", "mcp")
NATIVE_COMPILE_NOT_RUN: Final = "not_run"

__all__ = ["GATE_ORDER", "NATIVE_COMPILE_NOT_RUN"]
