"""Accelerator selection of scripts/regulierung_package_test.py (KVM or TCG)."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "regulierung_package_test.py"
_SPEC = importlib.util.spec_from_file_location("regulierung_package_test", _SCRIPT)
assert _SPEC and _SPEC.loader
modul = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(modul)


def test_tcg_requested_never_uses_kvm(tmp_path: Path) -> None:
    assert modul.resolve_accelerator("tcg", tmp_path / "kvm") == "tcg"


def test_auto_falls_back_to_tcg_without_device(tmp_path: Path) -> None:
    assert modul.resolve_accelerator("auto", tmp_path / "kvm") == "tcg"


def test_kvm_requested_without_device_fails(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not accessible"):
        modul.resolve_accelerator("kvm", tmp_path / "kvm")


def test_regular_file_is_no_kvm_device(tmp_path: Path) -> None:
    falsch = tmp_path / "kvm"
    falsch.write_text("")
    assert modul.kvm_usable(falsch) is False


def test_tcg_arguments_keep_cpu_max() -> None:
    docker, qemu = modul.accelerator_arguments("tcg")
    assert docker == []
    assert qemu == ["-accel", "tcg", "-cpu", "max"]


def test_kvm_arguments_pass_device_and_group(tmp_path: Path) -> None:
    geraet = tmp_path / "kvm"
    geraet.write_text("")
    docker, qemu = modul.accelerator_arguments("kvm", geraet)
    assert docker == ["--device", str(geraet), "--group-add", str(os.stat(geraet).st_gid)]
    assert qemu == ["-accel", "kvm", "-cpu", "host"]


def test_dockerfile_entrypoint_has_no_fixed_accelerator() -> None:
    entrypoint = next(z for z in modul.DOCKERFILE.splitlines() if z.startswith("ENTRYPOINT"))
    assert "-accel" not in entrypoint and "-cpu" not in entrypoint
