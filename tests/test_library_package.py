"""Verify real Debian payloads and reject malicious or ambiguous library wheels."""

import base64
import csv
import hashlib
import io
import json
import zipfile

import pytest

from auditcore.tools.common import run
from auditcore.tools.deployer.library import _wheel_payload, build_library_deb


def make_wheel(tmp_path, *, changes=None, requirements=(), version="1.2.3"):
    package = "auditcore_dummygenerator"
    info = f"{package}-{version}.dist-info"
    payload = {
        f"{package}/__init__.py": b'"""Synthetic packaging fixture, no domain implementation."""\n',
        f"{info}/METADATA": (
            "Metadata-Version: 2.4\nName: auditcore-dummygenerator\n"
            f"Version: {version}\nRequires-Python: >=3.11\nLicense-Expression: MIT\n"
            + "".join(f"Requires-Dist: {r}\n" for r in requirements)
        ).encode(),
        f"{info}/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        f"{info}/licenses/LICENSE": b"MIT synthetic fixture license\n",
    }
    payload.update(changes or {})
    record = io.StringIO()
    writer = csv.writer(record)
    for name, content in payload.items():
        encoded = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=")
        writer.writerow((name, f"sha256={encoded.decode()}", len(content)))
    writer.writerow((f"{info}/RECORD", "", ""))
    payload[f"{info}/RECORD"] = record.getvalue().encode()
    wheel = tmp_path / f"{package}-{version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        for name, content in payload.items():
            archive.writestr(name, content)
    return wheel


def build(wheel, output, **kwargs):
    return build_library_deb(
        wheel,
        output,
        source_date_epoch=1700000000,
        maintainer="Packaging Test <packaging@example.invalid>",
        **kwargs,
    )


def test_domain_distribution_real_deb_and_reproducibility(tmp_path):
    wheel = make_wheel(tmp_path)
    first = build(wheel, tmp_path / "first")
    second = build(wheel, tmp_path / "second")
    assert first["package_sha256"] == second["package_sha256"]
    assert first["distribution"] == "auditcore-dummygenerator"
    assert first["artifact_scope"] == "PYTHON_LIBRARY"
    assert first["installation_test"] == "NOT_EXECUTED"
    assert first["application_release_approval"] == "NOT_APPLICABLE_WITH_REASON"
    control = run(["dpkg-deb", "--field", first["package"]])
    assert "Package: python3-auditcore-dummygenerator" in control
    assert "Depends: python3 (>= 3.11)" in control
    root = tmp_path / "unpacked"
    run(["dpkg-deb", "--raw-extract", first["package"], str(root)])
    assert (root / "usr/lib/python3/dist-packages/auditcore_dummygenerator/__init__.py").is_file()
    for name in ("postinst", "prerm"):
        content = (root / "DEBIAN" / name).read_text()
        assert not any(token in content for token in ("pip", "curl", "wget", "npm"))
    assert "py3clean -p python3-auditcore-dummygenerator" in (root / "DEBIAN/prerm").read_text()
    assert not list(root.rglob("RECORD"))
    assert (root / "usr/share/doc/python3-auditcore-dummygenerator/copyright").is_file()


def test_packaging_revision_preserves_upstream_wheel(tmp_path):
    wheel = make_wheel(tmp_path)
    original = build(wheel, tmp_path / "debs")
    upgrade = build(wheel, tmp_path / "debs", debian_revision=2)
    assert original["wheel_sha256"] == upgrade["wheel_sha256"]
    assert original["version"] == upgrade["version"] == "1.2.3"
    assert upgrade["debian_version"] == "1.2.3-2"
    assert run(["dpkg-deb", "--field", upgrade["package"], "Version"]).strip() == "1.2.3-2"


@pytest.mark.parametrize("revision", [0, -1, True, "1\nInjected: yes"])
def test_reject_invalid_packaging_revision(tmp_path, revision):
    with pytest.raises(ValueError, match="positive integer"):
        build(make_wheel(tmp_path), tmp_path / "debs", debian_revision=revision)


@pytest.mark.parametrize(
    "name",
    [
        "../escape.py",
        "/etc/escape.py",
        "auditcore_dummygenerator/../../escape.py",
        "auditcore_dummygenerator/./escape.py",
        "foreign/__init__.py",
        "auditcore_dummygenerator/startup.pth",
        "auditcore_dummygenerator/native.so",
    ],
)
def test_reject_unsafe_or_foreign_payload(tmp_path, name):
    wheel = make_wheel(tmp_path, changes={name: b"payload"})
    with pytest.raises(ValueError, match="Unsafe"):
        _wheel_payload(wheel)


def test_reject_tampered_record_content(tmp_path):
    wheel = make_wheel(tmp_path)
    with zipfile.ZipFile(wheel) as archive:
        payload = {name: archive.read(name) for name in archive.namelist()}
    payload["auditcore_dummygenerator/__init__.py"] = b"tampered"
    with zipfile.ZipFile(wheel, "w") as archive:
        for name, content in payload.items():
            archive.writestr(name, content)
    with pytest.raises(ValueError, match="digest mismatch"):
        _wheel_payload(wheel)


@pytest.mark.parametrize("version", ["1.2.3rc1", "1.2.3+local", "1.2.3-evil"])
def test_reject_unmapped_debian_versions(tmp_path, version):
    wheel = make_wheel(tmp_path, version=version)
    with pytest.raises(ValueError, match="stable-version"):
        _wheel_payload(wheel)


def test_reject_version_metadata_mismatch(tmp_path):
    wheel = make_wheel(tmp_path)
    wrong = tmp_path / wheel.name.replace("1.2.3", "9.9.9")
    wheel.rename(wrong)
    with pytest.raises(ValueError):
        _wheel_payload(wrong)


def test_required_dependencies_need_exact_mapping_and_extras_are_explicit(tmp_path):
    wheel = make_wheel(tmp_path, requirements=("requests>=2.30", 'pytest>=8; extra == "test"'))
    with pytest.raises(ValueError, match="exact Debian dependency mapping"):
        build(wheel, tmp_path / "rejected")
    with pytest.raises(ValueError, match="Invalid Debian dependency"):
        build(wheel, tmp_path / "injected", dependency_mapping={"requests>=2.30": "bad\nField: x"})
    result = build(
        wheel,
        tmp_path / "valid",
        dependency_mapping={
            "requests>=2.30": "python3-requests (>= 2.30)",
        },
    )
    assert result["optional_requirements_not_bundled"] == ('pytest>=8; extra == "test"',)
    assert "python3-requests (>= 2.30)" in run(["dpkg-deb", "--field", result["package"]])
    manifest = next((tmp_path / "valid").glob("*_manifest.json"))
    assert json.loads(manifest.read_text())["dependency_mapping"] == {
        "requests>=2.30": "python3-requests (>= 2.30)",
    }


def test_reject_maintainer_injection_before_build(tmp_path):
    wheel = make_wheel(tmp_path)
    with pytest.raises(ValueError, match="Maintainer"):
        build_library_deb(
            wheel,
            tmp_path / "bad",
            source_date_epoch=1,
            maintainer="Bad\nDepends: injected <test@example.invalid>",
        )


def test_reject_console_script_collision_with_platform(tmp_path):
    wheel = make_wheel(
        tmp_path,
        changes={
            "auditcore_dummygenerator-1.2.3.dist-info/entry_points.txt": (
                b"[console_scripts]\nauditcore-quality = auditcore_dummygenerator:main\n"
            ),
        },
    )
    with pytest.raises(ValueError, match="belong to its distribution"):
        _wheel_payload(wheel)


def test_domain_cli_uses_system_python(tmp_path):
    wheel = make_wheel(
        tmp_path,
        changes={
            "auditcore_dummygenerator-1.2.3.dist-info/entry_points.txt": (
                b"[console_scripts]\nauditcore-dummygenerator = auditcore_dummygenerator:main\n"
            ),
            "auditcore_dummygenerator/__init__.py": b"def main():\n    return 0\n",
        },
    )
    result = build(wheel, tmp_path / "dist")
    root = tmp_path / "unpacked"
    run(["dpkg-deb", "--extract", result["package"], str(root)])
    script = root / "usr/bin/auditcore-dummygenerator"
    assert script.read_text().startswith("#!/usr/bin/python3\n")
    assert script.stat().st_mode & 0o111


def test_reject_record_membership_and_malformed_rows(tmp_path):
    wheel = make_wheel(tmp_path)
    with zipfile.ZipFile(wheel) as archive:
        payload = {name: archive.read(name) for name in archive.namelist()}
    for record in (b"\n", b"unknown,,\n"):
        payload["auditcore_dummygenerator-1.2.3.dist-info/RECORD"] = record
        with zipfile.ZipFile(wheel, "w") as archive:
            for name, content in payload.items():
                archive.writestr(name, content)
        with pytest.raises(ValueError, match="RECORD"):
            _wheel_payload(wheel)


def test_unknown_license_requires_explicit_local_test_mode(tmp_path):
    metadata = (
        b"Metadata-Version: 2.4\nName: auditcore-dummygenerator\nVersion: 1.2.3\n"
        b"Requires-Python: >=3.11\nLicense-File: NOTICE\n"
    )
    wheel = make_wheel(
        tmp_path,
        changes={
            "auditcore_dummygenerator-1.2.3.dist-info/METADATA": metadata,
            "auditcore_dummygenerator-1.2.3.dist-info/licenses/NOTICE": b"No license grant.\n",
        },
    )
    with pytest.raises(ValueError, match="License review required"):
        build(wheel, tmp_path / "blocked")
    result = build(wheel, tmp_path / "test-only", allow_unreviewed_license=True)
    assert result["license_expression"] == "UNKNOWN"
    assert result["license_status"] == "REVIEW_REQUIRED"
    assert result["publication_status"] == "BLOCKED"
    assert result["release_authorization"] == "REVIEW_REQUIRED"


@pytest.mark.parametrize(
    "requirement",
    [
        "requests @ https://unapproved.invalid/requests.whl",
        "--extra-index-url bad",
    ],
)
def test_direct_dependency_urls_and_options_are_rejected(tmp_path, requirement):
    wheel = make_wheel(tmp_path, requirements=(requirement,))
    with pytest.raises(ValueError, match="dependency"):
        _wheel_payload(wheel)


def test_optional_renderer_mapping_is_suggested_without_forcing_runtime(tmp_path):
    requirement = 'reportlab>=4; extra == "pdf"'
    wheel = make_wheel(tmp_path, requirements=(requirement,))
    result = build(
        wheel,
        tmp_path / "optional",
        optional_dependency_mapping={requirement: "python3-reportlab (>= 3.6.12-1+deb12u1)"},
    )
    control = run(["dpkg-deb", "--field", result["package"]])
    assert "Suggests: python3-reportlab (>= 3.6.12-1+deb12u1)" in control
    assert result["depends"] == ["python3 (>= 3.11)"]
    assert result["suggests"] == ["python3-reportlab (>= 3.6.12-1+deb12u1)"]


@pytest.mark.parametrize(
    "mapping",
    [
        {"unrelated": "python3-reportlab"},
        {'reportlab>=4; extra == "pdf"': "python3-reportlab\nDepends: injected"},
        ["python3-reportlab"],
    ],
)
def test_reject_undeclared_or_injected_optional_dependencies(tmp_path, mapping):
    wheel = make_wheel(tmp_path, requirements=('reportlab>=4; extra == "pdf"',))
    with pytest.raises(ValueError):
        build(wheel, tmp_path / "rejected", optional_dependency_mapping=mapping)
