"""Message templates of profiles: only plain placeholders, no attribute or index access."""

from __future__ import annotations

import string

from .errors import ProfileError


def check_template(template: object, where: str) -> None:
    """Message templates may only reference plain names (no attribute/index access)."""
    if not isinstance(template, str):
        raise ProfileError(f"{where}: Textvorlage muss Text sein.")
    try:
        parts = list(string.Formatter().parse(template))
    except ValueError as exc:
        raise ProfileError(f"{where}: ungültige Textvorlage: {exc}") from exc
    for _literal, name, spec, conversion in parts:
        if name is None:
            continue
        if not name.isidentifier() or conversion not in (None, "") or (spec and "{" in spec):
            raise ProfileError(f"{where}: unzulässiger Platzhalter {name!r}.")
