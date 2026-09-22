"""Registry coverage, provenance and actual runtime fingerprint enforcement."""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime
from importlib.resources import files
from pathlib import Path

import pytest

from auditcore_dummygenerator import TestDataGenerator, list_profiles, profile_reference
from auditcore_dummygenerator import profiles as module


def test_metadata_covers_actual_field_and_deviation_dispatch() -> None:
    source = files("auditcore_dummygenerator").joinpath("generator.py").read_text()
    tree = ast.parse(source)
    expected = set()
    for method, variable, category in (
        ("generate_field", "field_type", "field"),
        ("apply_deviation", "scenario", "deviation"),
    ):
        function = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == method
        )
        for node in ast.walk(function):
            if (
                isinstance(node, ast.Compare)
                and isinstance(node.left, ast.Name)
                and node.left.id == variable
            ):
                expected.update(
                    f"auditcore.dummygenerator.{category}.{item.value}"
                    for item in node.comparators
                    if isinstance(item, ast.Constant) and isinstance(item.value, str)
                )
    expected.update(f"auditcore.dummygenerator.catalog.{country}" for country in ("DE", "AT"))
    assert {profile["artifact_id"] for profile in list_profiles()} == expected


def test_profile_version_provenance_status_and_exact_reference() -> None:
    for profile in list_profiles():
        assert profile["version"] == "0.1.0"
        assert profile["status"] == "Draft"
        assert profile["type"] in {"rulebook", "template"}
        assert profile["title"] and profile["change_reason"]
        assert datetime.fromisoformat(profile["created_at"]).tzinfo is not None
        assert datetime.fromisoformat(profile["updated_at"]) >= datetime.fromisoformat(
            profile["created_at"]
        )
        assert profile["owner"]["organization"] == "UNKNOWN"
        assert profile["authors"]["source_commit_author"] == "janpow77"
        assert profile["predecessor"]["commit"] == "05bc5ac560dfff3bc7181323240745215492d09a"
        assert profile["predecessor"]["source_sha256"] == (
            "fce760d2dd06b4fe5438120e3de3f596ef8a6f7c4cbf9bdc28be7b0deb0e6780"
        )
        reference = profile_reference(profile["artifact_id"])
        assert reference["content_hash"] == profile["content_hash"]
        assert reference["version"] == profile["version"]
        assert profile["review"]["human_release_approval"] == "NOT_GRANTED"


def test_registry_cannot_be_changed_through_returned_metadata() -> None:
    before = files("auditcore_dummygenerator").joinpath("profiles.json").read_bytes()
    profiles = list_profiles()
    original = profiles[0]["title"]
    profiles[0]["title"] = "changed locally"
    TestDataGenerator(42).generate_rows({"rows": 1})
    assert list_profiles()[0]["title"] == original
    assert files("auditcore_dummygenerator").joinpath("profiles.json").read_bytes() == before


@pytest.mark.parametrize("tamper", ["content", "implementation", "duplicate"])
def test_runtime_rejects_modified_profiles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tamper: str
) -> None:
    resources = files("auditcore_dummygenerator")
    source = resources.joinpath("generator.py").read_bytes()
    registry = json.loads(resources.joinpath("profiles.json").read_text())
    if tamper == "content":
        registry["profiles"][0]["content"]["configuration"] = {"field_type": "altered"}
    elif tamper == "implementation":
        source += b"\n# altered source\n"
    else:
        registry["profiles"].append(registry["profiles"][0])
    (tmp_path / "generator.py").write_bytes(source)
    (tmp_path / "profiles.json").write_text(json.dumps(registry))
    monkeypatch.setattr(module, "files", lambda name: tmp_path)
    with pytest.raises(ValueError):
        list_profiles()


def test_unknown_profile_is_not_silently_defaulted() -> None:
    with pytest.raises(KeyError):
        profile_reference("auditcore.dummygenerator.field.not_defined")


def test_profile_reference_binds_a_real_seeded_run() -> None:
    request = {"rows": 3, "fields": [{"name": "n", "type": "number"}]}
    result = TestDataGenerator(42).generate_rows(request)
    manifest = {
        "profile": profile_reference("auditcore.dummygenerator.field.number"),
        "seed": 42,
        "request_sha256": hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest(),
        "output_sha256": hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest(),
    }
    assert manifest["profile"]["content_hash"]
    assert result == TestDataGenerator(42).generate_rows(request)
