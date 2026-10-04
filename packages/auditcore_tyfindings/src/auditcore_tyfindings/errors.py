"""Fehlervertrag der Bibliothek; ``code`` ist stabil und maschinenlesbar."""

from __future__ import annotations


class TyFindingsFehler(Exception):
    """Basisklasse aller Fehler der Bibliothek."""

    code = "tyfindings_error"


class ProfilFehler(TyFindingsFehler, ValueError):
    """Ein Profil oder eine Tabelle fehlt, ist fehlerhaft oder nicht ausdrücklich gewählt."""

    code = "profile_error"


class EingabeFehler(TyFindingsFehler, TypeError):
    """Eine Eingabe hat den falschen Typ (z. B. Kennziffer als Zahl statt als Text)."""

    code = "input_error"
