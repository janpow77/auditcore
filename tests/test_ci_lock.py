"""requirements/ci.in lists exactly the third-party requirements of all packages."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ci_lock", ROOT / "scripts/ci_lock.py")
assert SPEC is not None and SPEC.loader is not None
ci_lock = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ci_lock)


def test_ci_input_is_current():
    assert ci_lock.main(["--check"]) == 0, "run: python scripts/ci_lock.py"


def test_internal_packages_are_excluded(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\ndependencies = ["auditcore_common==0.2.0", "httpx>=0.24"]\n'
        '[project.optional-dependencies]\ndev = ["auditcore[quality]", "pytest>=8"]\n'
    )
    assert ci_lock.render_input(tmp_path).splitlines()[1:] == ["httpx>=0.24", "pytest>=8"]


def test_lock_pins_every_input_name():
    lock = (ROOT / "requirements/ci.lock").read_text().lower()
    names = {
        ci_lock.NAME.match(line).group(1).lower().replace("_", "-")
        for line in (ROOT / "requirements/ci.in").read_text().splitlines()
        if line and not line.startswith("#")
    }
    missing = {name for name in names if f"\n{name}==" not in lock}
    assert not missing
