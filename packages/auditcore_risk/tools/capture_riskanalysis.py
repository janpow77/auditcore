"""Execute the original riskanalysis red-flag engine and record inputs/outputs.

The pinned files ``backend/app/pipeline/red_flags.py`` and
``payee_normalizer.py`` are verified by Git blob and then imported unchanged
from the checkout (their only imports are pandas, NumPy and rapidfuzz). The
tool never imports ``auditcore_risk`` and never touches a database or network.
Run it with the versions pinned in riskanalysis ``backend/requirements.txt``
(pandas 3.0.5, NumPy 2.5.1, rapidfuzz 3.14.5)::

    python tools/capture_riskanalysis.py <riskanalysis checkout> \
        tests/fixtures/riskanalysis_observed.json

All names and amounts are synthetic.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import platform
import random
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import rapidfuzz

REPOSITORY = "janpow77/riskanalysis"
COMMIT = "b5c523bf7eaa326153778d9751f176f03d4d56ed"
FILES = {
    "backend/app/pipeline/red_flags.py": "b6196a7dbd3838bd4dd361c71e3cc44c904f4980",
    "backend/app/pipeline/payee_normalizer.py": "fceae5b0d3364c5b20cc638ce4453ac082085aa7",
    "backend/tests/test_red_flags.py": "3585409565a1f6bb0315f6905f998592fa114725",
}
FLAG_COLUMNS = ["rf01", "rf02", "rf08", "rf09", "rf10", "rf11", "rf12", "rf13", "rf14", "rf15"]
NAN = float("nan")


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(  # noqa: S324 - Git blob identity
        b"blob " + str(len(raw)).encode() + b"\0" + raw, usedforsecurity=False
    ).hexdigest()


def encode(value: Any) -> Any:
    """JSON form that keeps NaN/inf and timestamps distinguishable from ``None``."""
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, float | np.floating):
        v = float(value)
        if math.isnan(v):
            return {"$float": "nan"}
        if math.isinf(v):
            return {"$float": "inf" if v > 0 else "-inf"}
        return v
    if value is pd.NaT:
        return {"$nat": True}
    if isinstance(value, pd.Timestamp):
        return {"$datetime": value.isoformat()}
    if isinstance(value, list):
        return [encode(v) for v in value]
    if isinstance(value, dict):
        return {k: encode(v) for k, v in value.items()}
    return value


def base_row(**kw: Any) -> dict[str, Any]:
    """Same default row as ``backend/tests/test_red_flags.py::_row``."""
    row = {
        "bruttobetrag": 1234.0,
        "abweichungen_betrag": 0.0,
        "vergabenummer": "VG-2021-0815",
        "kostenart_auswertung_bezeichnung": "Sachausgaben",
        "Name": "Alpha GmbH",
        "zahlungsempfaenger": "Lieferant Müller KG",
        "payee_canonical": "lieferant mueller kg",
        "antrag": 1,
        "Gruppennummer": 100,
        "Anzahl_Versionen": 1,
        "Anzahl_ungueltige_Versionen": 0,
    }
    row.update(kw)
    return row


def frame_case(name: str, rows: list[dict[str, Any]], drop: tuple[str, ...] = ()) -> dict[str, Any]:
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns and key not in drop:
                columns.append(key)
    return {
        "name": name,
        "columns": columns,
        "rows": [{k: v for k, v in row.items() if k not in drop} for row in rows],
    }


def original_test_frames() -> list[dict[str, Any]]:
    """The frames of the 26 original tests (without their assertions)."""
    r = base_row
    cases = [
        frame_case("orig-rf08-treffer", [r(bruttobetrag=40_000.0, vergabenummer="0=ni")]),
        frame_case("orig-rf08-bagatell", [r(bruttobetrag=20_000.0, vergabenummer="0")]),
        frame_case(
            "orig-rf08-personal",
            [
                r(
                    bruttobetrag=40_000.0,
                    vergabenummer="0",
                    kostenart_auswertung_bezeichnung="Personalkosten",
                )
            ],
        ),
        frame_case(
            "orig-rf08-echte-vergabe", [r(bruttobetrag=40_000.0, vergabenummer="VG-2021-4711")]
        ),
        frame_case("orig-rf08-ohne-spalte", [r(bruttobetrag=40_000.0)], drop=("vergabenummer",)),
        frame_case(
            "orig-rf10-viele-belege",
            [r(bruttobetrag=3_000.0, payee_canonical="bau ag", antrag=1, vergabenummer="VG-1")]
            * 21,
        ),
        frame_case(
            "orig-rf10-wenige-belege",
            [r(bruttobetrag=3_000.0, payee_canonical="bau ag", antrag=1, vergabenummer="VG-1")] * 5,
        ),
        frame_case(
            "orig-rf10-vier-vorhaben",
            [
                r(
                    bruttobetrag=15_000.0,
                    payee_canonical="wiederholt gmbh",
                    antrag=a,
                    Gruppennummer=500,
                    vergabenummer="VG-X",
                )
                for a in (1, 2, 3, 4)
            ],
        ),
        frame_case(
            "orig-rf10-drei-vorhaben",
            [
                r(
                    bruttobetrag=20_000.0,
                    payee_canonical="dreimal gmbh",
                    antrag=a,
                    Gruppennummer=501,
                    vergabenummer="VG-X",
                )
                for a in (1, 2, 3)
            ],
        ),
        frame_case(
            "orig-rf10-mindestvolumen",
            [
                r(
                    bruttobetrag=1_000.0,
                    payee_canonical="kleinst gmbh",
                    antrag=a,
                    Gruppennummer=502,
                    vergabenummer="VG-X",
                )
                for a in (1, 2, 3, 4)
            ],
        ),
        frame_case(
            "orig-rf10-personal",
            [
                r(
                    bruttobetrag=3_000.0,
                    payee_canonical="mitarbeiterin schmidt",
                    antrag=1,
                    kostenart_auswertung_bezeichnung="Personalkosten",
                    vergabenummer="0",
                )
            ]
            * 25,
        ),
        frame_case("orig-rf11-treffer", [r(Anzahl_Versionen=6, Anzahl_ungueltige_Versionen=4)]),
        frame_case("orig-rf11-drei", [r(Anzahl_Versionen=3, Anzahl_ungueltige_Versionen=3)]),
        frame_case("orig-rf11-anteil", [r(Anzahl_Versionen=10, Anzahl_ungueltige_Versionen=3)]),
        frame_case(
            "orig-rf11-ohne-spalten",
            [r()],
            drop=("Anzahl_Versionen", "Anzahl_ungueltige_Versionen"),
        ),
        frame_case(
            "orig-rf12-treffer",
            [
                r(bruttobetrag=10_000.0, abweichungen_betrag=0.0, antrag=1, Gruppennummer=700),
                r(bruttobetrag=10_000.0, abweichungen_betrag=3_000.0, antrag=2, Gruppennummer=700),
            ],
        ),
        frame_case(
            "orig-rf12-ein-vorhaben",
            [r(bruttobetrag=10_000.0, abweichungen_betrag=5_000.0, antrag=1, Gruppennummer=800)]
            * 3,
        ),
        frame_case(
            "orig-rf12-niedrig",
            [
                r(bruttobetrag=10_000.0, abweichungen_betrag=0.0, antrag=1, Gruppennummer=900),
                r(bruttobetrag=10_000.0, abweichungen_betrag=500.0, antrag=2, Gruppennummer=900),
            ],
        ),
        frame_case("orig-rf01", [r(bruttobetrag=5_000.0), r(bruttobetrag=5_123.0)]),
        frame_case("orig-rf02", [r(bruttobetrag=24_500.0)]),
        frame_case("orig-rf09", [r(Name="Beispiel GmbH", zahlungsempfaenger="Beispiel GmbH")]),
        frame_case("orig-codes", [r(bruttobetrag=40_000.0, vergabenummer="0")]),
        frame_case("orig-signatur", [r()]),
    ]
    summary_rows = [
        r(
            bruttobetrag=5_000.0,
            kostenart_auswertung_bezeichnung="Personal",
            Gruppennummer=10,
            antrag=10,
        ),
        r(
            bruttobetrag=24_500.0,
            kostenart_auswertung_bezeichnung="Personal",
            Gruppennummer=11,
            antrag=11,
        ),
        r(bruttobetrag=40_001.0, vergabenummer="0", Gruppennummer=12, antrag=12),
        r(
            bruttobetrag=1_234.0,
            Name="Selbst GmbH",
            zahlungsempfaenger="Selbst GmbH",
            kostenart_auswertung_bezeichnung="Personal",
            Gruppennummer=13,
            antrag=13,
        ),
        *[
            r(
                bruttobetrag=3_001.0,
                payee_canonical="bau ag",
                kostenart_auswertung_bezeichnung="Sachausgaben",
                vergabenummer="VG-2021-0815",
                antrag=20,
                Gruppennummer=20,
            )
            for _ in range(21)
        ],
        r(
            bruttobetrag=1_234.0,
            Anzahl_Versionen=8,
            Anzahl_ungueltige_Versionen=6,
            kostenart_auswertung_bezeichnung="Personal",
            Gruppennummer=30,
            antrag=30,
        ),
        r(
            bruttobetrag=10_000.0,
            abweichungen_betrag=0.0,
            kostenart_auswertung_bezeichnung="Personal",
            antrag=41,
            Gruppennummer=40,
        ),
        r(
            bruttobetrag=10_000.0,
            abweichungen_betrag=4_000.0,
            kostenart_auswertung_bezeichnung="Personal",
            antrag=42,
            Gruppennummer=40,
        ),
    ]
    cases.append(frame_case("orig-summary-alle-codes", summary_rows))
    return cases


def boundary_frames() -> list[dict[str, Any]]:
    r = base_row
    cases: list[dict[str, Any]] = []
    amounts = [
        0.0,
        -1000.0,
        1000.0,
        1000.0000001,
        999.99,
        2000.5,
        NAN,
        None,
        math.inf,
        -math.inf,
        1e6,
        3000,
        25_000.0,
        25_000.01,
        24_999.99,
    ]
    thresholds = [1_000, 5_000, 10_000, 15_000, 25_000, 50_000, 100_000, 221_000]
    for t in thresholds:
        low = 0.9 * t
        amounts += [
            low,
            math.nextafter(low, 0),
            t - 0.01,
            float(t),
            t + 1.0,
            math.nextafter(float(t), 0),
        ]
    cases.append(frame_case("rf01-rf02-betraege", [r(bruttobetrag=a) for a in amounts]))
    ids = [
        "0",
        "0=ni",
        "0 -",
        "0.",
        "0.0",
        0,
        0.0,
        "00",
        "01",
        " 0 ",
        "0abc",
        "O",
        "nan",
        "NaN",
        "None",
        None,
        NAN,
        "",
        "  ",
        "VG-1",
        815,
        12.0,
        "0\n",
        "0-17",
        "0=",
        "-0",
    ]
    kinds = [
        "Sachausgaben",
        "Personalkosten",
        "PERSONAL",
        None,
        NAN,
        "Gemeinkosten",
        "Abschreibung",
        "Pauschale",
        "Reisekosten",
        "Investition",
        "personalnebenkosten",
    ]
    rows = []
    for i, vid in enumerate(ids):
        for j, kind in enumerate(kinds):
            if (i + j) % 3 == 0:
                rows.append(
                    r(
                        bruttobetrag=25_000.01 if j % 2 else 30_000.0,
                        vergabenummer=vid,
                        kostenart_auswertung_bezeichnung=kind,
                        antrag=1000 + i,
                    )
                )
    cases.append(frame_case("rf08-kennungen-kostenarten", rows))
    cases.append(
        frame_case(
            "rf08-ohne-kostenart",
            [r(bruttobetrag=30_000.0, vergabenummer="0")],
            drop=("kostenart_auswertung_bezeichnung",),
        )
    )
    pairs = [
        ("Beispiel GmbH", "Beispiel GmbH"),
        ("Müller GmbH", "Mueller GmbH"),
        ("Holzbau Schmidt", "Holzbau Schmitt"),
        ("Stadtwerke Nord", "Nordstadtwerke"),
        ("ABC", "ABC GmbH"),
        (None, "Beispiel GmbH"),
        ("Beispiel GmbH", NAN),
        ("Planungsbüro Nord", "Planungsbüro Süd"),
        ("Werk 1", "Werk 2"),
        (12345, "12345"),
    ]
    cases.append(
        frame_case(
            "rf09-namen",
            [r(Name=a, zahlungsempfaenger=b, antrag=2000 + i) for i, (a, b) in enumerate(pairs)],
        )
    )
    overrides = [True, False, None, NAN, "False", 0, 1, "", "ja"]
    cases.append(
        frame_case(
            "rf09-pseudonym-override",
            [
                r(
                    Name="Beispiel GmbH",
                    zahlungsempfaenger="Beispiel GmbH",
                    _pseudonym_rf09=o,
                    antrag=2100 + i,
                )
                for i, o in enumerate(overrides)
            ],
        )
    )
    # RF10 pair boundaries
    for n, amount in ((20, 3_000.0), (21, 2_380.95), (21, 2_381.0), (21, 2_380.9523809523807)):
        cases.append(
            frame_case(
                f"rf10-paar-{n}-{amount}",
                [r(bruttobetrag=amount, payee_canonical="bau ag", antrag=1, vergabenummer="VG-1")]
                * n,
            )
        )
    for k, amount in ((3, 20_000.0), (4, 12_500.0), (4, 12_500.01), (5, 10_000.0)):
        cases.append(
            frame_case(
                f"rf10-gruppe-{k}-{amount}",
                [
                    r(
                        bruttobetrag=amount,
                        payee_canonical="wiederholt gmbh",
                        antrag=a,
                        Gruppennummer=500,
                        vergabenummer="VG-X",
                    )
                    for a in range(1, k + 1)
                ],
            )
        )
    cases.append(
        frame_case(
            "rf10-gruppe-nan-antrag",
            [
                r(
                    bruttobetrag=20_000.0,
                    payee_canonical="wiederholt gmbh",
                    antrag=a,
                    Gruppennummer=510,
                    vergabenummer="VG-X",
                )
                for a in (1, 2, 3, None, NAN)
            ],
        )
    )
    cases.append(
        frame_case(
            "rf10-leere-payees",
            [
                r(bruttobetrag=5_000.0, payee_canonical=p, antrag=1, vergabenummer="VG-X")
                for p in ["", " ", None, NAN, "bau ag"] * 5
            ],
        )
    )
    cases.append(
        frame_case(
            "rf10-ohne-payee-spalte",
            [r(bruttobetrag=3_000.0, antrag=1)] * 21,
            drop=("payee_canonical",),
        )
    )
    cases.append(
        frame_case(
            "rf10-ohne-gruppe",
            [r(bruttobetrag=15_000.0, payee_canonical="x gmbh", antrag=a) for a in (1, 2, 3, 4)],
            drop=("Gruppennummer",),
        )
    )
    cases.append(
        frame_case(
            "rf10-gemischt-personal",
            [
                r(
                    bruttobetrag=3_000.0,
                    payee_canonical="bau ag",
                    antrag=1,
                    vergabenummer="VG-1",
                    kostenart_auswertung_bezeichnung="Personal" if i % 2 else "Sachausgaben",
                )
                for i in range(44)
            ],
        )
    )
    # RF11
    versions = [
        (6, 4),
        (3, 3),
        (10, 3),
        (4, 2),
        (4, 3),
        (0, 0),
        (0, 5),
        ("6", "4"),
        ("x", 4),
        (None, 2),
        (8, None),
        (-4, -3),
        (4.0, 2.5),
        (" 8 ", "5"),
        (1e1, 6),
    ]
    cases.append(
        frame_case(
            "rf11-versionen",
            [
                r(Anzahl_Versionen=a, Anzahl_ungueltige_Versionen=b, antrag=3000 + i)
                for i, (a, b) in enumerate(versions)
            ],
        )
    )
    cases.append(
        frame_case(
            "rf11-nur-eine-spalte", [r(Anzahl_Versionen=8)], drop=("Anzahl_ungueltige_Versionen",)
        )
    )
    # RF12
    cases.append(
        frame_case(
            "rf12-genau-zehn-prozent",
            [
                r(bruttobetrag=10_000.0, abweichungen_betrag=0.0, antrag=1, Gruppennummer=700),
                r(bruttobetrag=10_000.0, abweichungen_betrag=1_000.0, antrag=2, Gruppennummer=700),
            ],
        )
    )
    cases.append(
        frame_case(
            "rf12-knapp-ueber",
            [
                r(bruttobetrag=10_000.0, abweichungen_betrag=0.0, antrag=1, Gruppennummer=700),
                r(bruttobetrag=10_000.0, abweichungen_betrag=1_000.01, antrag=2, Gruppennummer=700),
            ],
        )
    )
    cases.append(
        frame_case(
            "rf12-nan-antrag-in-gruppe",
            [
                r(bruttobetrag=10_000.0, abweichungen_betrag=0.0, antrag=1, Gruppennummer=710),
                r(
                    bruttobetrag=10_000.0,
                    abweichungen_betrag=5_000.0,
                    antrag=None,
                    Gruppennummer=710,
                ),
                r(bruttobetrag=10_000.0, abweichungen_betrag=0.0, antrag=2, Gruppennummer=710),
            ],
        )
    )
    cases.append(
        frame_case(
            "rf12-gleicher-antrag-andere-gruppe",
            [
                r(bruttobetrag=10_000.0, abweichungen_betrag=0.0, antrag=1, Gruppennummer=720),
                r(bruttobetrag=10_000.0, abweichungen_betrag=3_000.0, antrag=2, Gruppennummer=720),
                r(bruttobetrag=10_000.0, abweichungen_betrag=0.0, antrag=1, Gruppennummer=721),
                r(bruttobetrag=10_000.0, abweichungen_betrag=0.0, antrag=1, Gruppennummer=None),
            ],
        )
    )
    cases.append(
        frame_case(
            "rf12-strings-und-negativ",
            [
                r(bruttobetrag=10_000.0, abweichungen_betrag="3000", antrag=1, Gruppennummer=730),
                r(bruttobetrag=10_000.0, abweichungen_betrag="x", antrag=2, Gruppennummer=730),
                r(bruttobetrag=-10_000.0, abweichungen_betrag=0.0, antrag=3, Gruppennummer=731),
                r(bruttobetrag=10_000.0, abweichungen_betrag=5_000.0, antrag=4, Gruppennummer=731),
            ],
        )
    )
    cases.append(
        frame_case(
            "rf12-ohne-abweichungen",
            [r(bruttobetrag=10_000.0, antrag=a, Gruppennummer=740) for a in (1, 2)],
            drop=("abweichungen_betrag",),
        )
    )
    cases.append(frame_case("rf12-ohne-gruppe", [r(antrag=1)], drop=("Gruppennummer",)))
    # RF13-RF15
    extra: list[dict[str, Any]] = [
        {
            "auszahlungsdauer_tage": 80,
            "indikator_erreichungsquote": 0.8,
            "sanktionslisten_status": "möglicher Treffer",
        },
        {
            "auszahlungsdauer_tage": 81,
            "indikator_erreichungsquote": 0.79,
            "sanktionslisten_status": "kein Treffer",
        },
        {
            "auszahlungsdauer_tage": 80.5,
            "indikator_erreichungsquote": NAN,
            "sanktionslisten_status": "nicht geprüft",
        },
        {
            "auszahlungsdauer_tage": None,
            "indikator_erreichungsquote": None,
            "sanktionslisten_status": None,
        },
        {
            "auszahlungsdauer_tage": "90",
            "indikator_erreichungsquote": "0.5",
            "sanktionslisten_status": "Möglicher Treffer",
        },
        {
            "auszahlungsdauer_tage": "x",
            "indikator_erreichungsquote": "x",
            "sanktionslisten_status": " möglicher Treffer",
        },
        {
            "auszahlungsdauer_tage": -5,
            "indikator_erreichungsquote": -1,
            "sanktionslisten_status": NAN,
        },
    ]
    cases.append(
        frame_case("rf13-rf15-werte", [r(antrag=4000 + i, **e) for i, e in enumerate(extra)])
    )
    cases.append(frame_case("rf13-rf15-ohne-spalten", [r()]))
    return cases


def random_frames(count: int, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    names = [
        "Alpha GmbH",
        "Beta AG",
        "Gamma Bau KG",
        "Delta e.V.",
        "Epsilon Stiftung",
        "Müller Technik GmbH",
        "Stadtwerke Nord",
        None,
    ]
    payees = ["alpha", "beta bau", "gamma", "delta service", "", " ", None]
    kinds = [
        "Sachausgaben",
        "Personalkosten",
        "Investitionen",
        "Gemeinkostenpauschale",
        "Abschreibungen",
        None,
        "Fremdleistungen",
    ]
    ids = ["VG-1", "VG-2", "0", "0=ni", "", None, "0.", "V-17", 815]
    status = ["kein Treffer", "möglicher Treffer", "nicht geprüft", None]
    thresholds = [1_000, 5_000, 10_000, 15_000, 25_000, 50_000, 100_000, 221_000]
    optional = [
        "vergabenummer",
        "kostenart_auswertung_bezeichnung",
        "payee_canonical",
        "Gruppennummer",
        "Anzahl_Versionen",
        "Anzahl_ungueltige_Versionen",
        "abweichungen_betrag",
        "auszahlungsdauer_tage",
        "indikator_erreichungsquote",
        "sanktionslisten_status",
        "_pseudonym_rf09",
    ]
    cases = []
    for k in range(count):
        n = rng.randint(1, 40)
        drop = tuple(c for c in optional if rng.random() < 0.15)
        rows = []
        for _ in range(n):
            choice = rng.random()
            if choice < 0.25:
                amount: Any = float(rng.randint(1, 60) * 1000)
            elif choice < 0.45:
                t = rng.choice(thresholds)
                amount = round(t * rng.uniform(0.85, 1.02), 2)
            elif choice < 0.5:
                amount = rng.choice([None, NAN, 0.0, -500.0])
            else:
                amount = round(rng.uniform(10, 80_000), 2)
            name = rng.choice(names)
            payee_name = name if rng.random() < 0.1 else rng.choice(names)
            rows.append(
                {
                    "bruttobetrag": amount,
                    "abweichungen_betrag": rng.choice(
                        [0.0, 0.0, round(rng.uniform(0, 5000), 2), None]
                    ),
                    "vergabenummer": rng.choice(ids),
                    "kostenart_auswertung_bezeichnung": rng.choice(kinds),
                    "Name": name,
                    "zahlungsempfaenger": payee_name,
                    "payee_canonical": rng.choice(payees),
                    "antrag": rng.choice([1, 2, 3, 4, 5, 6, None]),
                    "Gruppennummer": rng.choice([10, 20, 30, None]),
                    "Anzahl_Versionen": rng.choice([1, 2, 4, 5, 8, None]),
                    "Anzahl_ungueltige_Versionen": rng.choice([0, 1, 2, 3, 5, None]),
                    "auszahlungsdauer_tage": rng.choice([10, 79, 80, 81, 120, None]),
                    "indikator_erreichungsquote": rng.choice([0.5, 0.79, 0.8, 1.0, None]),
                    "sanktionslisten_status": rng.choice(status),
                    "_pseudonym_rf09": rng.choice([True, False, None]),
                }
            )
        cases.append(frame_case(f"random-{seed}-{k:03d}", rows, drop=drop))
    return cases


def run_case(
    case: dict[str, Any], compute: Callable[..., Any], summary: Callable[..., Any]
) -> dict[str, Any]:
    df = pd.DataFrame(case["rows"], columns=case["columns"])
    result: dict[str, Any] = {
        "name": case["name"],
        "columns": case["columns"],
        "rows": encode(case["rows"]),
    }
    try:
        out = compute(df)
    except Exception as exc:  # noqa: BLE001 - record the original failure
        result["exception"] = {"type": type(exc).__name__, "message": str(exc)}
        return result
    result["exception"] = None
    result["flags"] = {c: [bool(v) for v in out[c].tolist()] for c in FLAG_COLUMNS}
    result["name_match"] = encode([float(v) for v in out["name_match"].tolist()])
    result["red_flag_codes"] = [list(v) for v in out["red_flag_codes"].tolist()]
    result["summary"] = encode(summary(out))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--random", type=int, default=120)
    parser.add_argument("--seed", type=int, default=20260923)
    args = parser.parse_args()
    checkout = args.checkout.resolve()
    head = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if head != COMMIT:
        raise SystemExit(f"checkout is at {head}, expected {COMMIT}")
    for path, blob in FILES.items():
        if git_blob((checkout / path).read_bytes()) != blob:
            raise SystemExit(f"{path} does not match the pinned blob")
    sys.path.insert(0, str(checkout / "backend"))
    module = importlib.import_module("app.pipeline.red_flags")
    if Path(str(module.__file__)).resolve() != checkout / "backend/app/pipeline/red_flags.py":
        raise SystemExit("imported red_flags from an unexpected location")
    near = [
        0.0,
        -1.0,
        NAN,
        math.inf,
        899.99,
        900.0,
        999.99,
        1000.0,
        4500.0,
        13_499.99,
        13_500.0,
        198_899.99,
        198_900.0,
        220_999.99,
        221_000.0,
        300_000.0,
    ]
    ids = ["0", "0=ni", "0 -", "0.", "", None, "nan", "VG-2021-0815", "0.0", 0, " 0 ", "00"]
    cases = [
        run_case(c, module.compute_red_flags, module.red_flag_summary)
        for c in original_test_frames() + boundary_frames() + random_frames(args.random, args.seed)
    ]
    document = {
        "source": {
            "repository": REPOSITORY,
            "commit": COMMIT,
            "files": FILES,
            "symbols": [
                "compute_red_flags",
                "_near_threshold",
                "red_flag_summary",
                "_hat_echte_vergabe",
                "_name_match",
                "_compute_rf10",
                "_compute_rf11",
                "_compute_rf12",
                "VERGABE_SCHWELLEN",
                "_PROXIMITY",
                "RF08_BAGATELLGRENZE",
                "_PLATZHALTER_VERGABE",
                "_NICHT_VERGABERELEVANT",
                "RED_FLAG_LABELS",
                "RED_FLAG_CODES",
            ],
        },
        "environment": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "rapidfuzz": rapidfuzz.__version__,
        },
        "constants": {
            "VERGABE_SCHWELLEN": module.VERGABE_SCHWELLEN,
            "_PROXIMITY": module._PROXIMITY,
            "RF08_BAGATELLGRENZE": module.RF08_BAGATELLGRENZE,
            "_PLATZHALTER_VERGABE": module._PLATZHALTER_VERGABE.pattern,
            "_NICHT_VERGABERELEVANT": module._NICHT_VERGABERELEVANT.pattern,
            "_NICHT_VERGABERELEVANT_flags": int(module._NICHT_VERGABERELEVANT.flags),
            "RED_FLAG_LABELS": module.RED_FLAG_LABELS,
            "RED_FLAG_CODES": module.RED_FLAG_CODES,
        },
        "near_threshold": [
            {"input": encode(a), "output": bool(module._near_threshold(a))} for a in near
        ],
        "hat_echte_vergabe": {
            "input": encode(ids),
            "output": [bool(v) for v in module._hat_echte_vergabe(pd.Series(ids)).tolist()],
        },
        "cases": cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n")
    failed = sum(1 for c in cases if c["exception"])
    print(f"{len(cases)} frame cases ({failed} with original exception) written to {args.output}")


if __name__ == "__main__":
    main()
