"""Shared pieces of the legacy replays: profile access and the raw index record."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache

from .profiles import RegistryProfile, load_profile
from .screening import ScreeningSettings

VERSION = "2026.09.1"


@cache
def _profile(profile_id: str) -> RegistryProfile:
    return load_profile(profile_id, VERSION)


@cache
def _settings(profile_id: str) -> ScreeningSettings:
    return ScreeningSettings.from_profile(_profile(profile_id))


@dataclass(frozen=True)
class RawRecord:
    """An index record that, unlike ``ListEntry``, may lack id or name (flowworkshop CSV path)."""

    entry_id: str
    schema: str
    name: str
    aliases: tuple[str, ...]
    birth_date: str = ""
    countries: str = ""
    addresses: str = ""
    identifiers: str = ""
    sanctions: str = ""
    program_ids: str = ""
    first_seen: str = ""
    last_seen: str = ""
