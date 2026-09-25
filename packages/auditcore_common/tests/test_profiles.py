"""Profile listing, recommendation and loading against the package copies (differential)."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Iterator
from itertools import product
from pathlib import Path
from typing import Any

import legacy_reference as legacy
import pytest
from samples import assert_same_outcome

from auditcore_common.hashing import canonical_sha256
from auditcore_common.profiles import (
    InvalidName,
    load_packaged_profile,
    packaged_profile_entries,
    packaged_profile_ids,
    recommended_profile_id,
)

FILES: dict[str, object] = {
    "a-1.json": {"id": "a", "version": "1", "recommended_for": ["p1", "p2"]},
    "a-2.json": {"id": "a", "version": "2", "recommended_for": ["p2"]},
    "b-1.json": {"id": "c", "version": "1"},
    ".h-1.json": {"id": ".h", "version": "1", "recommended_for": ["p4"]},
    "a-1-1.json": {"id": "a-1", "version": "1"},
    "n-1.json": {"id": 5, "version": 1},
    "d-1.json": {"id": "d", "version": "1", "recommended_for": "p5"},
}
IDS: list[object] = ["a", "b", "c", "x/y", "x\\y", ".h", "", "a-1", "n", "d", 1, None]
VERSIONS: list[object] = ["1", "2", "..", "", None, 1]


@pytest.fixture()
def resource_package(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    name = "legacy_profiles_pkg"
    package = tmp_path / name
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "notes.txt").write_text("not a profile")
    for file, data in FILES.items():
        (package / file).write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setattr(legacy, "RESOURCE_PACKAGE", name)
    yield name
    sys.modules.pop(name, None)


def _dataclass_loader(
    package: str, require_text: bool, invalid_name: InvalidName
) -> Callable[[Any, Any], object]:
    return lambda pid, ver: load_packaged_profile(
        package,
        pid,
        ver,
        parse=legacy.profile_from_dict,
        identity=lambda p: (p.id, p.version),
        error=legacy.ProfileError,
        require_text=require_text,
        invalid_name=invalid_name,
    )


def _funding_loader(package: str) -> Callable[[Any, Any], object]:
    def load(pid: Any, ver: Any) -> object:
        data = load_packaged_profile(
            package,
            pid,
            ver,
            parse=lambda raw: raw,
            identity=lambda d: (d.get("id"), d.get("version")),  # type: ignore[attr-defined]
            error=legacy.ProfileError,
            invalid_name="invalid_or_hidden",
        )
        return {**data, "fingerprint": canonical_sha256(data)}  # type: ignore[dict-item]

    return load


LOADERS: dict[str, tuple[Callable[..., object], tuple[bool, InvalidName] | None]] = {
    "dataprotection": (legacy.dataprotection_load_profile, (True, "missing")),
    "entity_matching": (legacy.entity_load_profile, (True, "missing")),
    "procurement": (legacy.procurement_load_profile, (False, "missing")),
    "market_indicators": (legacy.market_load_profile, (True, "invalid")),
    "registry_sources": (legacy.registry_load_profile, (True, "invalid")),
    "legal_sources": (legacy.legal_load_profile, (False, "invalid_or_hidden")),
    "funding_sources": (legacy.funding_load_profile, None),
}


@pytest.mark.parametrize("variant", sorted(LOADERS))
def test_load_matches_every_loader(variant: str, resource_package: str) -> None:
    old, flags = LOADERS[variant]
    new = (
        _funding_loader(resource_package)
        if flags is None
        else _dataclass_loader(resource_package, *flags)
    )
    for pid, ver in product(IDS, VERSIONS):
        assert_same_outcome(lambda: old(pid, ver), lambda: new(pid, ver))


def test_listing_matches(resource_package: str) -> None:
    assert packaged_profile_ids(resource_package) == legacy.dataprotection_available_profiles()
    old = legacy.risk_packaged()
    new = packaged_profile_entries(resource_package)
    assert list(old) == list(new)
    assert [e.name for e in old.values()] == [e.name for e in new.values()]


@pytest.mark.parametrize("purpose", ["p1", "p2", "p3", "p4", "p5", ""])
def test_recommended_matches(purpose: str, resource_package: str) -> None:
    def new() -> object:
        found = recommended_profile_id(resource_package, purpose, legacy.ProfileError)
        return legacy.entity_load_profile(*found)

    assert_same_outcome(lambda: legacy.entity_recommended_profile(purpose), new)
