"""Packaged, versioned JSON profiles: list, recommend and load them explicitly.

Every domain package ships its profiles as ``<id>-<version>.json`` in a
resource package and never falls back to an implicit default. The loaders
of the packages differ only in validation order and messages; these
differences are explicit keywords of :func:`load_packaged_profile`.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from importlib import resources
from importlib.resources.abc import Traversable
from typing import Literal, TypeVar, cast

P = TypeVar("P")
#: The raw JSON document as the caller's parser expects it (not validated here).
R = TypeVar("R")

#: How a file name containing ``/`` or ``\\`` (and ``.`` at the start) is reported.
InvalidName = Literal["missing", "invalid", "invalid_or_hidden"]

TEXT_REQUIRED = "Profilkennung und Version sind als Text anzugeben."
INVALID_NAME = "Ungültige Profilkennung."
MISMATCH = "Profildatei und Profilkennung stimmen nicht überein."


def _json_files(resource_package: str) -> list[Traversable]:
    return [
        entry
        for entry in resources.files(resource_package).iterdir()
        if entry.name.endswith(".json")
    ]


def _read(entry: Traversable) -> object:
    return json.loads(entry.read_text(encoding="utf-8"))


def _identity(data: object) -> tuple[str, str]:
    return (str(data["id"]), str(data["version"]))  # type: ignore[index]


def packaged_profile_ids(resource_package: str) -> tuple[tuple[str, str], ...]:
    """Sorted ``(id, version)`` of every ``*.json`` in ``resource_package``."""
    return tuple(sorted(_identity(_read(entry)) for entry in _json_files(resource_package)))


def packaged_profile_entries(resource_package: str) -> dict[tuple[str, str], Traversable]:
    """``(id, version)`` → resource file; the last file wins on a duplicate identity."""
    return {_identity(_read(entry)): entry for entry in _json_files(resource_package)}


def recommended_profile_id(
    resource_package: str, purpose: str, error: Callable[[str], Exception]
) -> tuple[str, str]:
    """The only profile listing ``purpose`` in ``recommended_for``; else ``error``."""
    found = []
    for entry in _json_files(resource_package):
        data = _read(entry)
        if purpose in data.get("recommended_for", []):  # type: ignore[attr-defined]
            found.append(_identity(data))
    if len(found) != 1:
        raise error(f"Für '{purpose}' ist kein eindeutiges empfohlenes Profil hinterlegt.")
    return found[0]


def _check_name(name: str, invalid_name: InvalidName, error: Callable[[str], Exception]) -> bool:
    """True if the name is unusable and must be reported as missing."""
    separator = "/" in name or "\\" in name
    if invalid_name == "missing":
        return separator
    if separator or (invalid_name == "invalid_or_hidden" and name.startswith(".")):
        raise error(INVALID_NAME)
    return False


def load_packaged_profile(
    resource_package: str,
    profile_id: str,
    version: str,
    *,
    parse: Callable[[R], P],
    identity: Callable[[P], tuple[object, object]],
    error: Callable[[str], Exception],
    require_text: bool = False,
    invalid_name: InvalidName = "missing",
) -> P:
    """Load ``<profile_id>-<version>.json`` explicitly, parse it and check its identity.

    Order: optional text check (:data:`TEXT_REQUIRED`), file-name check
    (``invalid_name``), existence, ``parse``, identity check (:data:`MISMATCH`).
    """
    if require_text and not (isinstance(profile_id, str) and isinstance(version, str)):
        raise error(TEXT_REQUIRED)
    name = f"{profile_id}-{version}.json"
    unusable = _check_name(name, invalid_name, error)
    entry = resources.files(resource_package).joinpath(name)
    if unusable or not entry.is_file():
        raise error(f"Profil {profile_id} in Version {version} ist nicht vorhanden.")
    profile = parse(cast(R, _read(entry)))
    if tuple(identity(profile)) != (profile_id, version):
        raise error(MISMATCH)
    return profile
