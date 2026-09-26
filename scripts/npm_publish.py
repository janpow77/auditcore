"""Publish the signed @auditcore release tarballs to the npm registry.

The workflow ``npm-publish.yml`` downloads the assets of one GitHub release and
calls this script. Nothing is rebuilt: every tarball must match the SHA-256,
size and npm integrity recorded in ``npm-packages.json`` and be listed in the
signed ``SHA256SUMS``. Packages are published in dependency order; versions
that already exist on the registry with the same integrity are skipped. A
version that exists with different content is reported as a conflict: it is
never overwritten, the remaining packages are still published and the run
fails at the end.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import re
import subprocess
import tarfile
from pathlib import Path
from typing import Any

SCOPE = "@auditcore/"
MANIFEST = "npm-packages.json"
REPOSITORY = "github.com/janpow77/auditcore"
VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-[0-9A-Za-z.-]+)?")


class PublishError(ValueError):
    """The release assets or the registry state forbid publishing."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def npm_integrity(data: bytes) -> str:
    """Subresource-integrity string as npm reports it (``dist.integrity``)."""
    return "sha512-" + base64.b64encode(hashlib.sha512(data).digest()).decode()


def read_sums(path: Path) -> dict[str, str]:
    """File name to SHA-256 from a ``sha256sum`` listing."""
    sums: dict[str, str] = {}
    for line in path.read_text().splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  \*?([^/]+)", line.strip())
        if match:
            sums[match.group(2)] = match.group(1)
    return sums


def _repository_url(manifest: dict[str, Any]) -> str:
    repository = manifest.get("repository")
    url = repository.get("url", "") if isinstance(repository, dict) else repository or ""
    return re.sub(r"^git\+|\.git$", "", str(url)).removeprefix("https://")


def _packed_manifest(data: bytes) -> dict[str, Any]:
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        member = archive.extractfile("package/package.json")
        if member is None:
            raise PublishError("Tarball without package/package.json")
        loaded: dict[str, Any] = json.loads(member.read())
    return loaded


def verify_package(entry: dict[str, Any], assets: Path, sums: dict[str, str]) -> None:
    """Bind one manifest entry to its tarball, the signed sums and the repository."""
    name, version, file = entry["name"], entry["version"], entry["file"]
    if not name.startswith(SCOPE) or not VERSION.fullmatch(version) or "/" in file:
        raise PublishError(f"Unexpected package identity: {name}@{version}")
    path = assets / file
    if path.is_symlink() or not path.is_file():
        raise PublishError(f"Tarball missing: {file}")
    data = path.read_bytes()
    digest = sha256(data)
    if sums.get(file) != digest or entry.get("sha256") != digest:
        raise PublishError(f"SHA-256 does not match SHA256SUMS/{MANIFEST}: {file}")
    if entry.get("size") != len(data) or entry.get("integrity") != npm_integrity(data):
        raise PublishError(f"Size or npm integrity mismatch: {file}")
    packed = _packed_manifest(data)
    if packed.get("name") != name or packed.get("version") != version:
        raise PublishError(f"Tarball content is not {name}@{version}")
    if packed.get("license") != "MIT" or packed.get("private"):
        raise PublishError(f"Not a public MIT package: {name}")
    if _repository_url(packed) != REPOSITORY:
        # npm rejects provenance unless repository.url names the building repository.
        raise PublishError(f"package.json#repository must point to {REPOSITORY}: {name}")


def load_release(assets: Path, tag: str) -> list[dict[str, Any]]:
    """Verified manifest entries of the release ``tag`` (``vX.Y.Z``)."""
    manifest = json.loads((assets / MANIFEST).read_text())
    if f"v{manifest.get('release_version')}" != tag:
        raise PublishError(f"{MANIFEST} belongs to another release than {tag}")
    sums = read_sums(assets / "SHA256SUMS")
    if sums.get(MANIFEST) != sha256((assets / MANIFEST).read_bytes()):
        raise PublishError(f"{MANIFEST} is not covered by the signed SHA256SUMS")
    packages: list[dict[str, Any]] = manifest.get("packages") or []
    names = [entry["name"] for entry in packages]
    if not packages or len(names) != len(set(names)):
        raise PublishError(f"{MANIFEST} lists no packages or duplicates")
    for entry in packages:
        verify_package(entry, assets, sums)
    return packages


def publish_order(packages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Dependencies before dependants (stable, alphabetical within a level)."""
    by_name = {entry["name"]: entry for entry in packages}
    pending = {
        name: set(entry.get("internal_requirements") or {}) & set(by_name)
        for name, entry in by_name.items()
    }
    ordered: list[dict[str, Any]] = []
    while pending:
        ready = sorted(name for name, needs in pending.items() if not needs)
        if not ready:
            raise PublishError(f"Dependency cycle between: {', '.join(sorted(pending))}")
        for name in ready:
            ordered.append(by_name[name])
            del pending[name]
        for needs in pending.values():
            needs.difference_update(ready)
    return ordered


def _version_key(version: str) -> tuple[int, int, int]:
    match = VERSION.fullmatch(version)
    if not match:
        return (-1, -1, -1)
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def dist_tag(version: str, current_latest: str | None) -> str:
    """``next`` for pre-releases, ``latest`` unless that would move it backwards."""
    if "-" in version:
        return "next"
    if current_latest and _version_key(current_latest) > _version_key(version):
        return "previous"
    return "latest"


def npm_view(name: str, field: str) -> str | None:
    """A registry field, or ``None`` when the package or version does not exist."""
    result = subprocess.run(
        ["npm", "view", name, field, "--json"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if result.returncode != 0:
        if "E404" in result.stderr:
            return None
        raise PublishError(f"npm view {name} failed: {result.stderr.strip()[-400:]}")
    text = result.stdout.strip()
    value = json.loads(text) if text else None
    return value if isinstance(value, str) else None


def plan_package(entry: dict[str, Any]) -> dict[str, Any]:
    """Decide publish or skip for one verified package against the registry."""
    name, version = entry["name"], entry["version"]
    published = npm_view(f"{name}@{version}", "dist.integrity")
    step = {"name": name, "version": version, "file": entry["file"]}
    if published is not None and published != entry["integrity"]:
        return {**step, "action": "conflict", "reason": "exists on npm with different content"}
    if published is not None:
        return {**step, "action": "skip", "reason": "already published"}
    tag = dist_tag(version, npm_view(name, "dist-tags.latest"))
    return {**step, "action": "publish", "dist_tag": tag}


def npm_publish(assets: Path, step: dict[str, Any]) -> None:
    command = [
        "npm",
        "publish",
        str(assets / step["file"]),
        "--provenance",
        "--access",
        "public",
        "--tag",
        step["dist_tag"],
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=600, check=False)
    if result.returncode != 0:
        raise PublishError(f"npm publish {step['name']} failed: {result.stderr.strip()[-800:]}")


def run(assets: Path, tag: str, publish: bool) -> list[dict[str, Any]]:
    steps = []
    for entry in publish_order(load_release(assets, tag)):
        step = plan_package(entry)
        if publish and step["action"] == "publish":
            npm_publish(assets, step)
            step["action"] = "published"
        steps.append(step)
        print(json.dumps(step, ensure_ascii=False), flush=True)
    return steps


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, required=True, help="downloaded release assets")
    parser.add_argument("--tag", required=True, help="release tag, e.g. v0.4.2")
    parser.add_argument("--publish", action="store_true", help="publish (default: plan only)")
    parser.add_argument("--report", type=Path, help="write the steps as JSON")
    args = parser.parse_args(argv)
    try:
        steps = run(args.assets.resolve(), args.tag, args.publish)
    except PublishError as error:
        print(f"::error::{error}")
        return 1
    if args.report:
        report = {"tag": args.tag, "publish": args.publish, "steps": steps}
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    conflicts = [f"{s['name']}@{s['version']}" for s in steps if s["action"] == "conflict"]
    if conflicts:
        # The plan only warns so that the publish job still ships the other packages.
        level = "error" if args.publish else "warning"
        print(f"::{level}::Version exists on npm with different content: {', '.join(conflicts)}")
        return 1 if args.publish else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
