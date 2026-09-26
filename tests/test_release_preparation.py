"""Reject stale or incomplete optional-renderer release evidence (synthetic fixtures)."""

import importlib.util
import io
import json
import tarfile
import zipfile
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "release_preparation",
    Path(__file__).resolve().parents[1] / "scripts/prepare_library_release.py",
)
assert SPEC is not None and SPEC.loader is not None
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


def fixture_wheel(package, version, metadata=""):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr(
            f"{package}-{version}.dist-info/METADATA",
            f"Name: {package}\nVersion: {version}\n{metadata}",
        )
    return stream.getvalue()


def fixture_evidence(tmp_path):
    invoice = "auditcore_invoicegenerator-0.2.0-py3-none-any.whl"
    dummy = "auditcore_dummygenerator-0.1.0-py3-none-any.whl"
    assets = {
        invoice: fixture_wheel(
            "auditcore_invoicegenerator",
            "0.2.0",
            "Provides-Extra: pdf\nRequires-Dist: auditcore_dummygenerator==0.1.0\n"
            'Requires-Dist: reportlab>=4; extra == "pdf"\n',
        ),
        dummy: fixture_wheel("auditcore_dummygenerator", "0.1.0"),
    }
    hashes = {name: release.digest(data) for name, data in assets.items()}
    base = "https://github.com/janpow77/auditcore/releases/download/v0.2.0"
    filename = "requirements-auditcore_invoicegenerator-pdf.txt"
    text = (
        "--index-url https://pypi.org/simple\n--require-hashes\n"
        f"auditcore-invoicegenerator[pdf] @ {base}/{invoice} --hash=sha256:{hashes[invoice]}\n"
        f"auditcore-dummygenerator @ {base}/{dummy} --hash=sha256:{hashes[dummy]}\n"
        f"reportlab==5.0.1 --hash=sha256:{'a' * 64}\n"
    )
    (tmp_path / filename).write_text(text)
    checks = {}
    for name in [
        "apt-renderers",
        *[
            f"pdf-{stage}"
            for stage in (
                "install",
                "smoke",
                "independence",
                "pip-check",
                "remove",
                "locked-install",
                "locked-smoke",
            )
        ],
    ]:
        content = b"Synthetic evidence fixture; not an executed package test.\n"
        (tmp_path / f"{name}.log").write_bytes(content)
        checks[name] = {"status": "PASS", "exit_code": 0, "log_sha256": release.digest(content)}
    report = {
        "scope": "OPTIONAL_RENDERER_INSTALLATION",
        "status": "PASS",
        "release_version": "0.2.0",
        "checks": checks,
        "features": {
            "pdf": {
                "status": "PASS",
                "package": "auditcore_invoicegenerator",
                "version": "0.2.0",
                "wheel_hashes": hashes,
                "dependencies": {"reportlab": "5.0.1"},
                "requirements": filename,
                "requirements_sha256": release.digest(text.encode()),
            }
        },
    }
    return assets, report


def test_optional_release_accepts_exact_mixed_version_dependency_closure(tmp_path):
    assets, report = fixture_evidence(tmp_path)
    (tmp_path / "result.json").write_text(json.dumps(report))
    output = release.optional_assets(assets, tmp_path, "0.2.0")
    assert set(output) == {
        "requirements-auditcore_invoicegenerator-pdf.txt",
        "optional-renderer-verification.json",
    }


@pytest.mark.parametrize("change", ["empty", "missing_dependency", "version", "package", "url"])
def test_optional_release_rejects_stale_or_incomplete_bindings(tmp_path, change):
    assets, report = fixture_evidence(tmp_path)
    feature = report["features"]["pdf"]
    if change == "empty":
        feature["wheel_hashes"] = {}
    elif change == "missing_dependency":
        feature["wheel_hashes"].pop("auditcore_dummygenerator-0.1.0-py3-none-any.whl")
    elif change == "version":
        feature["version"] = "0.1.0"
    elif change == "package":
        feature["package"] = "auditcore_reporting"
    else:
        lock = tmp_path / feature["requirements"]
        lock.write_text(lock.read_text().replace("download/v0.2.0", "download/v0.1.0"))
        feature["requirements_sha256"] = release.digest(lock.read_bytes())
    (tmp_path / "result.json").write_text(json.dumps(report))
    with pytest.raises(ValueError):
        release.optional_assets(assets, tmp_path, "0.2.0")


def test_expected_sources_cover_every_completed_distribution():
    completed = {
        path.parent.name
        for path in (Path(__file__).resolve().parents[1] / "packages").glob("*/pyproject.toml")
    }
    assert completed == release.PACKAGES


@pytest.mark.parametrize("name", sorted(release.EXPECTED_SOURCES))
def test_real_packaged_provenance_passes_the_authorization_check(name):
    root = Path(__file__).resolve().parents[1] / "packages" / name / "src" / name
    release.check_extracted_authorization(name, json.loads((root / "provenance.json").read_text()))


def _extracted_provenance():
    return {
        "sources": [
            {
                "repository": "janpow77/flowstat",
                "commit": "d665ac221f50ba1f465b7337bdd4aa218d78ec8a",
            },
            {
                "repository": "janpow77/flowinvoice",
                "commit": "fb2d18568d2eaf64574d131ceae51a936b9aac02",
            },
        ],
        "rights": {
            "authorization": {
                "status": "USER_AUTHORIZED_MIT",
                "date": "2026-09-22",
                "confirmation": "die bibliotheken sollen mit sein, die anderen repos nicht",
            }
        },
    }


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p["rights"]["authorization"].pop("status"),
        lambda p: p["rights"]["authorization"].update(status="UNKNOWN"),
        lambda p: p["rights"]["authorization"].update(date="2026-09-21"),
        lambda p: p["rights"]["authorization"].pop("confirmation"),
        lambda p: p["sources"].append({"repository": "janpow77/regulierung", "commit": "a" * 40}),
        lambda p: p["sources"][0].update(commit="b" * 40),
        lambda p: p.pop("sources"),
    ],
)
def test_extracted_authorization_fails_closed(change):
    provenance = _extracted_provenance()
    release.check_extracted_authorization("auditcore_statistics", provenance)
    change(provenance)
    with pytest.raises(ValueError, match="authorization missing"):
        release.check_extracted_authorization("auditcore_statistics", provenance)


def test_same_named_extra_of_another_package_is_not_a_published_renderer():
    wheel = "auditcore_dataprotection-0.1.0-py3-none-any.whl"
    assets = {
        wheel: fixture_wheel(
            "auditcore_dataprotection",
            "0.1.0",
            "Provides-Extra: excel\nProvides-Extra: pdf\n"
            'Requires-Dist: openpyxl>=3.0.9; extra == "excel"\n',
        )
    }
    assert release.optional_assets(assets, None, "0.2.0") == {}
    assert release.RENDERER_OWNERS == {
        "pdf": "auditcore_invoicegenerator",
        "excel": "auditcore_reporting",
    }


def test_release_requires_passing_code_quality_gate():
    """No release assets without the executed code-quality ratchet (release blocker)."""
    assert "code-quality-gate" in release.REQUIRED_CHECKS


def _npm_tarball(directory, manifest, files=("dist/index.js",)):
    """Synthetic ``npm pack`` output (not an executed build)."""
    name = manifest["name"].removeprefix("@").replace("/", "-") + f"-{manifest['version']}.tgz"
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as archive:
        for member, content in [
            ("package/package.json", json.dumps(manifest).encode()),
            ("package/LICENSE", b"MIT License\n"),
            *[(f"package/{item}", b"export {}\n") for item in files],
        ]:
            info = tarfile.TarInfo(member)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
    data = stream.getvalue()
    (directory / name).write_bytes(data)
    entry = {
        "name": manifest["name"],
        "version": manifest["version"],
        "filename": name,
        "integrity": release.npm_integrity(data),
    }
    return {**manifest, "_directory": manifest["name"].split("/")[1]}, entry


def _npm_fixture(tmp_path):
    exports = {".": {"import": "./dist/index.js"}, "./package.json": "./package.json"}
    common = {"name": "@auditcore/common", "version": "0.1.0", "license": "MIT", "exports": exports}
    ui = {
        "name": "@auditcore/ui",
        "version": "0.2.0",
        "license": "MIT",
        "exports": exports,
        "dependencies": {"@auditcore/common": "0.1.0", "leaflet": "^1.9.4"},
        "peerDependencies": {"vue": "^3.5.0", "@auditcore/kanban-core": "^0.1.0"},
        "peerDependenciesMeta": {"@auditcore/kanban-core": {"optional": True}},
    }
    sources, report = {}, []
    for manifest in (common, ui):
        source, entry = _npm_tarball(tmp_path, manifest)
        sources[manifest["name"]] = source
        report.append(entry)
    return sources, report


def test_npm_tarballs_are_bound_with_integrity_and_install_closure(tmp_path):
    sources, report = _npm_fixture(tmp_path)
    assets = release.verify_npm_tarballs(sources, report, tmp_path, "0.4.2", "a" * 40)
    manifest = json.loads(assets[release.NPM_MANIFEST])
    assert manifest["registry_publication"] == "NOT_EXECUTED"
    ui = next(p for p in manifest["packages"] if p["name"] == "@auditcore/ui")
    data = assets["auditcore-ui-0.2.0.tgz"]
    assert ui["integrity"] == release.npm_integrity(data)
    assert ui["integrity"].startswith("sha512-")
    assert ui["sha256"] == release.digest(data)
    assert ui["install_closure"] == ["@auditcore/common", "@auditcore/ui"]
    base = "https://github.com/janpow77/auditcore/releases/download/v0.4.2"
    assert ui["package_json_dependencies"] == {
        "@auditcore/common": f"{base}/auditcore-common-0.1.0.tgz",
        "@auditcore/ui": f"{base}/auditcore-ui-0.2.0.tgz",
    }


@pytest.mark.parametrize(
    "change", ["missing_workspace", "integrity", "license", "private", "unresolved", "unbuilt"]
)
def test_npm_tarballs_fail_closed(tmp_path, change):
    sources, report = _npm_fixture(tmp_path)
    if change == "missing_workspace":
        report.pop()
    elif change == "integrity":
        report[0]["integrity"] = release.npm_integrity(b"other")
    elif change == "license":
        sources["@auditcore/common"]["license"] = "UNLICENSED"
    elif change == "private":
        sources["@auditcore/ui"]["private"] = True
    elif change == "unresolved":
        manifest = {k: v for k, v in sources["@auditcore/ui"].items() if k != "_directory"}
        manifest["dependencies"] = {"@auditcore/common": "^0.2.0"}
        sources["@auditcore/ui"], report[1] = _npm_tarball(tmp_path, manifest)
    else:
        manifest = {k: v for k, v in sources["@auditcore/common"].items() if k != "_directory"}
        sources["@auditcore/common"], report[0] = _npm_tarball(tmp_path, manifest, files=())
    with pytest.raises(ValueError):
        release.verify_npm_tarballs(sources, report, tmp_path, "0.4.2", "a" * 40)


@pytest.mark.parametrize(
    ("version", "spec", "expected"),
    [
        ("0.1.0", "0.1.0", True),
        ("0.1.1", "0.1.0", False),
        ("0.1.3", "^0.1.0", True),
        ("0.2.0", "^0.1.0", False),
        ("1.4.0", "^1.0.0", True),
        ("2.0.0", "^1.0.0", False),
    ],
)
def test_internal_npm_ranges(version, spec, expected):
    assert release._npm_version_satisfies(version, spec) is expected
