"""Exercise installed-style packaging APIs with isolated technical packages and real pip."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from auditcore.tools.common import digest, run
from auditcore.tools.deployer.cli import main
from auditcore.tools.deployer.python_repository import build_pip_index, build_python_package


def package_source(root, name, *, dependencies=(), body="VALUE = 42\n"):
    root.mkdir()
    (root / "src" / name).mkdir(parents=True)
    (root / "src" / name / "__init__.py").write_text(body)
    (root / "LICENSE").write_text("MIT License\nCopyright 2026 Test Authors\n")
    (root / "pyproject.toml").write_text(
        '[build-system]\nrequires=["setuptools>=83", "wheel"]\n'
        'build-backend="setuptools.build_meta"\n'
        f'[project]\nname="{name}"\nversion="1.0.0"\nrequires-python=">=3.11"\n'
        f'license="MIT"\nlicense-files=["LICENSE"]\ndependencies={json.dumps(list(dependencies))}\n'
        '[tool.setuptools.packages.find]\nwhere=["src"]\n'
    )
    return root


@pytest.fixture(scope="module")
def built_packages(tmp_path_factory):
    root = tmp_path_factory.mktemp("technical-packages")
    base = package_source(root / "base", "auditcore_fixturebase")
    consumer = package_source(
        root / "consumer",
        "auditcore_fixtureconsumer",
        dependencies=("auditcore-fixturebase==1.0.0",),
        body="from auditcore_fixturebase import VALUE\nRESULT = VALUE + 1\n",
    )
    first = build_python_package(base, root / "base-dist", source_date_epoch=1700000000)
    second = build_python_package(consumer, root / "consumer-dist", source_date_epoch=1700000000)
    return root, first, second


def test_python_build_contains_matching_wheel_sdist_and_sbom(built_packages):
    root, first, _ = built_packages
    assert first["status"] == "PYTHON_ARTIFACTS_BUILT"
    assert first["wheel_sha256"] == digest(Path(first["wheel"]).read_bytes())
    assert first["sdist_sha256"] == digest(Path(first["sdist"]).read_bytes())
    assert first["sbom"]["status"] == "PASS"
    assert first["installation_test"] == "NOT_EXECUTED"
    assert not list((root / "base").rglob("*.egg-info"))
    assert first["publication"] == "NOT_EXECUTED"


def test_local_simple_index_resolves_requirements_and_imports_installed_packages(
    built_packages,
    tmp_path,
):
    _, first, second = built_packages
    result = build_pip_index([Path(first["wheel"]), Path(second["wheel"])], tmp_path / "index")
    python = tmp_path / "venv/bin/python"
    run([sys.executable, "-m", "venv", str(tmp_path / "venv")])
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(
        f"--index-url {result['index_url']}\n"
        f"auditcore-fixtureconsumer==1.0.0 --hash=sha256:{second['wheel_sha256']}\n"
        f"auditcore-fixturebase==1.0.0 --hash=sha256:{first['wheel_sha256']}\n"
    )
    environment = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("PIP_") and k not in {"PYTHONPATH", "PYTHONHOME"}
    }
    environment["PIP_CONFIG_FILE"] = os.devnull
    installed = subprocess.run(
        [
            str(python),
            "-I",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-cache-dir",
            "--only-binary=:all:",
            "--require-hashes",
            "-r",
            str(requirements),
        ],
        env=environment,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert installed.returncode == 0, installed.stderr
    proof = run(
        [
            str(python),
            "-I",
            "-c",
            "import auditcore_fixturebase as b, auditcore_fixtureconsumer as c; "
            "assert c.RESULT == 43; print(c.__file__); print(b.__file__)",
        ],
        tmp_path,
    )
    assert proof.count(str(tmp_path / "venv")) == 2
    assert "site-packages" in proof
    assert result["projects"] == ["auditcore-fixturebase", "auditcore-fixtureconsumer"]
    index = (tmp_path / "index/simple/auditcore-fixturebase/index.html").read_text()
    assert f"#sha256={first['wheel_sha256']}" in index


def test_index_rejects_collisions_and_nonempty_destination(built_packages, tmp_path):
    _, first, _ = built_packages
    wheel = Path(first["wheel"])
    with pytest.raises(ValueError, match="Duplicate"):
        build_pip_index([wheel, wheel], tmp_path / "duplicate")
    existing = tmp_path / "existing"
    existing.mkdir()
    (existing / "keep").write_text("existing release")
    with pytest.raises(ValueError, match="empty"):
        build_pip_index([wheel], existing)
    assert (existing / "keep").read_text() == "existing release"


def test_source_build_rejects_external_symlink(tmp_path):
    source = package_source(tmp_path / "source", "auditcore_fixture")
    (source / "outside").symlink_to("/etc/passwd")
    with pytest.raises(ValueError, match="symlink escapes"):
        build_python_package(source, tmp_path / "dist", source_date_epoch=1700000000)


def test_cli_builds_and_indexes_from_explicit_paths(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = package_source(tmp_path / "source", "auditcore_fixturecli")
    assert (
        main(
            [
                "build-python",
                str(source),
                "--output",
                str(tmp_path / "dist"),
                "--source-date-epoch",
                "1700000000",
            ]
        )
        == 0
    )
    report = json.loads(capsys.readouterr().out)
    assert report["distribution"] == "auditcore-fixturecli"
    assert main(["pip-index", report["wheel"], "--output", str(tmp_path / "index")]) == 0
    index = json.loads(capsys.readouterr().out)
    assert index["status"] == "LOCAL_INDEX_BUILT"
    assert (
        main(
            [
                "build-library",
                report["wheel"],
                "--output",
                str(tmp_path / "deb"),
                "--maintainer",
                "Packaging Test <packaging@example.invalid>",
                "--source-date-epoch",
                "1700000000",
            ]
        )
        == 0
    )
    package = json.loads(capsys.readouterr().out)
    assert Path(package["package"]).is_file()


def test_cli_malformed_dependency_mapping_reports_blocked(built_packages, tmp_path, capsys):
    _, first, _ = built_packages
    mapping = tmp_path / "mapping.json"
    mapping.write_text('["not", "an", "object"]')
    assert (
        main(
            [
                "build-library",
                first["wheel"],
                "--output",
                str(tmp_path / "deb"),
                "--maintainer",
                "Packaging Test <packaging@example.invalid>",
                "--source-date-epoch",
                "1700000000",
                "--dependency-mapping",
                str(mapping),
            ]
        )
        == 1
    )
    assert json.loads(capsys.readouterr().out)["status"] == "BLOCKED"
