"""Optional fixtures of scripts/regulierung_package_test.py (seed and verify programs)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
_SPEC = importlib.util.spec_from_file_location(
    "regulierung_package_test", _SCRIPTS / "regulierung_package_test.py"
)
assert _SPEC and _SPEC.loader
modul = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(modul)


def test_without_fixtures_the_digest_is_absent():
    assert modul.fixtures_digest(None) is None


def test_digest_covers_names_and_contents(tmp_path: Path):
    (tmp_path / "seed.py").write_text("print('a')\n")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "data.json").write_text("{}")
    first = modul.fixtures_digest(tmp_path)
    assert first == modul.fixtures_digest(tmp_path)
    (tmp_path / "sub" / "data.json").write_text("[]")
    changed_content = modul.fixtures_digest(tmp_path)
    assert changed_content != first
    (tmp_path / "sub" / "data.json").rename(tmp_path / "sub" / "other.json")
    assert modul.fixtures_digest(tmp_path) != changed_content


def test_missing_fixture_directory_is_rejected(tmp_path: Path):
    with pytest.raises(SystemExit, match="not a directory"):
        modul.fixtures_digest(tmp_path / "missing")


def test_guest_image_always_has_a_fixture_directory():
    assert "COPY fixtures /auditcore-fixtures\n" in modul.DOCKERFILE


def test_guest_runs_seed_after_install_and_verify_after_upgrade_and_reinstall():
    guest = (_SCRIPTS / "regulierung_guest_test.py").read_text()
    seed = guest.index('checks["install_seed_application_data"]')
    sentinel = guest.index('sentinel.write_text("synthetic persistent application state')
    assert seed < sentinel
    assert 'if verify and phase in {"upgrade", "reinstall"}:' in guest
    assert 'checks[f"{phase}_verify_application_data"] = "PASS"' in guest


def test_symbolic_links_are_rejected(tmp_path: Path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.env").write_text("KEY=1")
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    (fixtures / "seed.py").write_text("")
    (fixtures / "shared").symlink_to(outside)
    with pytest.raises(SystemExit, match="symbolic links: shared"):
        modul.fixtures_digest(fixtures)
    (fixtures / "shared").unlink()
    (fixtures / "seed.py").rename(fixtures / "real.py")
    (fixtures / "seed.py").symlink_to(fixtures / "real.py")
    with pytest.raises(SystemExit, match="symbolic links: seed.py"):
        modul.fixtures_digest(fixtures)


def test_fixture_directory_itself_must_not_be_a_link(tmp_path: Path):
    real = tmp_path / "real"
    real.mkdir()
    (tmp_path / "link").symlink_to(real)
    with pytest.raises(SystemExit, match="not a directory"):
        modul.fixtures_digest(tmp_path / "link")


def test_guest_keeps_hook_output_on_failure_and_needs_seed_for_verify():
    guest = (_SCRIPTS / "regulierung_guest_test.py").read_text()
    body = guest[guest.index("def run_hook(") : guest.index("def request(")]
    assert body.index("report[key] =") < body.index("result.check_returncode()")
    assert "verify requires seed" in guest


def test_guest_hook_runner_is_not_shadowed_by_a_local_name():
    """Regression 18.11.2026: a loop variable named like the helper made it a list."""
    import ast

    tree = ast.parse((_SCRIPTS / "regulierung_guest_test.py").read_text())
    names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    }
    assert "run_hook" not in names


@pytest.mark.parametrize(
    ("configuration", "problem"),
    [
        ({}, None),
        ({"seed": ["python3", "/auditcore-fixtures/seed.py"]}, None),
        ({"seed": ["a"], "verify": ["b"]}, None),
        ({"seed": "python3 seed.py"}, "seed/verify must be non-empty argv lists"),
        ({"seed": []}, "seed/verify must be non-empty argv lists"),
        ({"seed": ["a", 1]}, "seed/verify must be non-empty argv lists"),
        ({"verify": ["b"]}, "verify requires seed: it compares against the seeded state"),
    ],
)
def test_hook_configuration_is_checked_on_the_host(configuration, problem):
    assert modul.hook_configuration_error(configuration) == problem


_GAST = importlib.util.spec_from_file_location(
    "regulierung_guest_test",
    Path(__file__).resolve().parents[1] / "scripts" / "regulierung_guest_test.py",
)
assert _GAST is not None and _GAST.loader is not None
gast = importlib.util.module_from_spec(_GAST)
_GAST.loader.exec_module(gast)


def test_hook_timeout_keeps_the_partial_output(monkeypatch):
    def zu_lang(*_args, **_kwargs):
        raise gast.subprocess.TimeoutExpired(["seed"], 900, output=b"halb fertig\n")

    monkeypatch.setattr(gast.subprocess, "run", zu_lang)
    report: dict = {}
    with pytest.raises(gast.subprocess.TimeoutExpired):
        gast.run_hook(report, "seed_output", ["seed"])
    assert report["seed_output"] == "halb fertig\n[timeout after 900 s]"
