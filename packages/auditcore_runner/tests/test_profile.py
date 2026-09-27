from __future__ import annotations

import json
from dataclasses import replace
from importlib.resources import files
from pathlib import Path

import jsonschema
import pytest

from auditcore_runner import profile_io
from auditcore_runner.hardware import HostFacts, parse_meminfo, parse_nvidia_csv
from auditcore_runner.profile import Target
from auditcore_runner.propose import propose
from auditcore_runner.validation import validate


def test_parse_meminfo_and_nvidia() -> None:
    memory = parse_meminfo("MemTotal:       61805536 kB\nSwapTotal: 8388604 kB\nSwapFree: 8388604 kB\n")
    assert memory["MemTotal"] == 60356 and memory["SwapFree"] == 8191
    cards = parse_nvidia_csv("0, GPU-a, NVIDIA RTX, 16303\n1, GPU-b, NVIDIA RTX 2, 8151\nKopf\n")
    assert [(c.index, c.uuid, c.vram_mb) for c in cards] == [(0, "GPU-a", 16303), (1, "GPU-b", 8151)]


def test_propose_large_machine_is_valid(workstation_facts: HostFacts) -> None:
    profile = propose(workstation_facts, "owner/repo")
    assert set(profile.classes) == {"cpu-gross", "gpu-16gb"}
    assert profile.classes["cpu-gross"].nice == 19 and profile.classes["cpu-gross"].cpu_shares == 128
    assert profile.classes["gpu-16gb"].max_instances == 2
    assert validate(profile, workstation_facts) == []


def test_propose_small_machine(server_facts: HostFacts) -> None:
    profile = propose(server_facts, "owner/repo")
    assert profile.classes["cpu"].cpus == 2 and profile.classes["cpu"].max_instances >= 1
    assert "gpu-8gb" in profile.classes
    assert validate(profile, server_facts) == []


def test_roundtrip_and_content_hash(workstation_facts: HostFacts) -> None:
    profile = propose(workstation_facts, "owner/repo")
    assert profile_io.from_json(json.loads(profile_io.dumps(profile))) == profile
    assert profile_io.content_hash(profile) == profile_io.content_hash(replace(profile, version=7))
    assert profile_io.content_hash(profile) != profile_io.content_hash(replace(profile, image="anderes:1"))


def test_example_templates_are_neutral_and_valid(workstation_facts: HostFacts, server_facts: HostFacts) -> None:
    schema = json.loads(
        files("auditcore_runner").joinpath("data", "schemas", "profil.schema.json").read_text(encoding="utf-8")
    )
    for name, facts in (("workstation-2gpu", workstation_facts), ("server-cpu", server_facts)):
        raw = json.loads(
            files("auditcore_runner").joinpath("data", "beispiele", f"{name}.json").read_text(encoding="utf-8")
        )
        jsonschema.validate(raw, schema)
        profile = profile_io.from_json(raw)
        server_profile = profile if name == "workstation-2gpu" else replace(profile, gpus=())
        assert validate(server_profile, facts) == [], name
        assert profile.target == Target("repo", "owner/repo")


def test_template_adapts_to_detected_cards(workstation_facts: HostFacts, monkeypatch: pytest.MonkeyPatch) -> None:
    from auditcore_runner import cli

    adapted = cli.from_template("workstation-2gpu", workstation_facts, "owner/repo")
    assert adapted.host == "workstation" and adapted.target.name == "owner/repo"
    assert [g.uuid for g in adapted.gpus] == [g.uuid for g in workstation_facts.gpus]
    assert validate(adapted, workstation_facts) == []


def test_migration_from_version_1() -> None:
    old = {
        "schema": "auditcore-runner/profil/1",
        "rechner": "alt",
        "repo": "owner/repo",
        "token_datei": "~/token",
        "image": "img:1",
        "reserve": {"cpus": 2, "speicher_gb": 4},
        "netz": {"name": "n", "subnetz": "172.30.1.0/24", "bruecke": "br-n", "aktiv": False, "sperre_pflicht": False},
        "aktivitaet": {"leerlauf_minuten": 5, "anteil_bei_nutzung": 0.5, "gpu0_leerlauf_minuten": 20},
        "klassen": {},
        "gpus": [],
    }
    data, applied = profile_io.migrate(old)
    assert applied == [1, 2] and data["schema"] == "auditcore-runner/profil/3"
    profile = profile_io.from_json(old)
    assert profile.target.name == "owner/repo" and profile.auth.kind == "pat" and profile.auth.token_file == "~/token"
    assert profile.scaling.idle_minutes == 5 and profile.source.kind == "statisch"


def test_newer_or_foreign_schema_is_rejected() -> None:
    with pytest.raises(profile_io.ProfileFormatError, match="neuer"):
        profile_io.from_json({"schema": "auditcore-runner/profil/99"})
    with pytest.raises(profile_io.ProfileFormatError, match="schema"):
        profile_io.from_json({"schema": "etwas/anderes"})


def test_field_errors_name_the_path(workstation_facts: HostFacts) -> None:
    data = profile_io.to_json(propose(workstation_facts, "owner/repo"))
    data["klassen"]["cpu-gross"]["cpus"] = "acht"  # type: ignore[index]
    with pytest.raises(profile_io.ProfileFormatError, match=r"klassen\.cpu-gross\.cpus"):
        profile_io.from_json(data)


def test_save_is_atomic_and_loadable(tmp_path: Path, workstation_facts: HostFacts) -> None:
    target = profile_io.save(propose(workstation_facts, "owner/repo"), tmp_path / "p" / "profil.json")
    assert profile_io.load(target).host == "workstation"
    assert not list(target.parent.glob(".profil.json.*"))
