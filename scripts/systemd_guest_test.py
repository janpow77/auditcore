"""Package lifecycle probe executed exclusively inside the disposable Debian VM."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import pwd
import re
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path


def command(*args: str) -> str:
    """Fail on any unsuccessful command and retain output in the VM console."""
    result = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout, flush=True)
    result.check_returncode()
    return result.stdout.strip()


def main() -> None:
    """Install, start, restart, upgrade and remove with real systemd PID 1."""
    if "auditcore.package-test=1" not in Path("/proc/cmdline").read_text().split():
        raise SystemExit("Refusing to run outside the dedicated auditcore test VM")
    report: dict = {"status": "FAIL", "scope": "package_lifecycle", "checks": {}}
    checks = report["checks"]
    try:
        assert Path("/proc/1/comm").read_text().strip() == "systemd"
        report["pid1"] = "systemd"
        report["kernel"] = os.uname().release
        report["systemd_version"] = command("systemctl", "--version").splitlines()[0]
        packages = [Path("/packages/old.deb"), Path("/packages/new.deb")]
        name = command("dpkg-deb", "--field", str(packages[0]), "Package")
        assert re.fullmatch(r"[a-z][a-z0-9+.-]+", name)
        assert name == command("dpkg-deb", "--field", str(packages[1]), "Package")
        report["package"] = name
        report["artifacts"] = [
            {"name": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in packages
        ]
        sentinel = Path(f"/var/lib/{name}/data/auditcore-test-sentinel")
        configuration = Path(f"/etc/{name}/{name}.env")
        for index, package in enumerate(packages):
            phase = "installation" if index == 0 else "upgrade"
            expected = command("dpkg-deb", "--field", str(package), "Version")
            architecture = command("dpkg-deb", "--field", str(package), "Architecture")
            assert re.fullmatch(r"[A-Za-z0-9.+:~_-]+", expected)
            assert re.fullmatch(r"[a-z0-9-]+", architecture)
            # APT's --no-download also skips copying local archives into its cache.
            version_name = expected.replace(":", "%3a")
            cached = Path(f"/var/cache/apt/archives/{name}_{version_name}_{architecture}.deb")
            shutil.copyfile(package, cached)
            command("apt-get", "install", "-y", "--no-download", str(package))
            assert command("dpkg-query", "-W", "-f=${Version}", name) == expected
            checks[phase] = "PASS"
            if index == 0:
                sentinel.write_text("preserve across upgrade and remove\n")
                with configuration.open("a") as stream:
                    stream.write("\n# auditcore retained configuration\n")
            else:
                assert sentinel.read_text() == "preserve across upgrade and remove\n"
                assert "# auditcore retained configuration" in configuration.read_text()
                checks["upgrade_data_and_configuration"] = "PASS"

            manifest = json.loads(Path(f"/opt/{name}/build-manifest.json").read_text())
            service = f"{name}.service"
            command("systemd-analyze", "verify", f"/usr/lib/systemd/system/{service}")
            command("systemctl", "enable", service)
            command("systemctl", "restart", service)
            assert command("systemctl", "is-active", service) == "active"
            assert command("systemctl", "is-enabled", service) == "enabled"
            pid = int(command("systemctl", "show", "--value", "-p", "MainPID", service))
            assert pid > 1
            uid = pwd.getpwnam(manifest["service_user"]).pw_uid
            assert uid > 0
            actual_uids = re.search(r"^Uid:\s+(.+)$", Path(f"/proc/{pid}/status").read_text(), re.M)
            assert actual_uids and set(actual_uids[1].split()) == {str(uid)}
            checks[f"{phase}_service_user"] = "PASS"
            checks[f"{phase}_systemd_service"] = "PASS"
            url = manifest.get("health_url")
            if not url:
                checks[f"{phase}_health"] = "NOT_CONFIGURED"
                raise ValueError("An explicit health_url is required for this verification")
            for _attempt in range(100):
                try:
                    with urllib.request.urlopen(url, timeout=1) as response:
                        assert response.status == 200
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError(f"{phase} health check failed")
            checks[f"{phase}_health"] = "PASS"
            command("systemctl", "status", "--no-pager", service)
        command("apt-get", "remove", "-y", name)
        result = subprocess.run(["systemctl", "is-active", f"{name}.service"], capture_output=True)
        assert result.returncode != 0
        assert not Path(f"/usr/lib/systemd/system/{name}.service").exists()
        assert not Path(f"/proc/{pid}").exists()
        assert sentinel.read_text() == "preserve across upgrade and remove\n"
        assert "# auditcore retained configuration" in configuration.read_text()
        checks["remove_service_stopped"] = "PASS"
        checks["remove_data_and_configuration"] = "PASS"
        checks["systemd_runtime"] = "PASS"
        report["status"] = "PASS"
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        subprocess.run(["journalctl", "-b", "--no-pager", "-n", "100"], check=False)
    finally:
        payload = base64.b64encode(json.dumps(report, sort_keys=True).encode()).decode()
        print(f"\nAUDITCORE_VM_RESULT={payload}\n", flush=True)
        subprocess.run(["systemctl", "poweroff", "--no-block"], check=False)


if __name__ == "__main__":
    main()
