"""Synthetische GeoPackage-Dateien für die Tests der Web-Schnittstelle."""

from __future__ import annotations

import sqlite3
import struct
from collections.abc import Sequence

Ring = Sequence[tuple[float, float]]


def gpkg_blob(polygons: Sequence[Sequence[Ring]], srs_id: int) -> bytes:
    """GeoPackageBinary ohne Hüllrechteck mit ISO-WKB (Polygon bzw. MultiPolygon)."""

    def polygon(rings: Sequence[Ring]) -> bytes:
        data = struct.pack("<BII", 1, 3, len(rings))
        for ring in rings:
            data += struct.pack("<I", len(ring)) + b"".join(struct.pack("<dd", *p) for p in ring)
        return data

    if len(polygons) == 1:
        wkb = polygon(polygons[0])
    else:
        wkb = struct.pack("<BII", 1, 6, len(polygons)) + b"".join(polygon(p) for p in polygons)
    return b"GP" + bytes([0, 1]) + struct.pack("<i", srs_id) + wkb


def gpkg_file(
    features: Sequence[tuple[str | None, object]], srs_id: int = 4326, *, table: str = "gebiete"
) -> bytes:
    """Minimale GeoPackage-Datei (SQLite) mit einer Flächentabelle."""
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


SQUARE: Ring = [(8.66, 50.10), (8.70, 50.10), (8.70, 50.12), (8.66, 50.12), (8.66, 50.10)]
