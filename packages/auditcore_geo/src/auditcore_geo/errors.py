"""Fehlervertrag der Geobibliothek."""

from __future__ import annotations


class GeoError(ValueError):
    """Basisklasse; ``code`` ist stabil und maschinenlesbar."""

    code = "geo_error"


class KoordinatenFehler(GeoError):
    """Koordinate nicht endlich, außerhalb des Wertebereichs oder Achsenfolge unbekannt."""

    code = "koordinaten_fehler"


class GeometrieFehler(GeoError):
    """Geometrie unlesbar, unvollständig oder von einem nicht unterstützten Typ."""

    code = "geometrie_fehler"


class ProfilFehler(GeoError):
    """Unbekanntes oder ungültiges Profil (Erdmodell, Projektion)."""

    code = "profil_fehler"
