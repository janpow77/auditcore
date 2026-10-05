"""Etappenplan, Gerüsttypen und Fakes."""

from __future__ import annotations

from pathlib import Path

import pytest

import auditcore_officebank.project as project
from auditcore_officebank import STAGES, StageNotImplemented, require, stage_of
from auditcore_officebank.acceptance import Tolerances
from auditcore_officebank.builder import BuildInput
from auditcore_officebank.delivery import PackageSpec
from auditcore_officebank.gates import GATE_ORDER, NATIVE_COMPILE_NOT_RUN
from auditcore_officebank.mssql import MssqlService
from auditcore_officebank.office import ModuleSet
from auditcore_officebank.testing import FakeGuest
from auditcore_officebank.vm import GuestBackend, GuestResult, VmState


def test_every_group_belongs_to_exactly_one_stage() -> None:
    groups = [group for stage in STAGES for group in stage.groups]
    assert len(groups) == len(set(groups))
    assert [stage.number for stage in STAGES] == list(range(7))


def test_require_and_stage_of() -> None:
    require("konfig")
    with pytest.raises(StageNotImplemented) as caught:
        require("vm")
    assert (caught.value.group, caught.value.stage) == ("vm", 2)
    with pytest.raises(KeyError):
        stage_of("unbekannt")


def test_fake_guest_records_and_replays() -> None:
    planned = GuestResult(1, "Fehler", 0.5, "job-1")
    guest: GuestBackend = FakeGuest.with_results([planned])
    assert guest.exec_system("Get-Date", 10) == planned
    assert guest.exec_system("Get-Date", 10).exit_code == 0
    guest.type_scancodes([0x1E, 0x1C])
    assert guest.status() is VmState.RUNNING
    assert isinstance(guest, FakeGuest)
    assert guest.scripts == ["Get-Date", "Get-Date"]
    assert guest.typed == [0x1E, 0x1C]


def test_skeleton_types() -> None:
    assert Tolerances().amount == 0.005
    assert BuildInput("src/modA.bas", "0" * 64, "module").kind == "module"
    spec = PackageSpec("Demo", "1.0", "20261005", include=("src/**",))
    assert spec.file_stem == "20261005_Demo_1.0"
    assert MssqlService("demo", "192.0.2.1", 1433, Path("d"), Path("b")).edition == "Developer"
    assert ModuleSet(("modA",), Path("src")).encoding == "ascii"
    assert GATE_ORDER[0] == "ascii"
    assert NATIVE_COMPILE_NOT_RUN == "not_run"


def test_project_subpackage_is_documented() -> None:
    assert project.__doc__ and "Etappe 6" in project.__doc__
