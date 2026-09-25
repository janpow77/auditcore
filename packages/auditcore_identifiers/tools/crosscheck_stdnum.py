"""Independent cross-check: record python-stdnum verdicts for the same samples.

python-stdnum (LGPL) is used only in this offline tool, never by the library or
its tests; the verdicts are stored as data in ``tests/fixtures/stdnum_crosscheck.json``.
It additionally searches, per EU member state, numbers that stdnum accepts
(format *and* national check digits), so the strict formats can be tested for
not rejecting real-world-valid numbers.

    <venv with python-stdnum>/bin/python tools/crosscheck_stdnum.py tests/fixtures
"""

from __future__ import annotations

import argparse
import json
import random
import string
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

import samples  # noqa: E402
import stdnum  # noqa: E402
from stdnum import bic, iban, lei  # noqa: E402
from stdnum.de import idnr, stnr  # noqa: E402
from stdnum.eu import vat  # noqa: E402
from stdnum.gb import vat as gb_vat  # noqa: E402

from auditcore_identifiers.registry import IBAN_BBAN_STRUCTURE  # noqa: E402  (inputs only)
from auditcore_identifiers.vat import EU_VAT_FORMATS  # noqa: E402  (prefix list only)


def _vat_valid(value: str | None) -> bool:
    if not value:
        return False
    text = value.strip().upper()
    if text.startswith("GB"):
        return bool(gb_vat.is_valid(text))
    return bool(vat.is_valid(text))


def _verdicts(values: list[str | None], check: Any) -> list[dict[str, Any]]:
    return [{"value": v, "stdnum_valid": bool(v) and bool(check(v))} for v in values]


def _search(prefix: str, rng: random.Random, wanted: int) -> list[str]:
    """Random candidates of 7–12 characters until stdnum accepts ``wanted`` numbers."""
    found: list[str] = []
    alphabet = string.digits * 4 + string.ascii_uppercase
    for _ in range(400_000):
        length = rng.randint(7, 12)
        body = "".join(rng.choice(alphabet) for _ in range(length))
        if prefix == "AT":
            body = "U" + body[:8]
        elif prefix == "SE":
            body = "".join(rng.choice(string.digits) for _ in range(10)) + "01"
        if vat.is_valid(prefix + body):
            found.append(vat.compact(prefix + body))
            if len(found) == wanted:
                break
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    vat_values = list(dict.fromkeys(v for v, _ in samples.vat_samples()))
    rng = random.Random(samples.SEED + 9)
    data = {
        "status": "OBSERVED",
        "tool": "tools/crosscheck_stdnum.py",
        "stdnum_version": stdnum.__version__,
        "iban": _verdicts(samples.iban_samples(dict(IBAN_BBAN_STRUCTURE)), iban.is_valid),
        "bic": _verdicts(samples.bic_samples(), bic.is_valid),
        "lei": _verdicts(samples.lei_samples(), lei.is_valid),
        "vat_id": _verdicts(vat_values, _vat_valid),
        "tax_id": _verdicts(samples.tax_id_samples(), idnr.is_valid),
        "tax_number": _verdicts(samples.tax_number_samples(), stnr.is_valid),
        "vat_valid_by_country": {
            prefix: _search(prefix, rng, 8) for prefix in sorted(EU_VAT_FORMATS)
            if prefix != "XI"
        },
    }
    target = args.output / "stdnum_crosscheck.json"
    target.write_text(json.dumps(data, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
