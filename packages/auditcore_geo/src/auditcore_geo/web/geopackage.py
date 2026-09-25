"""GeoPackage-Dateien (SQLite) lesen und Flächen als GeoJSON liefern (``/gpkg``).

Die Datei wird nur im Speicher geöffnet (``sqlite3.Connection.deserialize``),
schreibgeschützt und ohne vertrauenswürdiges Schema; Tabellen- und
Spaltennamen stammen ausschließlich aus ``gpkg_geometry_columns`` bzw.
``PRAGMA table_info`` und werden quotiert. Ein Fortschrittswächter bricht
übermäßig lange Abfragen ab.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .._flaechenmodell import GEOGRAPHISCHE_SRS_IDS, flaeche_aus_ringen
from ..errors import GeoError
from ..gpkg import lies_gpkg_polygone
from ..projektion import GRS80, WGS84, UtmZone, utm_nach_geographisch_lonlat
from ._contract import ContractError
from .settings import Settings

SQLITE_HEADER = b"SQLite format 3\x00"
POLYGON_TYPES = frozenset({"POLYGON", "MULTIPOLYGON", "CURVEPOLYGON", "MULTISURFACE", "GEOMETRY"})
LABEL_COLUMNS = ("name", "bezeichnung", "gebietsname", "gen", "label", "titel", "title")
MAX_VM_STEPS = 50_000_000
DIGITS = 7

Transform = Callable[[float, float], tuple[float, float]]


@dataclass(frozen=True)
class _Layer:
    table: str
    column: str
    srs_id: int


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _open(data: bytes) -> sqlite3.Connection:
    if not data.startswith(SQLITE_HEADER):
        raise ContractError("Keine GeoPackage-Datei (SQLite-Kopf fehlt).", code="kein_geopackage")
    connection = sqlite3.connect(":memory:")
    try:
        connection.deserialize(data)
        connection.execute("PRAGMA query_only = ON")
        connection.execute("PRAGMA trusted_schema = OFF")
        steps = [0]

        def guard() -> int:
            steps[0] += 1
            return 1 if steps[0] * 1000 > MAX_VM_STEPS else 0

        connection.set_progress_handler(guard, 1000)
        connection.execute("SELECT count(*) FROM sqlite_master").fetchone()
    except sqlite3.DatabaseError as exc:
        connection.close()
        raise ContractError(f"GeoPackage unlesbar: {exc}", code="kein_geopackage") from exc
    return connection


def _layers(connection: sqlite3.Connection) -> list[_Layer]:
    try:
        rows = connection.execute(
            "SELECT c.table_name, c.column_name, c.geometry_type_name, c.srs_id "
            "FROM gpkg_geometry_columns c JOIN sqlite_master m "
            "ON m.name = c.table_name AND m.type = 'table' ORDER BY c.table_name"
        ).fetchall()
    except sqlite3.DatabaseError as exc:
        raise ContractError(
            "Tabelle gpkg_geometry_columns fehlt – keine GeoPackage-Datei.", code="kein_geopackage"
        ) from exc
    return [
        _Layer(str(t), str(c), int(s))
        for t, c, kind, s in rows
        if str(kind).upper() in POLYGON_TYPES
    ]


def _transform(srs_id: int) -> Transform | None:
    """``None`` for geographic data; UTM back-projection for ETRS89/WGS 84 UTM zones."""
    if srs_id in GEOGRAPHISCHE_SRS_IDS:
        return None
    if 25828 <= srs_id <= 25838:
        zone = UtmZone(srs_id - 25800, True, GRS80)
    elif 32601 <= srs_id <= 32660 or 32701 <= srs_id <= 32760:
        zone = UtmZone(srs_id % 100, srs_id < 32700, WGS84)
    else:
        raise ContractError(
            f"Bezugssystem srs_id {srs_id} wird nicht umgerechnet "
            "(unterstützt: 4326, 4258, ETRS89/UTM 25828–25838, WGS 84/UTM 326xx/327xx).",
            code="profil_fehler",
        )
    return lambda x, y: utm_nach_geographisch_lonlat(x, y, zone)


def _label_column(connection: sqlite3.Connection, layer: _Layer) -> str | None:
    columns = connection.execute(f"PRAGMA table_info({_quote(layer.table)})").fetchall()
    text_columns = [
        str(c[1]) for c in columns if "CHAR" in str(c[2]).upper() or "TEXT" in str(c[2]).upper()
    ]
    for wanted in LABEL_COLUMNS:
        for name in text_columns:
            if name.lower() == wanted:
                return name
    return text_columns[0] if text_columns else None


def _select_sql(layer: _Layer, label: str | None) -> str:
    """Abfrage der Flächen; Namen stammen aus dem GeoPackage-Schema und sind quotiert."""
    label_sql = _quote(label) if label else "NULL"
    columns = f"rowid, {label_sql}, {_quote(layer.column)}"
    return f"SELECT {columns} FROM {_quote(layer.table)} ORDER BY rowid LIMIT ?"  # nosec B608 - nur quotierte Schemanamen, Grenzwert als Parameter


def _geojson(polygons: Sequence[Sequence[Sequence[tuple[float, float]]]]) -> dict[str, object]:
    coordinates = []
    for polygon in polygons:
        rings = []
        for ring in polygon:
            points = [[round(x, DIGITS), round(y, DIGITS)] for x, y in ring]
            if points and points[0] != points[-1]:
                points.append(points[0])
            rings.append(points)
        coordinates.append(rings)
    return {"type": "MultiPolygon", "coordinates": coordinates}


def _feature(
    fid: object, label: object, blob: object, transform: Transform | None
) -> dict[str, object]:
    if not isinstance(blob, bytes):
        raise GeoError("Geometrie fehlt.")
    geometry = lies_gpkg_polygone(blob)
    polygons = [[list(ring) for ring in polygon] for polygon in geometry.polygone]
    if transform is not None:
        polygons = [
            [[transform(x, y) for x, y in ring] for ring in polygon] for polygon in polygons
        ]
    flaeche = flaeche_aus_ringen(polygons)
    return {
        "id": str(fid),
        "bezeichnung": None if label is None else str(label),
        "geometrie": _geojson(polygons),
        "hinweise": list(flaeche.hinweise),
    }


def _choose(layers: list[_Layer], table: str | None) -> _Layer:
    if not layers:
        raise ContractError("Die Datei enthält keine Flächentabelle.", code="keine_flaechen")
    if table is None:
        return layers[0]
    for layer in layers:
        if layer.table == table:
            return layer
    raise ContractError(f"Flächentabelle {table!r} nicht gefunden.", status=404, code="unbekannt")


def read_geopackage(
    daten: bytes, settings: Settings, tabelle: str | None = None
) -> dict[str, object]:
    """Flächen einer GeoPackage-Datei als GeoJSON (``(lon, lat)``, WGS 84/ETRS89).

    Unlesbare Einzelgeometrien stehen in ``fehler`` (nie still verworfen);
    über ``max_gpkg_areas`` hinaus wird abgeschnitten und ``abgeschnitten``
    gesetzt.
    """
    if len(daten) > settings.max_gpkg_bytes:
        raise ContractError("GeoPackage zu groß.", status=413, code="zu_gross")
    connection = _open(daten)
    try:
        layers = _layers(connection)
        layer = _choose(layers, tabelle)
        transform = _transform(layer.srs_id)
        label = _label_column(connection, layer)
        rows = connection.execute(
            _select_sql(layer, label),
            (settings.max_gpkg_areas + 1,),
        ).fetchall()
    except sqlite3.OperationalError as exc:
        raise ContractError(
            f"GeoPackage-Abfrage abgebrochen: {exc}", code="kein_geopackage"
        ) from exc
    finally:
        connection.close()
    flaechen, fehler = [], []
    for fid, name, blob in rows[: settings.max_gpkg_areas]:
        try:
            flaechen.append(_feature(fid, name, blob, transform))
        except GeoError as exc:
            fehler.append({"id": str(fid), "meldung": str(exc)})
    return {
        "tabellen": [entry.table for entry in layers],
        "tabelle": layer.table,
        "srs_id": layer.srs_id,
        "umgerechnet": transform is not None,
        "flaechen": flaechen,
        "fehler": fehler,
        "abgeschnitten": len(rows) > settings.max_gpkg_areas,
    }


def read_source(name: str, settings: Settings, tabelle: str | None = None) -> dict[str, object]:
    """Eine vom Server benannte GeoPackage-Quelle lesen (``/gpkg/quellen/{name}``)."""
    path = settings.gpkg_sources.get(name)
    if path is None:
        raise ContractError(
            f"GeoPackage-Quelle {name!r} ist nicht eingerichtet.", status=404, code="unbekannt"
        )
    if path.stat().st_size > settings.max_gpkg_bytes:
        raise ContractError("GeoPackage zu groß.", status=413, code="zu_gross")
    return {"quelle": name, **read_geopackage(path.read_bytes(), settings, tabelle)}
