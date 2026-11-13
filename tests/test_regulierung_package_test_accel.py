"""Accelerator selection of scripts/regulierung_package_test.py (KVM or TCG)."""

from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "regulierung_package_test.py"
_SPEC = importlib.util.spec_from_file_location("regulierung_package_test", _SCRIPT)
assert _SPEC and _SPEC.loader
modul = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(modul)


def _ja() -> bool:
    return True


def _nein() -> bool:
    return False


#: /dev/null is a world read-writable character device, like a usable /dev/kvm.
_ZEICHENGERAET = Path("/dev/null")


def test_tcg_requested_never_uses_kvm(tmp_path: Path) -> None:
    assert modul.resolve_accelerator("tcg", _ZEICHENGERAET, _ja) == "tcg"


def test_usable_character_device_selects_kvm() -> None:
    assert modul.kvm_usable(_ZEICHENGERAET) is True
    assert modul.resolve_accelerator("auto", _ZEICHENGERAET, _ja) == "kvm"
    assert modul.resolve_accelerator("kvm", _ZEICHENGERAET, _ja) == "kvm"


def test_auto_falls_back_when_docker_cannot_pass_the_device() -> None:
    assert modul.resolve_accelerator("auto", _ZEICHENGERAET, _nein) == "tcg"
    with pytest.raises(ValueError, match="rootless/userns or remote"):
        modul.resolve_accelerator("kvm", _ZEICHENGERAET, _nein)


def test_device_without_group_access_is_not_usable(monkeypatch) -> None:
    class Ergebnis:
        st_mode = stat.S_IFCHR | 0o600

    monkeypatch.setattr(Path, "stat", lambda self, **kw: Ergebnis())
    monkeypatch.setattr(modul.os, "access", lambda *a: True)
    assert modul.kvm_usable(Path("/dev/kvm")) is False


@pytest.mark.parametrize(
    ("docker_host", "optionen", "erwartet"),
    [
        ("", '["name=apparmor","name=seccomp,profile=builtin"]', True),
        ("unix:///var/run/docker.sock", "[]", True),
        ("", '["name=seccomp","name=rootless"]', False),
        ("", '["name=userns"]', False),
        ("tcp://andere-maschine:2376", "[]", False),
    ],
)
def test_docker_daemon_detection(monkeypatch, docker_host, optionen, erwartet) -> None:
    monkeypatch.setenv("DOCKER_HOST", docker_host)
    monkeypatch.setattr(
        modul.subprocess,
        "run",
        lambda *a, **kw: subprocess.CompletedProcess(a, 0, stdout=optionen),
    )
    assert modul.docker_passes_devices() is erwartet


def test_docker_info_failure_means_no_kvm(monkeypatch) -> None:
    monkeypatch.delenv("DOCKER_HOST", raising=False)

    def fehler(*a, **kw):
        raise subprocess.CalledProcessError(1, "docker")

    monkeypatch.setattr(modul.subprocess, "run", fehler)
    assert modul.docker_passes_devices() is False


def test_auto_falls_back_to_tcg_without_device(tmp_path: Path) -> None:
    assert modul.resolve_accelerator("auto", tmp_path / "kvm", _ja) == "tcg"


def test_kvm_requested_without_device_fails(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not usable"):
        modul.resolve_accelerator("kvm", tmp_path / "kvm", _ja)


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
    assert qemu == ["-accel", "kvm", "-cpu", "Westmere"]


def test_dockerfile_entrypoint_has_no_fixed_accelerator() -> None:
    entrypoint = next(z for z in modul.DOCKERFILE.splitlines() if z.startswith("ENTRYPOINT"))
    assert "-accel" not in entrypoint and "-cpu" not in entrypoint
