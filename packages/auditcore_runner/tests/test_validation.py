from __future__ import annotations

from dataclasses import replace

from auditcore_runner.hardware import HostFacts
from auditcore_runner.profile import Auth, Network, Target, with_class
from auditcore_runner.propose import propose
from auditcore_runner.validation import validate


def fields(problems: list[object]) -> set[str]:
    return {p.field for p in problems}  # type: ignore[attr-defined]


def test_budget_over_machine(workstation_facts: HostFacts) -> None:
    profile = propose(workstation_facts, "owner/repo")
    big = replace(profile.classes["cpu-gross"], max_instances=10)
    problems = validate(with_class(profile, "cpu-gross", big), workstation_facts)
    assert any("CPUs zugesagt" in p.message for p in problems)
    assert any("GB zugesagt" in p.message for p in problems)


def test_labels_ranges_and_class_names(workstation_facts: HostFacts) -> None:
    profile = propose(workstation_facts, "owner/repo")
    broken = replace(profile.classes["cpu-gross"], labels=("linux", "bad label"), nice=25, cpu_shares=1)
    problems = validate(with_class(profile, "Gpu_99", broken), workstation_facts)
    names = fields(problems)
    assert {"klassen.Gpu_99", "klassen.Gpu_99.labels", "klassen.Gpu_99.nice", "klassen.Gpu_99.cpu_shares"} <= names


def test_target_and_auth(workstation_facts: HostFacts) -> None:
    profile = replace(propose(workstation_facts, "kaputt"), auth=Auth("app", app_key_file="relativ"))
    names = fields(validate(profile, workstation_facts))
    assert {"ziel.name", "auth", "auth.app_schluessel_datei"} <= names
    org = replace(profile, target=Target("org", "firma"), auth=Auth("gh"))
    assert any(p.field == "auth.art" and "Organisations" in p.message for p in validate(org, workstation_facts))


def test_gpu_rules(workstation_facts: HostFacts) -> None:
    profile = propose(workstation_facts, "owner/repo")
    one_card = replace(profile, gpus=(replace(profile.gpus[0], allowed=False), profile.gpus[1]))
    assert "klassen.gpu-16gb.max_instanzen" in fields(validate(one_card, workstation_facts))
    foreign = replace(profile, gpus=(replace(profile.gpus[0], uuid="GPU-fremd"), profile.gpus[1]))
    assert "gpus[0].uuid" in fields(validate(foreign, workstation_facts))


def test_network(workstation_facts: HostFacts) -> None:
    profile = replace(
        propose(workstation_facts, "owner/repo"),
        network=Network(subnet="8.8.8.0/24", bridge="viel-zu-lange-bruecke", enabled=False),
    )
    assert {"netz.subnetz", "netz.bruecke", "netz.sperre_pflicht"} <= fields(validate(profile, workstation_facts))
