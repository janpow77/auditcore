"""Stabile Fehlercodes ohne Geheimnisse oder fremde Kontodaten."""


class AccountError(ValueError):
    """Fachlicher Fehler mit optionalem Feldbezug."""

    def __init__(self, code: str, message: str, field: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.field = field


def require(condition: bool, code: str, message: str, field: str = "") -> None:
    """Verletzt eine Vorbedingung, bleibt der Vorgang wirkungslos."""
    if not condition:
        raise AccountError(code, message, field)
