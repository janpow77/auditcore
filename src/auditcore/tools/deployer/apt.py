"""Local APT metadata, signatures and explicitly configured publication."""

from __future__ import annotations

import gzip
import os
import shutil
import subprocess
from datetime import UTC, datetime
from email.utils import format_datetime
from pathlib import Path

from auditcore.tools.common import digest, run, safe_path
from auditcore.tools.deployer.models import AptRepositoryBuild


def release_date() -> str:
    """RFC 2822 UTC date for the ``Date`` field of a Release file.

    apt rejects a missing or malformed ``Date`` ("Invalid 'Date' entry"). A set
    ``SOURCE_DATE_EPOCH`` makes the value reproducible; otherwise the build time.
    """
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    moment = datetime.fromtimestamp(int(epoch), UTC) if epoch else datetime.now(UTC)
    return format_datetime(moment, usegmt=True)


class AptRepository:
    """Build flat signed APT repositories without embedding a URL or signing key."""

    def build(self, directory: Path, signing_key: str | None = None) -> AptRepositoryBuild:
        """Build Packages/Release and optionally sign with an existing GPG key."""
        directory = directory.resolve()
        packages = sorted(directory.glob("*.deb"))
        if not packages:
            raise ValueError("No Debian packages found")
        records = []
        for package in packages:
            control = run(["dpkg-deb", "--field", str(package)]).strip()
            records.append(
                f"{control}\nFilename: ./{package.name}\nSize: {package.stat().st_size}"
                f"\nSHA256: {digest(package.read_bytes())}\n"
            )
        content = ("\n".join(records) + "\n").encode()
        (directory / "Packages").write_bytes(content)
        (directory / "Packages.gz").write_bytes(gzip.compress(content, mtime=0))
        release = (
            "Origin: auditcore\nLabel: auditcore\n"
            f"Date: {release_date()}\n"
            "Architectures: all amd64 arm64\nSHA256:\n"
        )
        for name in ("Packages", "Packages.gz"):
            data = (directory / name).read_bytes()
            release += f" {digest(data)} {len(data)} {name}\n"
        (directory / "Release").write_text(release)
        if signing_key:
            for output, mode in (("InRelease", "--clearsign"), ("Release.gpg", "--detach-sign")):
                run(
                    [
                        "gpg",
                        "--batch",
                        "--yes",
                        "--local-user",
                        signing_key,
                        "--armor",
                        mode,
                        "--output",
                        str(directory / output),
                        str(directory / "Release"),
                    ]
                )
            run(["gpg", "--verify", str(directory / "Release.gpg"), str(directory / "Release")])
        return AptRepositoryBuild(
            "PASS" if signing_key else "REVIEW_REQUIRED",
            str(directory),
            len(packages),
            bool(signing_key),
        )

    def validate(self, directory: Path) -> dict[str, str]:
        """Verify signed metadata, index digests and every referenced package before release."""
        run(["gpg", "--verify", str(directory / "Release.gpg"), str(directory / "Release")])
        signed_release = run(["gpg", "--decrypt", str(directory / "InRelease")])
        release = (directory / "Release").read_text()
        if signed_release != release:
            raise ValueError("APT signed Release content mismatch")
        for name in ("Packages", "Packages.gz"):
            data = (directory / name).read_bytes()
            if f" {digest(data)} {len(data)} {name}\n" not in release:
                raise ValueError("APT index digest mismatch")
        indexed: set[Path] = set()
        for paragraph in (directory / "Packages").read_text().strip().split("\n\n"):
            fields = dict(line.split(": ", 1) for line in paragraph.splitlines() if ": " in line)
            package = safe_path(directory, fields["Filename"])
            indexed.add(package.resolve())
            content = package.read_bytes()
            if digest(content) != fields["SHA256"] or len(content) != int(fields["Size"]):
                raise ValueError("APT package digest mismatch")
        if indexed != {p.resolve() for p in directory.glob("*.deb")}:
            raise ValueError("APT unindexed package present")
        return {"status": "PASS", "signature": "PASS", "digests": "PASS"}

    def publish(self, directory: Path, destination: Path) -> None:
        """Copy verified signed repository to an explicitly supplied local publish directory."""
        if not (directory / "InRelease").exists() or not (directory / "Release.gpg").exists():
            raise ValueError("Signed metadata required before publication")
        self.validate(directory)
        if destination.exists() and any(destination.iterdir()):
            raise ValueError(
                "Publication destination must be empty; atomic release directory required"
            )
        destination.mkdir(parents=True, exist_ok=True)
        for path in directory.iterdir():
            if path.suffix == ".deb" or path.name in {
                "Packages",
                "Packages.gz",
                "Release",
                "Release.gpg",
                "InRelease",
            }:
                shutil.copyfile(path, destination / path.name)


def health_check(url: str) -> str:
    """Check an explicitly configured endpoint without disclosing response contents."""
    result = subprocess.run(
        ["curl", "--fail", "--silent", "--max-time", "15", url],
        capture_output=True,
        timeout=20,
        check=False,
    )
    return "PASS" if result.returncode == 0 else "FAIL"
