"""Package READMEs follow docs/bibliotheken/readme-vorlage.md.

For every package below ``packages/`` and ``packages-js/`` that is not listed
in ``docs/bibliotheken/readme-offen.json``:

* all mandatory sections exist in template order and satisfy the content rules
  of ``scripts/docs/readme_check.py``;
* the Python quick start runs (``scripts/docs/readme_snippets.py``, doctest-like);
* the generated API overview (Python) and the package catalog are current.

The npm quick starts are type-checked (and ``ts run`` blocks executed) in the
``js-packages`` workflow by ``scripts/js/check-readme-snippets.mjs``, which also
compares the npm API overview. Listed packages must still fail the check: a
package that already conforms has to be removed from the list (ratchet).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "docs"))

import api_overview  # noqa: E402
import catalog  # noqa: E402
import readme_check  # noqa: E402

PACKAGES = readme_check.all_packages(ROOT)
PENDING = readme_check.pending(ROOT)
PYTHON_PACKAGES = [p for p in PACKAGES if (p / "pyproject.toml").is_file()]


def _id(path: Path) -> str:
    return path.name


def test_pending_list_names_existing_packages() -> None:
    known = {p.name for p in PACKAGES}
    unknown = sorted(PENDING - known)
    assert not unknown, f"readme-offen.json nennt unbekannte Pakete: {unknown}"


@pytest.mark.parametrize("package_dir", PACKAGES, ids=_id)
def test_readme_follows_template(package_dir: Path) -> None:
    problems = readme_check.check(package_dir)
    if package_dir.name in PENDING:
        assert problems, (
            f"{package_dir.name} erfüllt die Vorlage – aus "
            "docs/bibliotheken/readme-offen.json entfernen"
        )
        return
    assert not problems, "\n".join(
        [f"{package_dir.name}/README.md entspricht nicht der Vorlage "
         "(docs/bibliotheken/readme-vorlage.md):", *problems]
    )


@pytest.mark.parametrize("package_dir", PYTHON_PACKAGES, ids=_id)
def test_python_quick_start_runs(package_dir: Path) -> None:
    if package_dir.name in PENDING:
        pytest.skip("README noch nicht nach Vorlage überarbeitet (readme-offen.json)")
    sources = [str(p) for p in sorted(ROOT.glob("packages/*/src"))]
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(sources)}
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts/docs/readme_snippets.py"),
         str(package_dir / "README.md")],
        cwd=package_dir, env=env, capture_output=True, text=True, timeout=300, check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_python_api_overviews_are_current() -> None:
    problems = api_overview.run(PYTHON_PACKAGES, write=False, skip=PENDING)
    assert not problems, "\n".join(problems)


def test_package_catalog_is_current() -> None:
    assert catalog.main(["--check"]) == 0, "`python scripts/docs/catalog.py --write` ausführen"
