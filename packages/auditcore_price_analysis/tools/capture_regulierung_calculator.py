"""Characterize regulierung's price calculation by executing the original code.

Run with an interpreter that provides SQLAlchemy and the regulierung backend
dependencies (for example the regulierung backend venv), against a clean,
GitHub-verified checkout of the pinned commit::

    python -I tools/capture_regulierung_calculator.py <regulierung-checkout> \
        tests/fixtures/regulierung_calculator_observed.json

``services/calculator.py`` is loaded directly from its file (it only uses the
standard library). ``services/preisauswahl.py`` imports ORM models; the
application database is redirected to in-memory SQLite before the import and
only the two pure selection functions are called. Every case records the
exact inputs and either the returned value or the raised exception.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
import types
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

COMMIT = "853676d2b1ab792395d63c62c9f96d5edcca8c2d"
FILES = {
    "backend/app/services/calculator.py": "1d40c9ef739e8933b4ec8195226f5eef117389ba",
    "backend/app/services/preisauswahl.py": "89b5cec43867794918cfcb851878eb6dfddf1abc",
}


def blob(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode() + b"\0" + raw, usedforsecurity=False
    ).hexdigest()


# --- JSON encoding of inputs and outputs -------------------------------------------------


def encode(value: Any) -> Any:
    """Type-preserving JSON form (Decimal, date, datetime, non-finite floats, objects)."""
    if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        if math.isnan(value):
            return {"$float": "nan"}
        if math.isinf(value):
            return {"$float": "inf" if value > 0 else "-inf"}
        return value
    if isinstance(value, Decimal):
        return {"$decimal": str(value)}
    if isinstance(value, datetime):
        return {"$datetime": value.isoformat()}
    if isinstance(value, date):
        return {"$date": value.isoformat()}
    if isinstance(value, types.SimpleNamespace):
        return {"$obj": {k: encode(v) for k, v in vars(value).items()}}
    if isinstance(value, dict):
        return {str(k): encode(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [encode(v) for v in value]
    if isinstance(value, set):
        return {"$set": sorted(encode(v) for v in value)}
    raise TypeError(f"not encodable: {type(value).__name__}")


def decode(value: Any) -> Any:
    """Inverse of :func:`encode`."""
    if isinstance(value, list):
        return [decode(v) for v in value]
    if not isinstance(value, dict):
        return value
    if "$float" in value:
        return float(value["$float"])
    if "$decimal" in value:
        return Decimal(value["$decimal"])
    if "$datetime" in value:
        return datetime.fromisoformat(value["$datetime"])
    if "$date" in value:
        return date.fromisoformat(value["$date"])
    if "$obj" in value:
        return types.SimpleNamespace(**{k: decode(v) for k, v in value["$obj"].items()})
    if "$set" in value:
        return {decode(v) for v in value["$set"]}
    return {k: decode(v) for k, v in value.items()}


# --- case catalogue (synthetic tariffs, no provider data) ---------------------------------

NW_A = {
    "grundpreis_eur_kw": 28.50,
    "arbeitspreis_ct_kwh": 10.82,
    "verrechnungspreis_eur_jahr": 154.80,
    "emissionspreis_ct_kwh": 0.68,
    "umlagenpreis_ct_kwh": 0.39,
    "waermeumlagenpreis_ct_kwh": 0.54,
}
NW_B = {
    "grundpreis_eur_kw": 32.10,
    "arbeitspreis_ct_kwh": 11.45,
    "verrechnungspreis_eur_jahr": 180.00,
    "emissionspreis_ct_kwh": 0.72,
    "umlagenpreis_ct_kwh": 0.39,
    "waermeumlagenpreis_ct_kwh": 0.54,
}
WA_A = {
    "grundpreis_eur_monat": 8.50,
    "arbeitspreis_eur_m3": 2.15,
    "verrechnungspreis_eur_monat": 0.0,
    "wasserentnahmeentgelt_eur_m3": 0.10,
}
STAFFEL3 = [
    {"bis_m3": 50, "preis": 1.80},
    {"bis_m3": 200, "preis": 2.20},
    {"bis_m3": 500, "preis": 2.50},
]
WA_S = {
    "grundpreis_eur_monat": 10.00,
    "arbeitspreis_staffel": STAFFEL3,
    "verrechnungspreis_eur_monat": 2.50,
    "wasserentnahmeentgelt_eur_m3": 0.15,
}


def without(data: dict[str, Any], *keys: str) -> dict[str, Any]:
    return {k: v for k, v in data.items() if k not in keys}


def with_(data: dict[str, Any], **changes: Any) -> dict[str, Any]:
    return {**data, **changes}


def cases() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    def add(group: str, function: str, *args: Any, **kwargs: Any) -> None:
        out.append(
            {
                "id": f"{group}-{len([c for c in out if c['group'] == group]) + 1:03d}",
                "group": group,
                "function": function,
                "args": encode(list(args)),
                "kwargs": encode(kwargs),
            }
        )

    nw = "calculate_nahwaerme"
    # Referenzfälle, Stichtage und Umlagenwechsel
    for stichtag in ("2025-01-01", "2025-06-30", "2025-07-01", "2026-09-01", "2020-02-29"):
        add("nw-stichtag", nw, NW_A, kw=12, kwh=27000, stichtag=stichtag)
    add("nw-stichtag", nw, NW_A, kw=12, kwh=27000, stichtag=date(2025, 7, 1))
    add("nw-stichtag", nw, NW_A, kw=12, kwh=27000, stichtag=date(2025, 6, 30))
    add("nw-stichtag", nw, NW_A, kw=12, kwh=27000, stichtag=datetime(2025, 7, 1, 12, 0))
    add("nw-stichtag", nw, NW_A, kw=12, kwh=27000, stichtag="01.07.2025")
    add("nw-stichtag", nw, NW_A, kw=12, kwh=27000, stichtag="2025-13-01")
    add("nw-stichtag", nw, NW_A, kw=12, kwh=27000, stichtag="2025-07-01T00:00:00")
    add("nw-stichtag", nw, NW_A)
    add("nw-stichtag", nw, NW_B, kw=12, kwh=27000, stichtag="2025-01-01")
    # Umlage je Regime fehlt
    add("nw-umlage", nw, without(NW_A, "umlagenpreis_ct_kwh"), stichtag="2025-01-01")
    add("nw-umlage", nw, without(NW_A, "umlagenpreis_ct_kwh"), stichtag="2025-07-01")
    add("nw-umlage", nw, without(NW_A, "waermeumlagenpreis_ct_kwh"), stichtag="2025-07-01")
    add("nw-umlage", nw, without(NW_A, "waermeumlagenpreis_ct_kwh"), stichtag="2025-01-01")
    add("nw-umlage", nw, with_(NW_A, waermeumlagenpreis_ct_kwh=-0.1), stichtag="2025-01-01")
    add("nw-umlage", nw, with_(NW_A, waermeumlagenpreis_ct_kwh=-0.1), stichtag="2025-07-01")
    # Verbrauchswerte und Grenzwerte
    for kw, kwh in (
        (5, 27000),
        (12, 50000),
        (0, 27000),
        (12, 0),
        (0, 0),
        (12.5, 27000.5),
        ("12", "27000"),
        (Decimal("12"), Decimal("27000")),
        (None, 27000),
        (12, None),
        (-1, 27000),
        (12, -0.01),
        ("12,5", 27000),
        (float("nan"), 27000),
        (12, float("inf")),
        (True, 27000),
        (1e9, 1e9),
        (0.1, 0.3),
    ):
        add("nw-verbrauch", nw, NW_A, kw=kw, kwh=kwh, stichtag="2025-01-01")
    # Fehlende und ungültige Komponenten
    for key in NW_A:
        add("nw-fehlt", nw, without(NW_A, key), stichtag="2025-01-01")
        add("nw-fehlt", nw, with_(NW_A, **{key: None}), stichtag="2025-07-01")
    add("nw-fehlt", nw, {}, stichtag="2025-01-01")
    add("nw-fehlt", nw, {}, kwh=0, stichtag="2025-01-01")
    add("nw-fehlt", nw, {"grundpreis_eur_kw": 0, "arbeitspreis_ct_kwh": 0})
    add("nw-fehlt", nw, {"grundpreis_eur_kw": 25.0}, stichtag="2025-01-01")
    for bad in ("10,82", "abc", "", True, False, -1, float("nan"), [1], {"v": 1}, "1e2", " 7 "):
        add("nw-ungueltig", nw, with_(NW_A, arbeitspreis_ct_kwh=bad), stichtag="2025-01-01")
    add("nw-ungueltig", nw, with_(NW_A, grundpreis_eur_kw=Decimal("28.5")))
    add("nw-ungueltig", nw, with_(NW_A, grundpreis_eur_kw="28.50"))
    add("nw-ungueltig", nw, with_(NW_A, verrechnungspreis_eur_jahr=0.0))
    add("nw-ungueltig", nw, with_(NW_A, unbekannt_ct_kwh=9.9))
    # Rundung
    for ap in (0.005, 1.005, 2.675, 0.015, 0.025, 10.825, 1e-9, 123456.789):
        add(
            "nw-rundung",
            nw,
            {"grundpreis_eur_kw": 0, "arbeitspreis_ct_kwh": ap, "verrechnungspreis_eur_jahr": 0},
            kw=0,
            kwh=100,
            stichtag="2025-01-01",
        )
    add(
        "nw-rundung",
        nw,
        {
            "grundpreis_eur_kw": 0.001,
            "arbeitspreis_ct_kwh": 0.001,
            "verrechnungspreis_eur_jahr": 0.004,
            "emissionspreis_ct_kwh": 0.001,
            "umlagenpreis_ct_kwh": 0.001,
        },
        kw=5,
        kwh=500,
        stichtag="2025-01-01",
    )
    add(
        "nw-rundung",
        nw,
        {"grundpreis_eur_kw": 1.0, "arbeitspreis_ct_kwh": 1.0, "verrechnungspreis_eur_jahr": 1.0},
        kw=1,
        kwh=3,
        stichtag="2025-01-01",
    )

    wa = "calculate_wasser"
    add("wa-standard", wa, WA_A, q3=4, m3=150, stichtag="2025-01-01")
    add("wa-standard", wa, WA_A)
    for m3 in (0, 50, 150, 180, 500, 2.5, "150", Decimal("150"), None, -1, "1,5", float("inf")):
        add("wa-verbrauch", wa, WA_A, q3=4, m3=m3, stichtag="2025-01-01")
    for q3 in (2.5, 10, 0, None, -4, "x", 4):
        add("wa-q3", wa, WA_A, q3=q3, m3=150, stichtag="2025-01-01")
    for stichtag in ("2025-07-01", date(2024, 1, 1), "31.12.2025", datetime(2025, 1, 1)):
        add("wa-stichtag", wa, WA_A, stichtag=stichtag)
    for key in WA_A:
        add("wa-fehlt", wa, without(WA_A, key), m3=150)
        add("wa-fehlt", wa, with_(WA_A, **{key: None}), m3=150)
    add("wa-fehlt", wa, {}, m3=150)
    add("wa-fehlt", wa, {}, m3=0)
    for bad in ("2,15", True, -0.01, "nan", [2.15]):
        add("wa-ungueltig", wa, with_(WA_A, arbeitspreis_eur_m3=bad), m3=150)
    add("wa-rundung", wa, without(with_(WA_A, arbeitspreis_eur_m3=1.07), "x"), m3=2.5)
    add(
        "wa-rundung",
        wa,
        {
            "grundpreis_eur_monat": 0,
            "arbeitspreis_eur_m3": 1.07,
            "verrechnungspreis_eur_monat": 0,
            "wasserentnahmeentgelt_eur_m3": 0,
        },
        m3=2.5,
    )
    add(
        "wa-rundung",
        wa,
        {
            "grundpreis_eur_monat": 0.001,
            "arbeitspreis_eur_m3": 0.001,
            "verrechnungspreis_eur_monat": 0.001,
            "wasserentnahmeentgelt_eur_m3": 0.001,
        },
        m3=5,
    )
    add("wa-rundung", wa, with_(WA_A, arbeitspreis_eur_m3=1.005), m3=1)
    # Staffeln
    for m3 in (0, 25, 49.999, 50, 50.001, 150, 200, 200.5, 500, 750, 1e6):
        add("wa-staffel", wa, WA_S, q3=4, m3=m3, stichtag="2025-01-01")
    staffel_varianten: list[Any] = [
        [{"bis_m3": 50, "preis": 1.50}, {"bis_m3": 100, "preis": 2.00}],
        [{"bis_m3": 100, "preis": 2.00}, {"bis_m3": 50, "preis": 1.50}],
        [{"bis_m3": 100, "preis": 2.0}],
        [{"bis_m3": 50, "preis": 1.5}, {"bis_m3": 50, "preis": 2.0}],
        [{"bis_m3": 0, "preis": 1.5}],
        [{"bis_m3": None, "preis": 1.5}],
        [{"bis_m3": 50, "preis": 1.5}, {"bis_m3": None, "preis": 2.0}],
        [{"bis_m3": 50, "preis": None}, {"bis_m3": 100, "preis": 2.0}],
        [{"bis_m3": 50}],
        [{"preis": 2.0}],
        [{"bis_m3": -5, "preis": 2.0}],
        [{"bis_m3": 50, "preis": -2.0}],
        [{"bis_m3": "50", "preis": "1.5"}, {"bis_m3": "100,5", "preis": "2"}],
        [{"bis_m3": 50.5, "preis": 1.5}, {"bis_m3": 100.25, "preis": 2.0}],
        [["50", "1.5"]],
        ["50"],
        [],
        {"staffeln": [{"bis_m3": 50, "preis": 1.8}, {"bis_m3": 200, "preis": 2.2}]},
        {"staffeln": []},
        {"stufen": [{"bis_m3": 50, "preis": 1.8}]},
        {},
        "50:1.8",
        None,
        [{"bis_m3": 50, "preis": 1.5, "extra": "x"}, {"bis_m3": 100, "preis": 2.0}],
    ]
    for staffel in staffel_varianten:
        for data in (
            with_(WA_S, arbeitspreis_staffel=staffel),
            with_(WA_A, arbeitspreis_staffel=staffel),
        ):
            add("wa-staffelform", wa, data, m3=150)
    add("wa-staffelform", wa, with_(without(WA_S, "grundpreis_eur_monat")), m3=150)
    add("wa-staffelform", wa, with_(WA_S, arbeitspreis_eur_m3=None), m3=150)

    st = "_calculate_staffel"
    for staffel, m3 in (
        ([{"bis_m3": 100, "preis": 2.00}, {"bis_m3": 300, "preis": 2.50}], 150),
        ([{"bis_m3": 100, "preis": 2.00}, {"bis_m3": 300, "preis": 2.50}], 50),
        ([{"bis_m3": 100, "preis": 2.00}, {"bis_m3": 300, "preis": 2.50}], 400),
        ([{"bis_m3": 100, "preis": 2.00}, {"bis_m3": 300, "preis": 2.50}], 0),
        ([], 150),
        ([{"bis_m3": 50, "preis": 1.5}, {"bis_m3": 50, "preis": 2.0}], 100),
        ([{"bis_m3": 10, "preis": 0.333}], 1),
        ([{"bis_m3": 10, "preis": 0.335}], 1),
        ([{"bis_m3": 10, "preis": 1.005}], 1),
        ([{"bis_m3": 100, "preis": 2.0}], -1),
        ([{"bis_m3": 100, "preis": 2.0}], None),
        ([{"bis_m3": 100, "preis": 2.0}], "1,5"),
    ):
        add("staffel", st, staffel, m3)

    de = "calculate_delta"
    for a, s in (
        (120, 100),
        (80, 100),
        (100, 100),
        (100, 0),
        (0, 0),
        (100, -100),
        (100.25, 100),
        (100.35, 100),
        (100.05, 100),
        (1.1, 1.0),
        (3.3, 3.0),
        (0, 100),
        (1e12, 1),
        (1, 3),
        (2, 3),
        (100.15, 100),
        (100.45, 100),
    ):
        add("delta", de, a, s)

    co = "determine_compliance"
    for jk, med, schwelle in (
        (100, 100, 20),
        (115, 100, 20),
        (125, 100, 20),
        (110, 100, 20),
        (110.01, 100, 20),
        (120, 100, 20),
        (120.01, 100, 20),
        (50, 100, 20),
        (100, 0, 20),
        (100, -5, 20),
        (0, 100, 20),
        (1.1, 1.0, 20),
        (1.2, 1.0, 20),
        (3.3, 3.0, 20),
        (3.6, 3.0, 20),
        (100, 100, 0),
        (100.01, 100, 0),
        (105, 100, 10),
        (105.0000001, 100, 10),
        (100, 100, -10),
        (90, 100, -10),
        (130, 100, 50),
    ):
        add("compliance", co, jk, med, schwelle_pct=schwelle)
    add("compliance", co, 115, 100)

    cs = "calculate_cluster_statistics"
    for values in (
        [],
        [100.0],
        [100.0, 200.0],
        [300.0, 100.0, 200.0],
        [1.0, 2.0, 3.0, 4.0],
        [0.125, 0.135],
        [2.675, 2.675],
        [1.005, 1.015, 1.025],
        [-10.0, 10.0],
        [1e9, 1e9 + 1],
        [0.1, 0.2, 0.3],
        [5, 5, 5, 5],
        [3707.1, 3747.6, 3956.4, 4012.35, 2890.0],
    ):
        add("cluster", cs, values)

    ns = types.SimpleNamespace
    wp = "waehle_preis_deterministisch"
    d1, d2, d3 = date(2025, 1, 1), date(2025, 7, 1), date(2026, 1, 1)
    add("auswahl", wp, [])
    add("auswahl", wp, [ns(ref="a", stichtag=d1, variant_id=None, id=1)])
    add(
        "auswahl",
        wp,
        [
            ns(ref="a", stichtag=d1, variant_id=None, id=1),
            ns(ref="b", stichtag=d2, variant_id=None, id=2),
        ],
    )
    same = [
        ns(ref="a", stichtag=d2, variant_id=7, id=3),
        ns(ref="b", stichtag=d2, variant_id=3, id=9),
        ns(ref="c", stichtag=d2, variant_id=None, id=1),
        ns(ref="d", stichtag=d1, variant_id=1, id=2),
    ]
    add("auswahl", wp, same)
    add("auswahl", wp, same, {7})
    add("auswahl", wp, same, {1})
    add("auswahl", wp, same, {7, 3})
    add("auswahl", wp, same, set())
    add("auswahl", wp, same, None)
    add(
        "auswahl",
        wp,
        [
            ns(ref="a", stichtag=d2, variant_id=None, id=5),
            ns(ref="b", stichtag=d2, variant_id=None, id=2),
        ],
    )
    add(
        "auswahl",
        wp,
        [
            ns(ref="a", stichtag=d2, variant_id=0, id=5),
            ns(ref="b", stichtag=d2, variant_id=None, id=None),
        ],
    )
    add(
        "auswahl",
        wp,
        [ns(ref="a", stichtag=d3, variant_id=2, id=1), ns(ref="b", stichtag=d3, id=2)],
    )

    ww = "waehle_wasser_preis"
    rows = [
        ns(ref="q4-alt", stichtag=d1, variant_id=None, id=1, zaehlergroesse_q3=4.0),
        ns(ref="q10-neu", stichtag=d3, variant_id=None, id=2, zaehlergroesse_q3=10.0),
        ns(ref="q2.5", stichtag=d2, variant_id=None, id=3, zaehlergroesse_q3=2.5),
        ns(ref="qnone", stichtag=d2, variant_id=None, id=4, zaehlergroesse_q3=None),
    ]
    add("wasser-auswahl", ww, [], 4)
    for q3 in (4, 4.0, 4.005, 4.01, 3.995, 10, 2.5, 6, None, 0):
        add("wasser-auswahl", ww, rows, q3)
    add("wasser-auswahl", ww, rows, Decimal("4.0"))
    add(
        "wasser-auswahl",
        ww,
        [
            ns(ref="v1", stichtag=d2, variant_id=5, id=1, zaehlergroesse_q3=4.0),
            ns(ref="v2", stichtag=d2, variant_id=2, id=2, zaehlergroesse_q3=4.0),
            ns(ref="v3", stichtag=d3, variant_id=9, id=3, zaehlergroesse_q3=10.0),
        ],
        4,
        {5},
    )
    add("wasser-auswahl", ww, rows[3:], 4)
    return out


# --- execution ---------------------------------------------------------------------------


def jsonable_result(value: Any) -> Any:
    """Result encoding; selected ORM-like objects are reported by their ``ref``."""
    if isinstance(value, types.SimpleNamespace):
        return {"$ref": value.ref}
    if isinstance(value, tuple):
        return {"$tuple": [jsonable_result(v) for v in value]}
    if isinstance(value, float):
        return encode(value)
    if isinstance(value, dict):
        return {k: jsonable_result(v) for k, v in value.items()}
    if isinstance(value, list):
        return [jsonable_result(v) for v in value]
    return encode(value)


def load_calculator(root: Path) -> types.ModuleType:
    path = root / "backend/app/services/calculator.py"
    spec = importlib.util.spec_from_file_location("legacy_calculator", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_selection(root: Path) -> types.ModuleType:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    os.environ["HARVEST_NULLPOOL"] = "true"
    sys.path.insert(0, str(root / "backend"))
    import app.database as database  # noqa: PLC0415

    if not database.engine.url.drivername.startswith("sqlite"):
        raise SystemExit("Refusing to run: engine is not in-memory SQLite")
    from app.services import preisauswahl  # noqa: PLC0415

    return preisauswahl


def run(root: Path) -> dict[str, Any]:
    calculator = load_calculator(root)
    selection = load_selection(root)
    functions = {
        name: getattr(calculator, name)
        for name in (
            "calculate_nahwaerme",
            "calculate_wasser",
            "_calculate_staffel",
            "calculate_delta",
            "determine_compliance",
            "calculate_cluster_statistics",
        )
    }
    functions["waehle_preis_deterministisch"] = selection.waehle_preis_deterministisch
    functions["waehle_wasser_preis"] = selection.waehle_wasser_preis
    observed = []
    for case in cases():
        args = decode(case["args"])
        kwargs = decode(case["kwargs"])
        try:
            outcome: dict[str, Any] = {
                "ok": jsonable_result(functions[case["function"]](*args, **kwargs))
            }
        except Exception as exc:  # noqa: BLE001 - errors are part of the observed contract
            outcome = {"error": {"type": type(exc).__name__, "message": str(exc)}}
        observed.append({**case, **outcome})
    return {
        "constants": {
            "UMLAGEN_STICHTAG": calculator.UMLAGEN_STICHTAG.isoformat(),
            "CENT": str(calculator.CENT),
            "ZEHNTEL": str(calculator.ZEHNTEL),
            "Q3_TOLERANZ": selection.Q3_TOLERANZ,
            "DATENSTATUS_OK": selection.DATENSTATUS_OK,
            "DATENSTATUS_KEIN_Q3_TARIF": selection.DATENSTATUS_KEIN_Q3_TARIF,
        },
        "cases": observed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="clean regulierung checkout at the pinned commit")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    if head != COMMIT:
        raise SystemExit(f"Checkout ist {head}, erwartet {COMMIT}")
    dirty = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain", "--", *FILES],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if dirty:
        raise SystemExit("Quelldateien sind lokal verändert")
    files = []
    for path, expected in FILES.items():
        actual = blob(root / path)
        if actual != expected:
            raise SystemExit(f"Blob von {path} ist {actual}, erwartet {expected}")
        files.append({"path": path, "git_blob": actual})
    report = {
        "status": "OBSERVED",
        "scope": "LOCAL_LEGACY_CHARACTERIZATION",
        "repository": "janpow77/regulierung",
        "commit": COMMIT,
        "files": files,
        "python": sys.version.split()[0],
        **run(root),
    }
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"{len(report['cases'])} Fälle beobachtet")


if __name__ == "__main__":
    main()
