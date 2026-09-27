"""RUN-011: class names are free; GPU behaviour follows ``art``, not the name."""

from __future__ import annotations

import json
from dataclasses import replace
from importlib.resources import files
from pathlib import Path

import jsonschema
import pytest

from auditcore_runner import backend, pool, profile_io
from auditcore_runner.hardware import HostFacts
from auditcore_runner.profile import Profile, RunnerClass
from auditcore_runner.propose import propose
from auditcore_runner.regeln import Signals, decide
from auditcore_runner.validation import validate


def renamed(facts: HostFacts) -> Profile:
    """The proposal with every class renamed – nothing may depend on the template names."""
    base = propose(facts, "owner/repo")
    mapping = {name: ("ml-karte" if c.is_gpu else "bau") for name, c in base.classes.items()}
    classes = {mapping[name]: c for name, c in base.classes.items()}
    gpus = tuple(replace(g, runner_class=mapping[g.runner_class]) for g in base.gpus)
    return replace(base, classes=classes, gpus=gpus)


def test_free_names_validate_and_scale(workstation_facts: HostFacts) -> None:
    profile = renamed(workstation_facts)
    assert set(profile.classes) == {"bau", "ml-karte"} and profile.gpu_classes() == ["ml-karte"]
    assert validate(profile, workstation_facts) == []
    signals = Signals(cpu_count=32, load_1m=1.0, memory_available_mb=40_000, swap_used_mb=0, idle_seconds=3600)
    targets = decide(profile, signals).targets
    assert set(targets) == {"bau", "ml-karte"} and targets["ml-karte"] > 0
    assert backend.backend("jit").environment(profile, "ml-karte", 1)["AUDITCORE_RUNNER_GPU_CLASS"] == "1"
    assert backend.backend("jit").environment(profile, "bau", 1)["AUDITCORE_RUNNER_GPU_CLASS"] == ""


def test_kind_rules(workstation_facts: HostFacts) -> None:
    profile = renamed(workstation_facts)
    cpu_with_cards = replace(
        profile, classes={**profile.classes, "ml-karte": replace(profile.classes["ml-karte"], kind="cpu", vram_mb=6000)}
    )
    fields = {p.field for p in validate(cpu_with_cards, workstation_facts)}
    assert "gpus[0].klasse" in fields and "klassen.ml-karte.vram_mb" in fields
    odd = replace(profile, classes={**profile.classes, "bau": replace(profile.classes["bau"], kind="tpu")})
    assert "klassen.bau.art" in {p.field for p in validate(odd, workstation_facts)}
    long_name = replace(profile, classes={**profile.classes, "x" * 40: profile.classes["bau"]})
    assert f"klassen.{'x' * 40}" in {p.field for p in validate(long_name, workstation_facts)}


def test_pool_accepts_any_valid_name() -> None:
    parsed = pool.parse({"schema": pool.POOL_SCHEMA, "klassen": {"bau": {"soll": 2}}})
    assert parsed.targets == {"bau": 2}
    assert pool.parse_assignments(["ml-karte=1"]) == {"ml-karte": 1}
    with pytest.raises(pool.PoolFormatError):
        pool.parse_assignments(["Bau Groß=1"])


def test_migration_2_to_3_derives_the_kind(workstation_facts: HostFacts) -> None:
    current = profile_io.to_json(renamed(workstation_facts))
    old = json.loads(json.dumps(current))
    old["schema"] = "auditcore-runner/profil/2"
    for entry in old["klassen"].values():
        del entry["art"]
    old["klassen"]["gpu-8gb"] = {**old["klassen"]["bau"], "vram_mb": 0}  # former GPU name without cards
    data, applied = profile_io.migrate(old)
    assert applied == [2]
    kinds = {name: entry["art"] for name, entry in data["klassen"].items()}  # type: ignore[union-attr]
    assert kinds == {"bau": "cpu", "ml-karte": "gpu", "gpu-8gb": "gpu"}


def test_schema_and_examples_carry_the_kind(workstation_facts: HostFacts) -> None:
    schema = json.loads(files("auditcore_runner").joinpath("data", "schemas", "profil.schema.json").read_text())
    jsonschema.validate(profile_io.to_json(renamed(workstation_facts)), schema)
    example = json.loads(files("auditcore_runner").joinpath("data", "beispiele", "workstation-2gpu.json").read_text())
    assert example["schema"] == "auditcore-runner/profil/3"
    assert {n: c["art"] for n, c in example["klassen"].items()} == {"cpu-gross": "cpu", "gpu-16gb": "gpu"}


def test_runner_class_default_kind_is_cpu() -> None:
    assert not RunnerClass(True, 1, 1, 1, ("self-hosted",)).is_gpu


def test_auth_order_app_then_token_then_gh(tmp_path: Path, workstation_facts: HostFacts) -> None:
    from auditcore_runner.auth_setup import detect_auth

    auth, reason = detect_auth(tmp_path)
    assert auth.kind == "gh" and "Einzelrechner" in reason
    (tmp_path / "github-token").write_text("geheim")
    auth, _ = detect_auth(tmp_path)
    assert auth.kind == "pat" and auth.token_file.endswith("github-token")
    (tmp_path / "github-app.json").write_text('{"app_id": 1, "installation_id": 2, "schluessel_datei": "~/app.pem"}')
    auth, reason = detect_auth(tmp_path)
    assert (auth.kind, auth.app_id, auth.installation_id, auth.app_key_file) == ("app", 1, 2, "~/app.pem")
    assert "empfohlen" in reason and "geheim" not in reason
    (tmp_path / "github-app.json").write_text('{"app_id": "x"}')
    assert detect_auth(tmp_path)[0].kind == "pat"


def test_proposal_uses_configured_app(workstation_facts: HostFacts) -> None:
    from auditcore_runner.profile import config_dir

    config_dir().mkdir(parents=True)
    (config_dir() / "github-app.json").write_text('{"app_id": 7, "installation_id": 8, "schluessel_datei": "~/k.pem"}')
    profile = propose(workstation_facts, "owner/repo")
    assert profile.auth.kind == "app" and validate(profile, workstation_facts) == []
