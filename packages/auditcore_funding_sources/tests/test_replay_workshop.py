"""Every recorded flowworkshop output is reproduced exactly (types included)."""

from __future__ import annotations

from typing import Any

import pytest
from conftest import FIXTURES, encode, load, revive

from auditcore_funding_sources import workshop

DATA = load("flowworkshop")
#: FS-W04: the source aborted on title rows with fewer fields (ParserError);
#: this library reads such files. Replayed separately in test_tables.py.
CORRECTED = [
    c for c in DATA["cases"] if c["exception"] and "semikolon_titelzeilen.csv" in c["name"]
]
CASES = [c for c in DATA["cases"] if c not in CORRECTED]


def run(case: dict[str, Any]) -> Any:
    op, i = case["operation"], revive(case["inputs"])
    w = workshop
    simple = {
        "workshop.parse_amount": w.parse_amount,
        "workshop.parse_date": w.parse_date,
        "workshop.strip_accents": w.strip_accents,
        "workshop.normalize_for_hash": w.normalize_for_hash,
        "workshop.normalize_company_name_simple": w.normalize_company_name_simple,
        "workshop.detect_sa_reference": w.detect_sa_reference,
        "workshop.stringify": w.stringify,
        "workshop.stringify_plz": w.stringify_plz,
        "workshop.coerce_float": w.coerce_float,
    }
    if op in simple:
        return simple[op](i["value"])
    if op == "workshop.normalize_company_name":
        return w.normalize_company_name(i["value"], drop_filler=i["drop_filler"])
    if op == "workshop.compute_record_hash":
        return w.compute_record_hash(i["row"], i["source_key"])
    if op == "workshop.detect_canonical_columns":
        return w.detect_canonical_columns(i["headers"], i["mapping"])
    if op == "workshop.parse_xlsx_or_csv":
        content = (FIXTURES / "files" / i["file"]).read_bytes()
        return w.parse_file(
            content,
            i["file"],
            header_row=i.get("header_row", 0),
            field_mapping=i.get("field_mapping"),
            sheet=i.get("sheet"),
        )
    if op == "workshop.read_table":
        from auditcore_funding_sources.tables import read_table

        content = (FIXTURES / "files" / i["file"]).read_bytes()
        table = read_table(content, i["file"], header_row=i.get("header_row", 0))
        return {"headers": list(table.headers), "rows": [_plain(r) for r in table.rows]}
    if op == "workshop.filter_by_fund":
        return w.filter_by_fund(i["rows"], i["fonds"])
    if op == "workshop.validate_rows":
        return w.validate_rows(i["rows"], w.SnapshotContext(**i["params"]))
    raise AssertionError(op)


def _plain(row: tuple[Any, ...]) -> list[Any]:
    import math

    return [None if isinstance(v, float) and math.isnan(v) else _item(v) for v in row]


def _item(value: Any) -> Any:
    return value


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_recorded_output(case: dict[str, Any]) -> None:
    if case["exception"]:
        with pytest.raises(Exception) as caught:
            run(case)
        assert type(caught.value).__name__ == case["exception"]["type"] or isinstance(
            caught.value, ValueError
        )
        assert str(caught.value) == case["exception"]["message"]
    else:
        assert encode(run(case)) == case["output"]


def test_fixture_is_complete() -> None:
    assert len(DATA["cases"]) == 315
    assert len(CORRECTED) == 3
    assert DATA["source"]["commit"] == "a05bb2143bd96d5e981f9462f05b965e1658be36"
    assert DATA["source"]["checkout_clean"] is True
