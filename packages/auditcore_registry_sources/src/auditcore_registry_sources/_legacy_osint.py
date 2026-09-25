"""osint replays: chamber and register downloads with their console output."""

from __future__ import annotations

import json
from typing import TypedDict

from auditcore_common.text import group_thousands_de

from . import chambers
from .chambers import ChamberRecord

#: Return value, written file and console output of an osint download script.
ScriptRun = TypedDict(
    "ScriptRun", {"return": int, "file": list[ChamberRecord], "stdout": str, "stderr": str}
)


def osint_zer(status: bytes, register: bytes) -> ScriptRun:
    """``zer_holen``: returned count, written file and console output."""
    total = json.loads(status).get("total", 0)
    delivery = chambers.parse_zer_register(register)
    return {
        "return": len(delivery.records),
        "file": list(delivery.records),
        "stdout": f"  Register meldet {group_thousands_de(total)} Einträge, lade …\n",
        "stderr": "",
    }


def osint_ihk(data: bytes) -> list[ChamberRecord]:
    """``ihk_holen``."""
    return list(chambers.parse_ihk_locations(data).records)


def osint_hwk(html: bytes) -> list[ChamberRecord]:
    """``hwk_holen``."""
    return list(chambers.parse_hwk_page(html, expected=None).records)


def osint_kammern(ihk: bytes, html: bytes) -> ScriptRun:
    """``kammern_holen``: IHK and HWK with the warning below 53 chambers of crafts."""
    first, second = osint_ihk(ihk), osint_hwk(html)
    warning = (
        "  Achtung: Die ZDH-Seite hat sich offenbar geändert — es sollten 53 "
        "Handwerkskammern sein.\n"
        if len(second) < chambers.EXPECTED_HWK
        else ""
    )
    return {
        "return": len(first) + len(second),
        "file": first + second,
        "stdout": f"  {len(first)} Industrie- und Handelskammern, {len(second)} Handwerkskammern\n",
        "stderr": warning,
    }
