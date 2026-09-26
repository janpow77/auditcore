"""Grenzen und Anschlüsse der Geo-Schnittstelle (vom einbindenden Server gesetzt)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from .geocoding import Geocoder

MAX_BODY_BYTES = 16 * 1024 * 1024
MAX_GPKG_BYTES = 64 * 1024 * 1024


@dataclass(frozen=True)
class Settings:
    """Grenzen je Anfrage und optionale Anschlüsse.

    ``geocoder`` ist standardmäßig ``None``: Ohne ausdrücklich übergebenen
    Geocoder gibt es keine Adresssuche (Datenschutz; Endpunkt antwortet 404
    ``geocoder_abgeschaltet``). ``gpkg_sources`` bildet Namen auf
    GeoPackage-Dateien des Servers ab; die Oberfläche sieht nur die Namen.
    """

    max_body_bytes: int = MAX_BODY_BYTES
    max_points: int = 50_000
    max_vertices: int = 250_000
    max_gpkg_bytes: int = MAX_GPKG_BYTES
    max_gpkg_areas: int = 5_000
    gpkg_sources: Mapping[str, Path] = field(default_factory=dict)
    geocoder: Geocoder | None = None
