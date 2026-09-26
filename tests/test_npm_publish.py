"""npm publication of release tarballs: verification, order, idempotency (synthetic)."""

import importlib.util
import io
import json
import tarfile
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "npm_publish", Path(__file__).resolve().parents[1] / "scripts/npm_publish.py"
)
assert SPEC is not None and SPEC.loader is not None
npm_publish = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(npm_publish)

REPO = {"type": "git", "url": "git+https://github.com/janpow77/auditcore.git"}


def tarball(package, version, **extra):
    manifest = {"name": package, "version": version, "license": "MIT", "repository": REPO, **extra}
    body = json.dumps(manifest).encode()
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as archive:
        info = tarfile.TarInfo("package/package.json")
        info.size = len(body)
        archive.addfile(info, io.BytesIO(body))
    return stream.getvalue()


def release(tmp_path, packages, tag="v0.4.2"):
    """Write tarballs, npm-packages.json and SHA256SUMS like prepare_library_release.py."""
    entries = []
    for name, version, requirements, data in packages:
        file = name.removeprefix("@").replace("/", "-") + f"-{version}.tgz"
        (tmp_path / file).write_bytes(data)
        entries.append(
            {
                "name": name,
                "version": version,
                "file": file,
                "sha256": npm_publish.sha256(data),
                "size": len(data),
                "integrity": npm_publish.npm_integrity(data),
                "internal_requirements": requirements,
            }
        )
    manifest = {"release_version": tag.removeprefix("v"), "packages": entries}
    (tmp_path / "npm-packages.json").write_text(json.dumps(manifest))
    names = [entry["file"] for entry in entries] + ["npm-packages.json"]
    (tmp_path / "SHA256SUMS").write_text(
        "".join(f"{npm_publish.sha256((tmp_path / n).read_bytes())}  {n}\n" for n in names)
    )
    return entries


def standard(tmp_path):
    return release(
        tmp_path,
        [
            (
                "@auditcore/ui",
                "0.3.0",
                {"@auditcore/common": "0.1.0", "@auditcore/ui-core": "0.1.0"},
                tarball("@auditcore/ui", "0.3.0"),
            ),
            (
                "@auditcore/ui-core",
                "0.1.0",
                {"@auditcore/common": "0.1.0"},
                tarball("@auditcore/ui-core", "0.1.0"),
            ),
            ("@auditcore/common", "0.1.0", {}, tarball("@auditcore/common", "0.1.0")),
        ],
    )


def test_order_puts_dependencies_first(tmp_path):
    standard(tmp_path)
    order = npm_publish.publish_order(npm_publish.load_release(tmp_path, "v0.4.2"))
    assert [entry["name"] for entry in order] == [
        "@auditcore/common",
        "@auditcore/ui-core",
        "@auditcore/ui",
    ]


def test_cycle_is_rejected():
    packages = [
        {"name": "@auditcore/a", "internal_requirements": {"@auditcore/b": "1.0.0"}},
        {"name": "@auditcore/b", "internal_requirements": {"@auditcore/a": "1.0.0"}},
    ]
    with pytest.raises(npm_publish.PublishError, match="cycle"):
        npm_publish.publish_order(packages)


@pytest.mark.parametrize(
    ("tamper", "message"),
    [
        (lambda p: (p / "auditcore-common-0.1.0.tgz").write_bytes(b"x"), "SHA-256"),
        (lambda p: (p / "SHA256SUMS").write_text(""), "not covered"),
        (lambda p: (p / "auditcore-common-0.1.0.tgz").unlink(), "missing"),
    ],
)
def test_tampered_assets_are_rejected(tmp_path, tamper, message):
    standard(tmp_path)
    tamper(tmp_path)
    with pytest.raises(npm_publish.PublishError, match=message):
        npm_publish.load_release(tmp_path, "v0.4.2")


def test_manifest_of_another_release_is_rejected(tmp_path):
    standard(tmp_path)
    with pytest.raises(npm_publish.PublishError, match="another release"):
        npm_publish.load_release(tmp_path, "v0.4.3")


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        ({"repository": "https://github.com/someone/else"}, "repository"),
        ({"private": True}, "public MIT"),
        ({"name": "@auditcore/other"}, "content"),
    ],
)
def test_tarball_content_is_checked(tmp_path, extra, message):
    release(
        tmp_path,
        [("@auditcore/common", "0.1.0", {}, tarball("@auditcore/common", "0.1.0", **extra))],
    )
    with pytest.raises(npm_publish.PublishError, match=message):
        npm_publish.load_release(tmp_path, "v0.4.2")


@pytest.mark.parametrize(
    ("version", "latest", "tag"),
    [
        ("0.2.0", None, "latest"),
        ("0.2.0", "0.1.9", "latest"),
        ("0.2.0", "0.10.0", "previous"),
        ("0.3.0-rc.1", "0.2.0", "next"),
    ],
)
def test_dist_tag(version, latest, tag):
    assert npm_publish.dist_tag(version, latest) == tag


def test_run_skips_published_and_publishes_missing(tmp_path, monkeypatch):
    entries = {entry["name"]: entry for entry in standard(tmp_path)}
    registry = {"@auditcore/common@0.1.0": entries["@auditcore/common"]["integrity"]}
    published = []
    monkeypatch.setattr(npm_publish, "npm_view", lambda name, field: registry.get(name))
    monkeypatch.setattr(
        npm_publish, "npm_publish", lambda assets, step: published.append(step["name"])
    )
    steps = npm_publish.run(tmp_path, "v0.4.2", publish=True)
    assert [(s["name"], s["action"]) for s in steps] == [
        ("@auditcore/common", "skip"),
        ("@auditcore/ui-core", "published"),
        ("@auditcore/ui", "published"),
    ]
    assert published == ["@auditcore/ui-core", "@auditcore/ui"]


def test_plan_only_never_publishes(tmp_path, monkeypatch):
    standard(tmp_path)
    monkeypatch.setattr(npm_publish, "npm_view", lambda name, field: None)
    monkeypatch.setattr(npm_publish, "npm_publish", lambda *_: pytest.fail("published"))
    assert npm_publish.main(["--assets", str(tmp_path), "--tag", "v0.4.2"]) == 0


def test_same_version_with_other_content_is_a_conflict(tmp_path, monkeypatch):
    standard(tmp_path)
    registry = {"@auditcore/common@0.1.0": "sha512-other"}
    published = []
    monkeypatch.setattr(npm_publish, "npm_view", lambda name, field: registry.get(name))
    monkeypatch.setattr(
        npm_publish, "npm_publish", lambda assets, step: published.append(step["name"])
    )
    report = tmp_path / "report.json"
    args = ["--assets", str(tmp_path), "--tag", "v0.4.2", "--publish", "--report", str(report)]
    assert npm_publish.main(args) == 1
    steps = json.loads(report.read_text())["steps"]
    assert steps[0]["action"] == "conflict"
    assert published == ["@auditcore/ui-core", "@auditcore/ui"]
    assert npm_publish.main(args[:4]) == 0  # the plan only warns


def test_npm_view_distinguishes_missing_from_failure(monkeypatch):
    class Result:
        def __init__(self, returncode, stdout="", stderr=""):
            self.returncode, self.stdout, self.stderr = returncode, stdout, stderr

    outcomes = iter(
        [
            Result(1, stderr="npm error code E404"),
            Result(0, '"sha512-x"'),
            Result(1, stderr="ETIMEDOUT"),
        ]
    )
    monkeypatch.setattr(npm_publish.subprocess, "run", lambda *a, **k: next(outcomes))
    assert npm_publish.npm_view("@auditcore/common@0.1.0", "dist.integrity") is None
    assert npm_publish.npm_view("@auditcore/common@0.1.0", "dist.integrity") == "sha512-x"
    with pytest.raises(npm_publish.PublishError, match="ETIMEDOUT"):
        npm_publish.npm_view("@auditcore/common", "dist-tags.latest")


@pytest.mark.parametrize(
    "manifest",
    sorted((Path(__file__).resolve().parents[1] / "packages-js").glob("*/package.json")),
    ids=lambda path: path.parent.name,
)
def test_workspace_metadata_allows_public_provenance(manifest):
    """Tarballs are packed from these files; npm needs the fields at publish time."""
    data = json.loads(manifest.read_text())
    assert data["name"].startswith(npm_publish.SCOPE)
    assert data["license"] == "MIT" and not data.get("private")
    assert npm_publish._repository_url(data) == npm_publish.REPOSITORY
    assert data["repository"]["directory"] == f"packages-js/{manifest.parent.name}"
    assert data["publishConfig"]["access"] == "public"
    assert {"dist", "LICENSE", "README.md"} <= set(data["files"])
