"""Isolated package lifecycle tests; no package is installed on the build host."""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from auditcore.tools.common import digest, run
from auditcore.tools.deployer.models import PackageValidation, UpgradeValidation


class DockerPackageTester:
    """Disposable Debian test environment with explicit service-runtime evidence."""

    def __init__(self, image: str = "auditcore-package-test:bookworm") -> None:
        self.image = image

    def prepare(self) -> str:
        """Build a clean test image; build tools remain outside target packages."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "Dockerfile").write_text(
                "FROM debian:bookworm-slim\n"
                "RUN apt-get update && apt-get install -y --no-install-recommends "
                "python3 adduser systemd ca-certificates && rm -rf /var/lib/apt/lists/*\n"
            )
            run(["docker", "build", "-t", self.image, str(root)], timeout=300)
        return run(["docker", "image", "inspect", self.image, "--format", "{{.Id}}"]).strip()

    def _metadata(self, package: Path) -> dict[str, str]:
        name = run(["dpkg-deb", "--field", str(package), "Package"]).strip()
        if not re.fullmatch(r"[a-z][a-z0-9+.-]+", name):
            raise ValueError("Invalid package name")
        return {"name": name, "sha256": digest(package.read_bytes())}

    def test(self, package: Path, old: Path | None = None) -> PackageValidation:
        """Install, optionally upgrade, remove; preserve config/data and verify service syntax."""
        metadata = self._metadata(package)
        name = metadata["name"]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "new.deb").write_bytes(package.read_bytes())
            if old:
                if self._metadata(old)["name"] != name:
                    raise ValueError("Upgrade requires the same application")
                (root / "old.deb").write_bytes(old.read_bytes())
            initial = "old.deb" if old else "new.deb"
            commands = [
                "set -eu",
                f"apt-get install -y /packages/{initial}",
                f"test -d /var/lib/{name}/data",
                f"printf sentinel > /var/lib/{name}/data/sentinel",
                f"printf '\n# retained-test-config\n' >> /etc/{name}/{name}.env",
            ]
            if old:
                commands += [
                    "apt-get install -y /packages/new.deb",
                    f'test "$(cat /var/lib/{name}/data/sentinel)" = sentinel',
                    f"grep -q retained-test-config /etc/{name}/{name}.env",
                ]
            health_runner = "\n".join(
                [
                    "import json, os, subprocess, time, urllib.request",
                    f"name = {name!r}",
                    "manifest = json.load(open('/opt/' + name + '/build-manifest.json'))",
                    "url = manifest.get('health_url')",
                    "if not url:",
                    "    print('AUDITCORE_HEALTH_NOT_CONFIGURED')",
                    "else:",
                    "    runtime = '/opt/' + name + '/runtime'",
                    "    command = list(manifest['entrypoint'])",
                    "    if manifest['runtime_strategy'] == 'BUNDLED_VENV':",
                    "        command[0] = runtime + '/bin/python3'",
                    "        runtime += '/site-packages'",
                    "    env = dict(os.environ, PYTHONPATH=runtime +"
                    " ':/opt/' + name + '/application')",
                    "    process = subprocess.Popen(['runuser', '-u',"
                    " manifest['service_user'], '--',",
                    "        'env', 'PYTHONPATH=' + env['PYTHONPATH'], *command],",
                    "                               cwd='/opt/' + name + '/application',",
                    "        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)",
                    "    try:",
                    "        for attempt in range(40):",
                    "            try:",
                    "                with urllib.request.urlopen(url, timeout=1) as response:",
                    "                    assert response.status == 200",
                    "                print('AUDITCORE_HEALTH_PASS')",
                    "                break",
                    "            except OSError:",
                    "                time.sleep(0.1)",
                    "        else:",
                    "            raise SystemExit('Health check failed')",
                    "    finally:",
                    "        process.terminate()",
                    "        process.wait(timeout=5)",
                ]
            )
            commands += [
                f"systemd-analyze verify /usr/lib/systemd/system/{name}.service",
                "python3 - <<'AUDITCORE_HEALTH'\n" + health_runner + "\nAUDITCORE_HEALTH",
                f"apt-get remove -y {name}",
                f'test "$(cat /var/lib/{name}/data/sentinel)" = sentinel',
                f"test -f /etc/{name}/{name}.env",
                "printf 'AUDITCORE_LIFECYCLE_PASS\\n'",
            ]
            process = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--network",
                    "none",
                    "--mount",
                    f"type=bind,src={root},dst=/packages,readonly",
                    self.image,
                    "sh",
                    "-c",
                    "\n".join(commands),
                ],
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
        passed = process.returncode == 0 and "AUDITCORE_LIFECYCLE_PASS" in process.stdout
        status = "PASS" if passed else "FAIL"
        return PackageValidation(
            "REVIEW_REQUIRED" if passed else "FAIL",
            {
                "ACD-INST-001": status,
                "ACD-RM-001": status,
                "ACD-UPG-001": status if old else "NOT_EXECUTED",
                "ACD-DATA-001": status,
                "ACD-CONF-001": status,
                "ACD-SVC-001": status,
                "systemd_runtime": "NOT_EXECUTED",
                "ACD-HEALTH-001": "PASS"
                if "AUDITCORE_HEALTH_PASS" in process.stdout
                else "NOT_CONFIGURED"
                if "AUDITCORE_HEALTH_NOT_CONFIGURED" in process.stdout
                else "NOT_EXECUTED",
            },
            metadata["sha256"],
            self.image,
        )

    def test_upgrade(self, old: Path, new: Path) -> UpgradeValidation:
        """Run upgrade lifecycle and retain exact artifact digests."""
        result = self.test(new, old)
        return UpgradeValidation(
            result.status, digest(old.read_bytes()), digest(new.read_bytes()), result.checks
        )


def inspect_package(package: Path) -> dict[str, Any]:
    """Read package metadata and archive listing without running maintainer scripts."""
    return {
        "status": "PASS",
        "sha256": digest(package.read_bytes()),
        "control": run(["dpkg-deb", "--info", str(package)]),
        "contents": run(["dpkg-deb", "--contents", str(package)]),
        "installation": "NOT_EXECUTED",
    }


def validate_sbom(sbom: Path, package: Path, manifest: Path) -> dict[str, str]:
    """Verify artifact bindings; structural validation is distinct from full schema validation."""
    data = json.loads(sbom.read_text())
    build = json.loads(manifest.read_text())
    structural = data.get("bomFormat") == "CycloneDX" and data.get("specVersion") == "1.6"
    valid = (
        structural
        and build.get("package_sha256") == digest(package.read_bytes())
        and (build.get("sbom_sha256") == digest(sbom.read_bytes()))
    )
    from auditcore.tools.quality.supplychain import validate_schema

    schema = validate_schema(data)
    return {
        "status": "PASS" if valid and schema["status"] == "PASS" else "FAIL",
        "schema_validation": schema["status"],
        "artifact_binding": "PASS" if valid else "FAIL",
    }
