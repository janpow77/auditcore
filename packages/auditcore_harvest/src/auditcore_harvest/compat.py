"""Compatibility helpers for renamed public names of harvest and source packages."""

from __future__ import annotations

import warnings
from collections.abc import Callable, Mapping


def deprecated_aliases(
    module: str, aliases: Mapping[str, tuple[str, object]]
) -> Callable[[str], object]:
    """Module ``__getattr__`` serving renamed names with a :class:`DeprecationWarning`.

    ``aliases`` maps each old name to ``(new_name, object)``. Usage in a module::

        __getattr__ = deprecated_aliases(__name__, {"AlterName": ("NewName", NewName)})
    """
    table = dict(aliases)

    def __getattr__(name: str) -> object:
        if name in table:
            new_name, value = table[name]
            warnings.warn(
                f"{name} heißt jetzt {new_name}; der alte Name entfällt in einer künftigen "
                "Version.",
                DeprecationWarning,
                stacklevel=2,
            )
            return value
        raise AttributeError(f"module {module!r} has no attribute {name!r}")

    return __getattr__
