"""Originalverhalten der Geofunktionen tatsächlich ausführen und als Fixture festhalten.

Die Quelldateien werden auf den festgehaltenen Commits über ihren Git-Blob
geprüft. Module ohne Fremdabhängigkeiten (osint) werden unverändert geladen;
aus Anwendungsmodulen mit Datenbank-/Webabhängigkeiten (audit_designer,
flowsearch) werden nur die benötigten, unveränderten Definitionen per AST
übernommen und ausgeführt; ``flowworkshop`` wird mit Stellvertretern für
Konfiguration, Datenbank und ``requests`` geladen. Netz, Datenbank und
``auditcore_geo`` werden nie verwendet. Referenzwerte stammen – nur zum
Vergleich, nicht als Abhängigkeit – aus pyproj/PROJ und shapely.

    python tools/capture_legacy.py <Quellen-Verzeichnis> tests/fixtures/legacy_observed.json

Das Quellen-Verzeichnis enthält die Klone ``osint``, ``audit_designer``,
``flowsearch`` und ``flowworkshop`` auf den unten genannten Commits.
"""

from __future__ import annotations

import argparse
import ast
import functools
import hashlib
import importlib.util
import json
import math
import platform
import random
import struct
import sys
import tempfile
import types
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pyproj
import shapely
import shapely.ops as sops
from shapely.geometry import Point as SPoint
from shapely.geometry import shape

SOURCES: dict[str, dict[str, Any]] = {
    "osint": {
        "repository": "janpow77/osint",
        "commit": "d361ddb9a502bb899065e799d50104f306cfdc89",
        "files": {
            "dienst": ("ortsdienst/dienst.py", "d9e06518385971a45a82a6d796f8dc1356b4e727"),
            "bundeslaender": (
                "werkzeuge/bundeslaender_holen.py",
                "4df5560ac0930c81c5f7397d2236a3190757db42",
            ),
            "betroffenheit": (
                "werkzeuge/betroffenheit.py",
                "2b7a1f63e784e044c3029827eb5a356e6f9b01ef",
            ),
            "verorten": (
                "werkzeuge/vorhaben_verorten.py",
                "1b6057a7555c8a0532b89b3b094ddcd7a3cb5536",
            ),
        },
    },
    "audit_designer": {
        "repository": "janpow77/audit_designer",
        "commit": "1254591156d3bdf6ccdf4050dec7713a61ad4a20",
        "files": {
            "gis": (
                "backend/app/api/vpai_notebook/gis/_common.py",
                "54b4f41c35fc51c4d3b1dbf2c84071fdc915270a",
            ),
            "register": (
                "backend/app/core/shared/research/register/geocoding.py",
                "12056f39a1f6644db5f086410a3028e4a91fd529",
            ),
            "company": (
                "backend/app/modules/vp_ai/services/company/company_records.py",
                "874901d0414976bbc3f9f9314894c7cf913c043a",
            ),
        },
    },
    "flowsearch": {
        "repository": "janpow77/flowsearch",
        "commit": "10cb2a3ead3892cbf9fa94f2ed18763187d3e0e4",
        "files": {
            "api": (
                "backend/app/api/eu_beneficiaries.py",
                "b45c67919253c92519989a2842578f2b6fa695f6",
            ),
            "natura": (
                "backend/app/services/natura2000_service.py",
                "33f83f6748eb30fcf9775c159e06c99b7263504f",
            ),
        },
    },
    "flowworkshop": {
        "repository": "janpow77/flowworkshop",
        "commit": "3d1cb40221645935c323392d70d84102d05ac7bb",
        "files": {
            "geocoding": (
                "auditworkshop/backend/services/geocoding_service.py",
                "3c6ac686be9bc222749fc06b7271ef94c44c2cc3",
            ),
            "country_profiles": (
                "auditworkshop/backend/services/country_profiles.py",
                "80b7d05a41e6851036dff7d86a2680341a85a419",
            ),
        },
    },
}


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def pinned(root: Path, repo: str, key: str) -> Path:
    rel, blob = SOURCES[repo]["files"][key]
    path = root / repo / rel
    if git_blob(path.read_bytes()) != blob:
        raise SystemExit(f"{path} entspricht nicht dem festgehaltenen Blob {blob}")
    return path


def import_file(path: Path, name: str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extract(
    path: Path,
    names: list[str],
    namespace: dict[str, Any],
    methods: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Unveränderte Top-Level-Definitionen (und Methoden als Funktionen) ausführen."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    wanted: list[ast.stmt] = []
    found: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names:
            wanted.append(node)
            found.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            ids = {t.id for t in targets if isinstance(t, ast.Name)}
            if ids & set(names):
                wanted.append(node)
                found |= ids & set(names)
        elif isinstance(node, ast.ClassDef) and methods and node.name in methods:
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                    item.name in methods[node.name]
                ):
                    item.decorator_list = []
                    wanted.append(item)
                    found.add(item.name)
    expected = set(names) | {m for ms in (methods or {}).values() for m in ms}
    if expected - found:
        raise SystemExit(f"{path}: Definitionen fehlen {sorted(expected - found)}")
    module = ast.Module(body=wanted, type_ignores=[])
    name = "legacy_" + hashlib.sha1(str(path).encode()).hexdigest()[:8]
    modul = types.ModuleType(name)
    modul.__dict__.update(namespace)
    sys.modules[name] = modul  # dataclasses lösen Annotationen über das Modul auf
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), modul.__dict__)  # noqa: S102
    return modul.__dict__


def observe(call: Callable[[], Any]) -> dict[str, Any]:
    try:
        return {"ok": jsonable(call())}
    except Exception as exc:  # noqa: BLE001 - Fehler sind beobachtetes Verhalten
        return {"error": type(exc).__name__, "message": str(exc)[:200]}


def jsonable(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return {"float": repr(value)}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    return value


# ───────────────────────────────────────────────────────── Eingaben

DISTANZ_PAARE: list[list[float]] = [
    [50.0, 8.0, 50.0, 8.0],
    [50.0, 8.0, 51.0, 8.0],
    [50.1106, 8.6821, 52.52, 13.405],
    [50.0782, 8.2398, 50.1109, 8.6821],
    [0.0, 179.9, 0.0, -179.9],
    [89.9, 0.0, 89.9, 180.0],
    [-89.9, 10.0, -89.9, -170.0],
    [0.0, 0.0, 0.0, 180.0],
    [10.0, 20.0, -10.0, -160.0],
    [0.0, 0.0, 1e-9, 0.0],
    [47.27, 5.87, 55.06, 15.04],
    [50.0, 8.0, 50.0, 8.000001],
    [45.0, 45.0, -45.0, -135.0],
    [33.3, 12.7, -33.3, -167.3],
    [-0.5, 0.1, 0.5, -179.9],
]
_rng = random.Random(20260923)
for _ in range(24):
    DISTANZ_PAARE.append(
        [
            round(_rng.uniform(47.0, 55.5), 6),
            round(_rng.uniform(5.5, 15.5), 6),
            round(_rng.uniform(47.0, 55.5), 6),
            round(_rng.uniform(5.5, 15.5), 6),
        ]
    )
for _ in range(8):
    DISTANZ_PAARE.append(
        [
            round(_rng.uniform(-90, 90), 6),
            round(_rng.uniform(-180, 180), 6),
            round(_rng.uniform(-90, 90), 6),
            round(_rng.uniform(-180, 180), 6),
        ]
    )

QUADRAT = [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]]
LOCH = [[4.0, 4.0], [6.0, 4.0], [6.0, 6.0], [4.0, 6.0], [4.0, 4.0]]
ZWEITES = [[20.0, 0.0], [30.0, 0.0], [30.0, 10.0], [20.0, 10.0], [20.0, 0.0]]
KONKAV = [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [5.0, 3.0], [0.0, 10.0], [0.0, 0.0]]
GEOMETRIEN: dict[str, dict[str, Any]] = {
    "quadrat": {"type": "Polygon", "coordinates": [QUADRAT]},
    "quadrat_mit_loch": {"type": "Polygon", "coordinates": [QUADRAT, LOCH]},
    "zwei_quadrate": {"type": "MultiPolygon", "coordinates": [[QUADRAT], [ZWEITES]]},
    "zwei_quadrate_loch": {"type": "MultiPolygon", "coordinates": [[QUADRAT, LOCH], [ZWEITES]]},
    "konkav": {"type": "Polygon", "coordinates": [KONKAV]},
}
LAGE_PUNKTE: list[list[float]] = [
    [5.0, 5.0],
    [2.0, 2.0],
    [5.0, 8.0],
    [15.0, 5.0],
    [25.0, 5.0],
    [5.0, 5.5],
    [-1.0, 5.0],
    [0.0, 5.0],
    [10.0, 5.0],
    [5.0, 0.0],
    [5.0, 10.0],
    [0.0, 0.0],
    [10.0, 0.0],
    [10.0, 10.0],
    [0.0, 10.0],
    [4.0, 5.0],
    [6.0, 5.0],
    [5.0, 4.0],
    [5.0, 6.0],
    [20.0, 5.0],
    [30.0, 5.0],
    [5.0, 3.0],
    [5.0, 2.9],
    [5.0, 3.1],
    [2.5, 5.0],
]


def frankfurt_flaeche() -> dict[str, Any]:
    """Synthetisches Schutzgebiet bei Frankfurt (0,02° × 0,01°) mit Loch."""
    aussen = [[8.66, 50.10], [8.68, 50.10], [8.68, 50.11], [8.66, 50.11], [8.66, 50.10]]
    loch = [[8.668, 50.103], [8.672, 50.103], [8.672, 50.107], [8.668, 50.107], [8.668, 50.103]]
    zweit = [[8.70, 50.10], [8.71, 50.10], [8.71, 50.105], [8.70, 50.105], [8.70, 50.10]]
    return {"type": "MultiPolygon", "coordinates": [[aussen, loch], [zweit]]}


ABSTAND_PUNKTE = [
    [8.67, 50.105],
    [8.65, 50.105],
    [8.67, 50.12],
    [8.705, 50.1025],
    [8.69, 50.102],
    [8.670, 50.105],
    [8.60, 50.00],
    [8.72, 50.105],
]

UTM_PUNKTE: list[list[float]] = [
    [500000.0, 5500000.0],
    [280000.0, 5230000.0],
    [920000.0, 6110000.0],
    [477000.0, 5550000.0],
    [691000.0, 5335000.0],
    [300000.0, 6000000.0],
    [166021.4431, 0.0],
    [833978.5569, 9000000.0],
    [500000.0, 0.0],
]
for _ in range(20):
    UTM_PUNKTE.append(
        [round(_rng.uniform(280000, 920000), 3), round(_rng.uniform(5230000, 6110000), 3)]
    )


def wkb_polygon(bo: str, ringe: list[list[tuple[float, float]]], typ: int = 3) -> bytes:
    kennung = b"\x01" if bo == "<" else b"\x00"
    teile = [kennung, struct.pack(bo + "I", typ), struct.pack(bo + "I", len(ringe))]
    for ring in ringe:
        teile.append(struct.pack(bo + "I", len(ring)))
        for x, y in ring:
            teile.append(struct.pack(bo + "dd", x, y))
    return b"".join(teile)


def gpkg(wkb: bytes, *, envelope: int = 0, flags_extra: int = 0, srs: int = 25832) -> bytes:
    groesse = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}.get(envelope, 0)
    flags = 1 | (envelope << 1) | flags_extra
    return b"GP\x00" + bytes([flags]) + struct.pack("<i", srs) + b"\x00" * groesse + wkb


RING_UTM = [
    (470000.0, 5540000.0),
    (480000.0, 5540000.0),
    (480000.0, 5550000.0),
    (470000.0, 5550000.0),
    (470000.0, 5540000.0),
]
LOCH_UTM = [
    (474000.0, 5544000.0),
    (476000.0, 5544000.0),
    (476000.0, 5546000.0),
    (474000.0, 5546000.0),
    (474000.0, 5544000.0),
]


def wkb_faelle() -> dict[str, bytes]:
    poly_le = wkb_polygon("<", [RING_UTM, LOCH_UTM])
    poly_be = wkb_polygon(">", [RING_UTM])
    multi = b"\x01" + struct.pack("<II", 6, 2) + poly_le + wkb_polygon(">", [RING_UTM])
    multi_fremd = b"\x01" + struct.pack("<II", 6, 1) + b"\x01" + struct.pack("<Idd", 1, 1.0, 2.0)
    iso_z = (
        b"\x01"
        + struct.pack("<II", 1003, 1)
        + struct.pack("<I", 4)
        + b"".join(struct.pack("<ddd", x, y, 100.0) for x, y in RING_UTM[:4])
    )
    ewkb_z = (
        b"\x01"
        + struct.pack("<II", 0x80000003, 1)
        + struct.pack("<I", 4)
        + b"".join(struct.pack("<ddd", x, y, 100.0) for x, y in RING_UTM[:4])
    )
    return {
        "polygon_le_ohne_huelle": gpkg(poly_le),
        "polygon_be_huelle_1": gpkg(poly_be, envelope=1),
        "polygon_le_huelle_2": gpkg(poly_le, envelope=2),
        "polygon_le_huelle_3": gpkg(poly_le, envelope=3),
        "polygon_le_huelle_4": gpkg(poly_le, envelope=4),
        "multipolygon_gemischt": gpkg(multi, srs=4258),
        "multipolygon_mit_punkt": gpkg(multi_fremd),
        "iso_z_polygon": gpkg(iso_z),
        "ewkb_z_polygon": gpkg(ewkb_z),
        "leer_flag": gpkg(poly_le, flags_extra=0b10000),
        "abgeschnitten": gpkg(poly_le)[:-9],
        "restbytes": gpkg(poly_le) + b"\x00\x01",
        "kein_gpkg": b"XX" + gpkg(poly_le)[2:],
        "huelle_5": gpkg(poly_le, envelope=5),
        "punkt": gpkg(b"\x01" + struct.pack("<Idd", 1, 1.0, 2.0)),
    }


def dp_linien() -> dict[str, list[tuple[float, float]]]:
    rng = random.Random(7)
    x = y = 0.0
    wanderung = []
    for _ in range(300):
        x += rng.uniform(0, 0.01)
        y += rng.uniform(-0.01, 0.01)
        wanderung.append((round(x, 6), round(y, 6)))
    kreis = [
        (
            round(8.5 + 0.1 * math.cos(2 * math.pi * i / 64), 6),
            round(50.0 + 0.07 * math.sin(2 * math.pi * i / 64), 6),
        )
        for i in range(64)
    ]
    kreis.append(kreis[0])
    return {
        "zwei_punkte": [(0.0, 0.0), (1.0, 1.0)],
        "gerade": [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)],
        "zacke": [(0.0, 0.0), (1.0, 0.5), (2.0, -0.5), (3.0, 0.0)],
        "gleiche_enden": [(0.0, 0.0), (1.0, 1.0), (2.0, 0.0), (0.0, 0.0)],
        "wanderung": wanderung,
        "kreis": kreis,
    }


# ─────────────────────────────────────────────────────── Aufzeichnung


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    root = args.sources.resolve()
    for repo in SOURCES:
        if not (root / repo / ".git").exists():
            raise SystemExit(f"Klon fehlt: {root / repo}")

    dienst = import_file(pinned(root, "osint", "dienst"), "osint_dienst")
    bl = import_file(pinned(root, "osint", "bundeslaender"), "osint_bundeslaender")
    betr = import_file(pinned(root, "osint", "betroffenheit"), "osint_betroffenheit")

    gis = extract(
        pinned(root, "audit_designer", "gis"),
        [
            "_iter_ring_coordinates",
            "_point_in_ring",
            "_point_in_geometry",
            "_geometry_centroid",
            "_haversine_distance_m",
            "_point_segment_distance_m",
            "_geometry_edge_distance_m",
        ],
        {"math": math, "Any": Any},
    )
    register = extract(
        pinned(root, "audit_designer", "register"),
        [
            "_entfernung_km",
            "NutsGebiet",
            "_punkt_in_ring",
            "_punkt_in_gebiet",
            "FLAECHEN_TOLERANZ_KM",
            "naechste_nuts3",
        ],
        {"math": math, "dataclass": dataclass, "lru_cache": functools.lru_cache},
    )
    company = extract(
        pinned(root, "audit_designer", "company"),
        [],
        {"math": math},
        methods={"_NaturaClient": ["_haversine_m", "_distance_to_geometry_m"]},
    )
    fs_api = extract(pinned(root, "flowsearch", "api"), ["calculate_distance"], {"math": math})
    fs_natura = extract(
        pinned(root, "flowsearch", "natura"),
        [],
        {
            "radians": math.radians,
            "sin": math.sin,
            "cos": math.cos,
            "asin": math.asin,
            "sqrt": math.sqrt,
            "Dict": dict,
            "Any": Any,
        },
        methods={"Natura2000Service": ["_calculate_distance", "_get_geometry_center"]},
    )

    class _Selbst:
        @staticmethod
        def _haversine_m(*a: float) -> float:
            return float(company["_haversine_m"](*a))

    faelle: dict[str, Any] = {}

    # Entfernungen
    geod = pyproj.Geod(ellps="WGS84")
    distanz = []
    varianten: dict[str, Callable[[float, float, float, float], Any]] = {
        "osint_haversine_km": dienst.haversine_km,
        "designer_gis_haversine_m": lambda a, b, c, d: gis["_haversine_distance_m"](b, a, d, c),
        "designer_register_entfernung_km": register["_entfernung_km"],
        "designer_company_haversine_m": company["_haversine_m"],
        "flowsearch_calculate_distance_km": fs_api["calculate_distance"],
        "flowsearch_natura_distance_m": lambda a, b, c, d: fs_natura["_calculate_distance"](
            None, a, b, c, d
        ),
    }
    for paar in DISTANZ_PAARE:
        lat1, lon1, lat2, lon2 = paar
        distanz.append(
            {
                "eingabe": paar,
                **{name: observe(functools.partial(f, *paar)) for name, f in varianten.items()},
                "referenz_wgs84_ellipsoid_m": geod.inv(lon1, lat1, lon2, lat2)[2],
            }
        )
    faelle["distanz"] = distanz

    # Umkreis (Ortsdienst)
    def bestand(punkte: list[list[float]]) -> Any:
        feats = [
            {
                "geometry": {"type": "Point", "coordinates": [lo, la]},
                "properties": {"id": str(i), "name": f"P{i}"},
            }
            for i, (la, lo) in enumerate(punkte)
        ]
        return dienst.Bestand.aus_features({"EFRE": feats})

    grenze_km = dienst.haversine_km(50.0, 8.0, 50.03, 8.04)
    phi = math.radians(60.0)
    theta = 1000.0 / dienst.ERDRADIUS_KM
    lat_max_lon = math.degrees(math.asin(math.sin(phi) / math.cos(theta)))
    dlon_max = math.degrees(math.asin(math.sin(theta) / math.cos(phi)))
    umkreis_faelle = [
        {
            "name": "frankfurt_5km",
            "zentrum": [50.1106, 8.6821],
            "km": 5.0,
            "punkte": [
                [50.1106, 8.6821],
                [50.14, 8.68],
                [50.2, 8.7],
                [50.1106, 8.75],
                [50.08, 8.66],
            ],
        },
        {
            "name": "grenze_genau",
            "zentrum": [50.0, 8.0],
            "km": grenze_km,
            "punkte": [[50.03, 8.04], [50.0301, 8.04]],
        },
        {
            "name": "alle_ohne_radius",
            "zentrum": [50.0, 8.0],
            "km": None,
            "punkte": [[51.0, 9.0], [50.0, 8.0], [49.0, 7.0]],
        },
        {
            "name": "hohe_breite_grosser_radius",
            "zentrum": [60.0, 10.0],
            "km": 1000.0,
            "punkte": [[round(lat_max_lon, 6), round(10.0 + dlon_max * 0.995, 6)], [60.0, 11.0]],
        },
        {
            "name": "datumsgrenze",
            "zentrum": [0.0, 179.9],
            "km": 50.0,
            "punkte": [[0.0, -179.95], [0.0, 179.8]],
        },
    ]
    for fall in umkreis_faelle:
        b = bestand(fall["punkte"])
        z = fall["zentrum"]
        fall["ergebnis"] = observe(lambda b=b, z=z, fall=fall: b.umkreis(z[0], z[1], fall["km"]))
        fall["abstaende_km"] = [
            dienst.haversine_km(z[0], z[1], la, lo) for la, lo in fall["punkte"]
        ]
    faelle["umkreis"] = umkreis_faelle

    # Punkt in Fläche
    lage = []
    for name, geom in GEOMETRIEN.items():
        s = shape(geom)
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        gebiet = register["NutsGebiet"](
            code="X",
            name=name,
            ringe=tuple(
                tuple(tuple((float(p[0]), float(p[1])) for p in r) for r in poly) for poly in polys
            ),
            min_lat=-90.0,
            min_lon=-180.0,
            max_lat=90.0,
            max_lon=180.0,
        )
        for lon, lat in LAGE_PUNKTE:
            p = SPoint(lon, lat)
            lage.append(
                {
                    "geometrie": name,
                    "punkt_lonlat": [lon, lat],
                    "designer_gis_point_in_geometry": observe(
                        lambda lon=lon, lat=lat, geom=geom: gis["_point_in_geometry"](
                            lon, lat, geom
                        )
                    ),
                    "designer_register_punkt_in_gebiet": observe(
                        lambda lon=lon, lat=lat, g=gebiet: register["_punkt_in_gebiet"](lat, lon, g)
                    ),
                    "osint_im_ring_aussenring": observe(
                        lambda lon=lon, lat=lat, polys=polys: betr._im_ring(
                            lon, lat, [tuple(q) for q in polys[0][0]]
                        )
                    ),
                    "referenz_shapely": "rand"
                    if s.boundary.distance(p) == 0
                    else ("innen" if s.contains(p) else "aussen"),
                }
            )
    faelle["lage"] = lage

    # Rand-/Stützpunktabstände, Schwerpunkte
    ff = frankfurt_flaeche()
    transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)
    ff_utm = sops.transform(transformer.transform, shape(ff))
    polys = ff["coordinates"]
    gebiet = register["NutsGebiet"](
        code="DEX",
        name="ff",
        ringe=tuple(
            tuple(tuple((float(p[0]), float(p[1])) for p in r) for r in poly) for poly in polys
        ),
        min_lat=50.10,
        min_lon=8.66,
        max_lat=50.11,
        max_lon=8.71,
    )
    register["_nuts_gebiete"] = lambda: {"DE": (gebiet,)}
    abstand = []
    for lon, lat in ABSTAND_PUNKTE:
        register["naechste_nuts3"].cache_clear()
        px, py = transformer.transform(lon, lat)
        abstand.append(
            {
                "punkt_lonlat": [lon, lat],
                "designer_gis_edge_distance_m": observe(
                    lambda lon=lon, lat=lat: gis["_geometry_edge_distance_m"](lon, lat, ff)
                ),
                "designer_company_distance_to_geometry_m": observe(
                    lambda lon=lon, lat=lat: company["_distance_to_geometry_m"](
                        _Selbst(), lat, lon, ff
                    )
                ),
                "designer_register_naechste_nuts3": observe(
                    lambda lon=lon, lat=lat: register["naechste_nuts3"](lat, lon, "DE")
                ),
                "referenz_utm32_rand_m": ff_utm.boundary.distance(SPoint(px, py)),
                "referenz_utm32_innen": ff_utm.contains(SPoint(px, py)),
            }
        )
    faelle["abstand"] = abstand
    ungueltig = [
        None,
        {},
        {"type": "Polygon", "coordinates": []},
        {"type": "Point", "coordinates": [8.0, 50.0]},
        {"type": "GeometryCollection", "geometries": []},
    ]
    faelle["abstand_ungueltig"] = [
        {
            "geometrie": g,
            "designer_company_distance_to_geometry_m": observe(
                lambda g=g: company["_distance_to_geometry_m"](_Selbst(), 50.0, 8.0, g)
            ),
            "designer_gis_edge_distance_m": observe(
                lambda g=g: gis["_geometry_edge_distance_m"](8.0, 50.0, g or {})
            ),
        }
        for g in ungueltig
    ]
    schwerpunkt = []
    for name, geom in {
        **GEOMETRIEN,
        "frankfurt": ff,
        "punkt": {"type": "Point", "coordinates": [8.0, 50.0]},
        "linie": {"type": "LineString", "coordinates": [[8.0, 50.0], [9.0, 51.0]]},
    }.items():
        c = shape(geom).centroid
        schwerpunkt.append(
            {
                "geometrie": name,
                "flowsearch_get_geometry_center": observe(
                    lambda geom=geom: fs_natura["_get_geometry_center"](None, geom)
                ),
                "designer_gis_geometry_centroid": observe(
                    lambda geom=geom: gis["_geometry_centroid"](geom)
                ),
                "referenz_shapely_schwerpunkt": [c.x, c.y],
            }
        )
    faelle["schwerpunkt"] = schwerpunkt

    # Achsenfolge
    achsen = {
        "lonlat_de": [[(8.6, 50.1), (8.7, 50.2), (8.6, 50.2)]],
        "latlon_de": [[(50.1, 8.6), (50.2, 8.7), (50.2, 8.6)]],
        "ausserhalb": [[(2.35, 48.85), (2.4, 48.9), (2.3, 48.9)]],
        "gemischt_zuerst_latlon": [[(50.1, 8.6)], [(8.6, 50.1), (8.7, 50.2)]],
        "leer": [],
        "vierter_ring_erst": [[(0.0, 0.0)], [(1.0, 1.0)], [(2.0, 2.0)], [(50.1, 8.6)]],
    }
    faelle["achsenfolge"] = [
        {"name": n, "ringe": r, "osint_achsen_drehen": observe(lambda r=r: betr._achsen_drehen(r))}
        for n, r in achsen.items()
    ]

    # UTM 32N → geographisch
    utm_ref = pyproj.Transformer.from_crs("EPSG:25832", "EPSG:4258", always_xy=True)
    faelle["utm"] = [
        {
            "eingabe": [e, n],
            "osint_utm_nach_wgs84": observe(lambda e=e, n=n: bl.utm_nach_wgs84(e, n)),
            "referenz_proj_lonlat": list(utm_ref.transform(e, n)),
        }
        for e, n in UTM_PUNKTE
    ]

    # GeoPackage/WKB
    faelle["wkb"] = [
        {
            "name": n,
            "blob_hex": blob.hex(),
            "osint_wkb_polygone": observe(lambda blob=blob: bl.wkb_polygone(blob)),
        }
        for n, blob in wkb_faelle().items()
    ]

    # Douglas-Peucker
    dp = []
    for name, linie in dp_linien().items():
        for tol in (0.0, 0.0025, 0.05, 1.0, -1.0):
            dp.append(
                {
                    "linie": name,
                    "punkte": linie,
                    "toleranz": tol,
                    "osint_douglas_peucker": observe(
                        lambda linie=linie, tol=tol: bl.douglas_peucker(linie, tol)
                    ),
                    "osint_ring_vereinfachen": observe(
                        lambda linie=linie, tol=tol: bl.ring_vereinfachen(linie, tol)
                    ),
                }
            )
    faelle["douglas_peucker"] = dp

    faelle["nominatim"] = nominatim_faelle(root)

    ergebnis = {
        "schema": "auditcore_geo.legacy_observed/1",
        "sources": {
            k: {
                "repository": v["repository"],
                "commit": v["commit"],
                "files": {n: {"path": p, "git_blob": b} for n, (p, b) in v["files"].items()},
            }
            for k, v in SOURCES.items()
        },
        "environment": {
            "python": platform.python_version(),
            "pyproj": pyproj.__version__,
            "proj": pyproj.proj_version_str,
            "shapely": shapely.__version__,
        },
        "inputs": {
            "geometrien": {
                **GEOMETRIEN,
                "frankfurt": frankfurt_flaeche(),
                "punkt": {"type": "Point", "coordinates": [8.0, 50.0]},
                "linie": {"type": "LineString", "coordinates": [[8.0, 50.0], [9.0, 51.0]]},
            }
        },
        "cases": faelle,
    }
    ergebnis["case_count"] = sum(len(v) for v in faelle.values())
    args.output.write_text(
        json.dumps(ergebnis, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(json.dumps({"cases": ergebnis["case_count"], **{k: len(v) for k, v in faelle.items()}}))
    return 0


# ───────────────────────────────────────────── Nominatim-Anfragebildung

ANTWORT = [
    {
        "place_id": 1,
        "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
        "osm_type": "way",
        "osm_id": 42,
        "lat": "50.1000000",
        "lon": "8.6000000",
        "category": "building",
        "type": "yes",
        "place_rank": 30,
        "importance": 0.1,
        "addresstype": "building",
        "name": "",
        "display_name": "Beispielweg 1, 60000 Beispielstadt, Deutschland",
        "boundingbox": ["50.0999", "50.1001", "8.5999", "8.6001"],
    }
]


def nominatim_faelle(root: Path) -> list[dict[str, Any]]:
    """Anfragebildung und Antwortauswertung der drei Aufrufer mit Stellvertretern statt Netz."""
    faelle: list[dict[str, Any]] = []

    # osint: urllib.request.urlopen
    aufrufe: list[dict[str, Any]] = []

    class _Antwort:
        def __init__(self, daten: Any) -> None:
            self.daten = json.dumps(daten).encode()

        def __enter__(self) -> Any:
            import io

            return io.BytesIO(self.daten)

        def __exit__(self, *a: Any) -> None:
            return None

    antworten: list[Any] = []

    def urlopen(anfrage: Any, timeout: float) -> Any:
        from urllib.parse import parse_qsl, urlsplit

        teile = urlsplit(anfrage.full_url)
        aufrufe.append(
            {
                "url": f"{teile.scheme}://{teile.netloc}{teile.path}",
                "params": dict(parse_qsl(teile.query)),
                "headers": dict(anfrage.header_items()),
                "timeout": timeout,
            }
        )
        a = antworten.pop(0)
        if isinstance(a, Exception):
            raise a
        return _Antwort(a)

    import urllib.parse
    import urllib.request

    fake_request = types.SimpleNamespace(Request=urllib.request.Request, urlopen=urlopen)
    fake_urllib = types.SimpleNamespace(parse=urllib.parse, request=fake_request)
    ns = extract(
        pinned(root, "osint", "verorten"),
        ["KENNUNG", "NOMINATIM", "PAUSE", "adresse_aufbereiten", "abfragen"],
        {"json": json, "re": __import__("re"), "urllib": fake_urllib},
    )
    for roh, antwort in (
        ("63477 Maintal / Am Kreuzstein 85", ANTWORT),
        ("Beispielstadt", []),
        ("Fehlerstadt", OSError("Netz weg")),
    ):
        aufrufe.clear()
        antworten[:] = [antwort]
        adresse = ns["adresse_aufbereiten"](roh)
        faelle.append(
            {
                "aufrufer": "osint.vorhaben_verorten.abfragen",
                "eingabe": roh,
                "adresse": adresse,
                "ergebnis": observe(lambda a=adresse: ns["abfragen"](a)),
                "anfragen": list(aufrufe),
                "pause_s": ns["PAUSE"],
            }
        )

    # audit_designer: httpx.Client
    class HTTPException(Exception):  # noqa: N818 - Name des Originals
        def __init__(self, status_code: int, detail: str) -> None:
            super().__init__(f"{status_code}: {detail}")

    class HTTPError(Exception):
        pass

    d_aufrufe: list[dict[str, Any]] = []
    d_antwort: list[Any] = []

    class _Resp:
        def __init__(self, daten: Any) -> None:
            self.daten = daten

        def raise_for_status(self) -> None:
            return None

        def json(self) -> Any:
            return self.daten

    class _Client:
        def __init__(self, timeout: float, headers: dict[str, str]) -> None:
            self.timeout, self.headers = timeout, headers

        def __enter__(self) -> Any:
            return self

        def __exit__(self, *a: Any) -> None:
            return None

        def get(self, url: str, params: dict[str, Any]) -> Any:
            d_aufrufe.append(
                {
                    "url": url,
                    "params": {k: str(v) for k, v in params.items()},
                    "headers": self.headers,
                    "timeout": self.timeout,
                }
            )
            a = d_antwort.pop(0)
            if isinstance(a, Exception):
                raise a
            return _Resp(a)

    fake_httpx = types.SimpleNamespace(Client=_Client, HTTPError=HTTPError)
    dns = extract(
        pinned(root, "audit_designer", "gis"),
        ["_geocode_address"],
        {"httpx": fake_httpx, "HTTPException": HTTPException},
    )
    highway = [dict(ANTWORT[0], **{"class": "highway"})]
    for eingabe, antwort in (
        ("Beispielweg 1, Beispielstadt", ANTWORT),
        ("Beispielweg", highway),
        ("Nirgendwo", []),
        ("Fehler", HTTPError("Netz weg")),
        ("  ", ANTWORT),
    ):
        d_aufrufe.clear()
        d_antwort[:] = [antwort]
        faelle.append(
            {
                "aufrufer": "audit_designer.gis._geocode_address",
                "eingabe": eingabe,
                "ergebnis": observe(lambda e=eingabe: dns["_geocode_address"](e)),
                "anfragen": list(d_aufrufe),
                "pause_s": None,
            }
        )

    # flowworkshop: geocode_single mit Stellvertretern
    w_aufrufe: list[dict[str, Any]] = []
    w_antwort: list[Any] = []
    schlaf: list[float] = []

    class _WResp:
        def __init__(self, daten: Any) -> None:
            self.daten = daten

        def json(self) -> Any:
            return self.daten

    def get(url: str, params: dict[str, Any], headers: dict[str, str], timeout: float) -> Any:
        w_aufrufe.append(
            {
                "url": url,
                "params": {k: str(v) for k, v in params.items()},
                "headers": headers,
                "timeout": timeout,
            }
        )
        a = w_antwort.pop(0)
        if isinstance(a, Exception):
            raise a
        return _WResp(a)

    uhr = [1000.0]
    fake_time = types.SimpleNamespace(time=lambda: uhr[0], sleep=lambda s: schlaf.append(s))
    tmp = Path(tempfile.mkdtemp(prefix="geo-capture-"))
    backend = root / "flowworkshop" / "auditworkshop" / "backend"
    pinned(root, "flowworkshop", "country_profiles")
    stubs = {
        "config": types.SimpleNamespace(
            GEOCODE_CACHE=str(tmp / "cache.json"), ALLOW_REMOTE_GEOCODING=True
        ),
        "database": types.SimpleNamespace(engine=None),
        "requests": types.SimpleNamespace(get=get),
        "sqlalchemy": types.SimpleNamespace(text=lambda s: s),
    }
    alt = {k: sys.modules.get(k) for k in stubs}
    sys.modules.update(stubs)  # type: ignore[arg-type]
    sys.path.insert(0, str(backend))
    try:
        ws = import_file(pinned(root, "flowworkshop", "geocoding"), "workshop_geocoding")
    finally:
        sys.path.remove(str(backend))
        for k, v in alt.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
    ws.time = fake_time
    ws.lookup_plz = lambda *a, **k: None
    ws.lookup_city = lambda *a, **k: None
    ws.lookup_nuts_code = lambda *a, **k: None
    for eingabe, antwort in (
        ("Beispielstadt, Hessen", ANTWORT),
        ("Nirgendwo", []),
        ("Fehlerstadt", OSError("Netz weg")),
        ("Beispielstadt, Hessen", None),
    ):
        w_aufrufe.clear()
        schlaf.clear()
        if antwort is not None:
            w_antwort[:] = [antwort]
        ws._last_request_time = 999.5
        faelle.append(
            {
                "aufrufer": "flowworkshop.geocoding_service.geocode_single",
                "eingabe": eingabe,
                "ergebnis": observe(lambda e=eingabe: ws.geocode_single(e, "DE")),
                "anfragen": list(w_aufrufe),
                "pause_s": list(schlaf),
                "zwischenspeicher": {k: v for k, v in ws._cache.items()},
            }
        )
    return faelle


if __name__ == "__main__":
    raise SystemExit(main())
