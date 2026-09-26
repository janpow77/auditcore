"""Demo-Backend der Geo-Karte: synthetische Kacheln und GeoPackage-Dateien.

``demo/api_server.py`` bindet ``auditcore_geo.web`` unter ``/api/geo`` ein
(Extra ``web``) und diese Hilfsrouten unter ``/api/geo-demo``. Alle
Koordinaten und Flächen sind erfunden; die Kacheln sind einfarbige Raster
ohne Kartendaten (kein fremder Kachelserver). Nicht für den Produktivbetrieb.
"""

from __future__ import annotations

import math
import sqlite3
import struct
import tempfile
import zlib
from collections.abc import Sequence
from pathlib import Path

from auditcore_geo import ETRS89_UTM32N, Punkt, geographisch_nach_utm
from auditcore_geo.web import Settings
from auditcore_geo.web import routes as geo_routes
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import BaseRoute, Route

Ring = Sequence[tuple[float, float]]


def _blob(polygons: Sequence[Sequence[Ring]], srs_id: int) -> bytes:
    """GeoPackageBinary (ohne Hüllrechteck) mit ISO-WKB-MultiPolygon."""
    wkb = struct.pack("<BII", 1, 6, len(polygons))
    for rings in polygons:
        wkb += struct.pack("<BII", 1, 3, len(rings))
        for ring in rings:
            wkb += struct.pack("<I", len(ring)) + b"".join(struct.pack("<dd", *p) for p in ring)
    return b"GP" + bytes([0, 1]) + struct.pack("<i", srs_id) + wkb


def _gpkg(features: Sequence[tuple[str, bytes]], srs_id: int, table: str) -> bytes:
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        "CREATE TABLE gpkg_geometry_columns (table_name TEXT, column_name TEXT, "
        "geometry_type_name TEXT, srs_id INTEGER, z INTEGER, m INTEGER);"
        f'CREATE TABLE "{table}" (fid INTEGER PRIMARY KEY, name TEXT, geom BLOB);'
    )
    connection.execute(
        "INSERT INTO gpkg_geometry_columns VALUES (?, 'geom', 'MULTIPOLYGON', ?, 0, 0)",
        (table, srs_id),
    )
    connection.executemany(f'INSERT INTO "{table}" (name, geom) VALUES (?, ?)', features)
    connection.commit()
    data = connection.serialize()
    connection.close()
    return data


def _ellipse(
    lon: float, lat: float, rx: float, ry: float, n: int, wobble: float
) -> list[tuple[float, float]]:
    ring = [
        (
            lon + rx * math.cos(2 * math.pi * i / n) * (1 + wobble * math.sin(7 * i / n * math.pi)),
            lat + ry * math.sin(2 * math.pi * i / n) * (1 + wobble * math.cos(5 * i / n * math.pi)),
        )
        for i in range(n)
    ]
    return [*ring, ring[0]]


def demo_upload_file() -> bytes:
    """Zum Hochladen in der Demo: zwei erfundene Flächen in EPSG:4326."""
    moor = _ellipse(9.02, 50.36, 0.03, 0.018, 120, 0.12)
    auwald = _ellipse(8.93, 50.29, 0.02, 0.012, 60, 0.05)
    features = [
        ("Moorgebiet (Demo)", _blob([[moor]], 4326)),
        ("Auwald (Demo)", _blob([[auwald]], 4326)),
    ]
    return _gpkg(features, 4326, "schutzgebiete")


def _server_source(folder: Path) -> Path:
    """Serverquelle in ETRS89/UTM 32N (EPSG:25832), damit die Umrechnung sichtbar ist."""
    ring = [(9.08, 50.30), (9.14, 50.30), (9.14, 50.33), (9.08, 50.33), (9.08, 50.30)]
    hole = [(9.10, 50.31), (9.12, 50.31), (9.12, 50.32), (9.10, 50.32), (9.10, 50.31)]
    utm = [
        [geographisch_nach_utm(Punkt(lat=y, lon=x), ETRS89_UTM32N) for x, y in r]
        for r in (ring, hole)
    ]
    path = folder / "landschaftsschutz-demo.gpkg"
    path.write_bytes(_gpkg([("Landschaftsschutz (Demo, UTM)", _blob([utm], 25832))], 25832, "lsg"))
    return path


def _png(width: int, height: int, pixel: bytes) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    line = b"\x00" + pixel * width
    raw = line * height
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


TILES = {0: _png(256, 256, bytes((226, 232, 222))), 1: _png(256, 256, bytes((218, 226, 214)))}


async def tile(request: Request) -> Response:
    """Schachbrett aus zwei Grüntönen je Kachel: nur Orientierung, keine Kartendaten."""
    x, y = int(request.path_params["x"]), int(request.path_params["y"])
    return Response(
        TILES[(x + y) % 2], media_type="image/png", headers={"Cache-Control": "max-age=3600"}
    )


async def upload_file(_: Request) -> Response:
    headers = {"Content-Disposition": 'attachment; filename="schutzgebiete-demo.gpkg"'}
    return Response(
        demo_upload_file(), media_type="application/geopackage+sqlite3", headers=headers
    )


def geo_routes_demo() -> tuple[list[BaseRoute], list[BaseRoute]]:
    """(Routen für ``/api/geo``, Hilfsrouten für ``/api/geo-demo``)."""
    folder = Path(tempfile.mkdtemp(prefix="flowaudit-geo-demo-"))
    settings = Settings(gpkg_sources={"landschaftsschutz-demo": _server_source(folder)})
    helper: list[BaseRoute] = [
        Route("/kacheln/{z:int}/{x:int}/{y:int}.png", tile),
        Route("/schutzgebiete-demo.gpkg", upload_file),
    ]
    return list(geo_routes(settings=settings)), helper
