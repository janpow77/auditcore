"""Zusammengefallene Ringe (GEO-C16): Original, 0.1.0 und Referenz tatsächlich ausführen.

Synthetische Geometrien (Ringe mit 1–4 gleichen Punkten, kollineare Ringe,
zusammengefallene Löcher, Multipolygone mit zusammengefallener Teilfläche)
werden ausgeführt gegen

- die Originalfunktionen aus ``audit_designer@1254591`` (``_point_in_geometry``,
  ``_geometry_edge_distance_m``, ``_geometry_centroid``,
  ``_NaturaClient._distance_to_geometry_m``) und ``flowsearch@10cb2a3``
  (``_get_geometry_center``) – geladen wie in ``capture_legacy.py``;
- ``auditcore_geo`` **0.1.0** (Quellbaum des Tags ``v0.3.0``), um das
  Verwerfen der ganzen Geometrie festzuhalten;
- eine Referenz aus shapely/pyproj (Abstand in EPSG:25832 zu den echten
  Teilflächen und den zusammengefallenen Außenringen als Punkt/Linie).

Die neue Bibliothek wird nicht verwendet.

    python tools/capture_entartet.py <Quellen> <src-0.1.0> tests/fixtures/entartet_observed.json

``<src-0.1.0>`` ist das Verzeichnis ``packages/auditcore_geo/src`` im Stand
``v0.3.0`` (etwa ``git archive v0.3.0 packages/auditcore_geo/src``).
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import platform
import sys
from pathlib import Path
from typing import Any

import pyproj
import shapely
import shapely.ops as sops
from shapely.geometry import LineString, MultiPolygon
from shapely.geometry import Point as SPoint
from shapely.geometry import Polygon as SPolygon

sys.path.insert(0, str(Path(__file__).parent))
from capture_legacy import SOURCES, extract, observe, pinned  # noqa: E402

A = [8.6800, 50.1100]
B = [8.6810, 50.1100]
C = [8.6820, 50.1100]
QUADRAT = [[8.66, 50.10], [8.70, 50.10], [8.70, 50.12], [8.66, 50.12], [8.66, 50.10]]

GEOMETRIEN: dict[str, dict[str, Any]] = {
    "punkt_1_position": {"type": "Polygon", "coordinates": [[A]]},
    "punkt_2_gleich": {"type": "Polygon", "coordinates": [[A, A]]},
    "punkt_3_gleich": {"type": "Polygon", "coordinates": [[A, A, A]]},
    "punkt_4_gleich": {"type": "Polygon", "coordinates": [[A, A, A, A]]},
    "linie_2_punkte": {"type": "Polygon", "coordinates": [[A, C, A]]},
    "kollinear_dezimal": {
        "type": "Polygon",
        "coordinates": [[[8.61, 50.11], [8.62, 50.12], [8.63, 50.13], [8.61, 50.11]]],
    },
    "kollinear_hin_und_zurueck": {"type": "Polygon", "coordinates": [[A, B, C, B, A]]},
    "loch_als_linie": {
        "type": "Polygon",
        "coordinates": [QUADRAT, [[8.67, 50.11], [8.69, 50.11], [8.67, 50.11]]],
    },
    "loch_als_punkt": {
        "type": "Polygon",
        "coordinates": [QUADRAT, [[8.68, 50.11], [8.68, 50.11], [8.68, 50.11], [8.68, 50.11]]],
    },
    "multi_mit_punktteil": {
        "type": "MultiPolygon",
        "coordinates": [[QUADRAT], [[[8.75, 50.11], [8.75, 50.11], [8.75, 50.11], [8.75, 50.11]]]],
    },
    "multi_nur_entartet": {
        "type": "MultiPolygon",
        "coordinates": [
            [[[8.75, 50.11], [8.75, 50.11], [8.75, 50.11], [8.75, 50.11]]],
            [[[8.76, 50.12], [8.78, 50.12], [8.76, 50.12]]],
        ],
    },
    "aussen_entartet_mit_loch": {
        "type": "Polygon",
        "coordinates": [
            [A, A, A, A],
            [[8.67, 50.105], [8.69, 50.105], [8.69, 50.115], [8.67, 50.105]],
        ],
    },
}

#: Abfragepunkte (lon, lat): auf dem Objekt, rund 50/100 m daneben, innen, weit weg.
PUNKTE: list[list[float]] = [
    A,
    B,
    [8.6800, 50.11045],
    [8.6814, 50.1100],
    [8.6800, 50.1109],
    [8.62, 50.12],
    [8.62, 50.1205],
    [8.6805, 50.11],
    [8.675, 50.11],
    [8.685, 50.105],
    [8.75, 50.11],
    [8.75, 50.1105],
    [8.77, 50.1204],
    [8.60, 50.00],
]


def _ist_entartet(ring: list[list[float]]) -> bool:
    punkte = {(float(p[0]), float(p[1])) for p in ring}
    if len(punkte) < 3:
        return True
    xs, ys = [p[0] for p in punkte], [p[1] for p in punkte]
    ausdehnung = (max(xs) - min(xs)) ** 2 + (max(ys) - min(ys)) ** 2
    return float(SPolygon(ring).area) <= 1e-12 * ausdehnung


def referenz(geometrie: dict[str, Any]) -> list[Any]:
    """Teile der Referenz: echte Polygone, zusammengefallene Außenringe als Punkt/Linie."""
    polys = (
        [geometrie["coordinates"]]
        if geometrie["type"] == "Polygon"
        else list(geometrie["coordinates"])
    )
    teile: list[Any] = []
    for poly in polys:
        aussen = poly[0]
        if _ist_entartet(aussen):
            verschieden = list(dict.fromkeys((float(p[0]), float(p[1])) for p in aussen))
            teile.append(SPoint(verschieden[0]) if len(verschieden) == 1 else LineString(aussen))
            continue
        loecher = [r for r in poly[1:] if not _ist_entartet(r)]
        teile.append(SPolygon(aussen, loecher))
    return teile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", type=Path)
    parser.add_argument("geo_010_src", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    root = args.sources.resolve()

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
    company = extract(
        pinned(root, "audit_designer", "company"),
        [],
        {"math": math},
        methods={"_NaturaClient": ["_haversine_m", "_distance_to_geometry_m"]},
    )
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

    sys.path.insert(0, str(args.geo_010_src.resolve()))
    geo010 = importlib.import_module("auditcore_geo")
    if geo010.__version__ != "0.1.0":
        raise SystemExit(f"auditcore_geo 0.1.0 erwartet, gefunden {geo010.__version__}")

    transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)
    faelle = []
    for name, geometrie in GEOMETRIEN.items():
        teile = referenz(geometrie)
        teile_utm = [sops.transform(transformer.transform, t) for t in teile]
        echte = [t for t in teile if isinstance(t, SPolygon)]
        schwerpunkt = (
            MultiPolygon(echte).centroid if echte else shapely.GeometryCollection(teile).centroid
        )
        punkte = []
        for lon, lat in PUNKTE:
            px, py = transformer.transform(lon, lat)
            p_utm = SPoint(px, py)
            p = SPoint(lon, lat)
            innen = any(t.contains(p) for t in teile if isinstance(t, SPolygon))
            rand = any(
                (t.boundary if isinstance(t, SPolygon) else t).distance(p) == 0 for t in teile
            )
            punkte.append(
                {
                    "punkt_lonlat": [lon, lat],
                    "designer_gis_point_in_geometry": observe(
                        lambda lon=lon, lat=lat, g=geometrie: gis["_point_in_geometry"](lon, lat, g)
                    ),
                    "designer_gis_edge_distance_m": observe(
                        lambda lon=lon, lat=lat, g=geometrie: gis["_geometry_edge_distance_m"](
                            lon, lat, g
                        )
                    ),
                    "designer_company_distance_to_geometry_m": observe(
                        lambda lon=lon, lat=lat, g=geometrie: company["_distance_to_geometry_m"](
                            _Selbst(), lat, lon, g
                        )
                    ),
                    "referenz_lage": "rand" if rand else ("innen" if innen else "aussen"),
                    "referenz_utm32_abstand_m": 0.0
                    if innen or rand
                    else min(
                        (t.boundary if isinstance(t, SPolygon) else t).distance(p_utm)
                        for t in teile_utm
                    ),
                }
            )
        faelle.append(
            {
                "name": name,
                "geometrie": geometrie,
                "auditcore_geo_010_flaeche_aus_geojson": observe(
                    lambda g=geometrie: len(geo010.flaeche_aus_geojson(g).polygone)
                ),
                "designer_gis_geometry_centroid": observe(
                    lambda g=geometrie: gis["_geometry_centroid"](g)
                ),
                "flowsearch_get_geometry_center": observe(
                    lambda g=geometrie: fs_natura["_get_geometry_center"](None, g)
                ),
                "referenz_shapely_schwerpunkt": [schwerpunkt.x, schwerpunkt.y],
                "punkte": punkte,
            }
        )

    ergebnis = {
        "schema": "auditcore_geo.entartet_observed/1",
        "sources": {
            k: {"repository": SOURCES[k]["repository"], "commit": SOURCES[k]["commit"]}
            for k in ("audit_designer", "flowsearch")
        },
        "auditcore_geo_010": {"tag": "v0.3.0", "version": geo010.__version__},
        "environment": {
            "python": platform.python_version(),
            "pyproj": pyproj.__version__,
            "proj": pyproj.proj_version_str,
            "shapely": shapely.__version__,
        },
        "cases": faelle,
    }
    args.output.write_text(
        json.dumps(ergebnis, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(json.dumps({"geometrien": len(faelle), "punkte": len(faelle) * len(PUNKTE)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
