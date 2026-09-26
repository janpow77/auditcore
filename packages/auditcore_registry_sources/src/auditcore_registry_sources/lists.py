"""List catalogues: which lists a source variant screens, where they come from.

Each catalogue is a profile (``*.sanctions_lists``). The licence stated in the
source application refers to the original list; lists obtained through
OpenSanctions fall under the OpenSanctions data terms. Both are recorded.
"""

from __future__ import annotations

from .errors import ProfileError
from .model import SanctionsList
from .profiles import RegistryProfile, load_profile


def list_catalog(profile: RegistryProfile) -> tuple[SanctionsList, ...]:
    """The lists of a list catalogue profile, in the order of the source."""
    profile.require_kind("list_catalog")
    result = []
    for item in profile.setting("lists"):
        result.append(
            SanctionsList(
                key=item["key"],
                source_key=item["source_key"],
                name=item["name"],
                issuer=item["issuer"],
                url=item["url"],
                format=item["format"],
                provider=item["provider"],
                licence_claimed_in_source=item["licence_claimed_in_source"],
                data_licence=item["data_licence"],
            )
        )
    return tuple(result)


def load_lists(profile_id: str, version: str) -> tuple[SanctionsList, ...]:
    """Convenience: load a list catalogue profile and return its lists."""
    return list_catalog(load_profile(profile_id, version))


def find_list(lists: tuple[SanctionsList, ...], key: str) -> SanctionsList:
    """List by key; an unknown key is an error, never ``None``."""
    for item in lists:
        if item.key == key:
            return item
    raise ProfileError(f"Unbekannte Liste '{key}'.")
