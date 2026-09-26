"""Hilfe für optionale Extras."""

from __future__ import annotations

import importlib
from types import ModuleType

from .errors import OptionalDependencyError


def require_module(module: str, extra: str) -> ModuleType:
    """Importiert ``module`` oder meldet das fehlende Extra verständlich."""
    try:
        return importlib.import_module(module)
    except ImportError as error:
        raise OptionalDependencyError(
            f"Für diese Funktion ist das Extra '{extra}' nötig: pip install 'auditcore_bpmn[{extra}]'"
        ) from error
