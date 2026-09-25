"""Differential test: originals vs ``strict`` – committed report is current and explained."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).parents[1]


def _tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location("difference_report",
                                                  ROOT / "tools" / "difference_report.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


#: Every change of verdict must have one of these strict reasons (see docs/profiles.md).
ALLOWED_STRICTER = {
    "INVALID:invalid_checksum",  # no MOD 97 / no check digit in the original
    "INVALID:invalid_length",  # register length for countries the original did not know
    "INVALID:invalid_format",  # BBAN structure, BE 9-digit numbers
    "INVALID:invalid_characters",  # \\d / isdigit accepted non-ASCII digits, ord()-55 quirk
    "INVALID:unknown_country",  # BIC/IBAN country codes that do not exist
}
ALLOWED_MORE_LENIENT_OR_MISSING = {"VALID", "MISSING:missing"}


def test_committed_difference_report_is_current() -> None:
    committed = json.loads((ROOT / "tests" / "fixtures" / "differences.json").read_text("utf-8"))
    tool = _tool()
    rows = tool.compute()
    assert rows == committed
    assert (ROOT / "docs" / "differences.md").read_text("utf-8") == tool.markdown(rows)


def test_every_difference_is_explained() -> None:
    for row in _tool().compute():
        if row["legacy"] == "VALID":
            assert row["strict"] in ALLOWED_STRICTER, row
        else:
            assert row["strict"] in ALLOWED_MORE_LENIENT_OR_MISSING | ALLOWED_STRICTER, row


def test_flowinvoice_iban_without_mod97_is_the_largest_difference() -> None:
    rows = {(r["comparison"], r["strict"]): r["count"] for r in _tool().compute()}
    assert rows[("flowinvoice validate_iban", "INVALID:invalid_checksum")] > 500
    assert ("Pipeline IbanChecksumRule", "INVALID:invalid_checksum") not in rows
