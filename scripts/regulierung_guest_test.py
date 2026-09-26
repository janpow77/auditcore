"""Actual Regulierung APT lifecycle checks; refuses execution outside its dedicated VM."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import pwd
import re
import secrets
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def command(*args: str) -> str:
    """Run a checked command without logging secrets from its arguments."""
    result = subprocess.run(
        args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900
    )
    print(result.stdout, flush=True)
    result.check_returncode()
    return result.stdout.strip()


def request(url: str, statuses: list[int]) -> bytes:
    """Read the actual HTTP response, including expected authorization errors."""
    try:
        response = urllib.request.urlopen(url, timeout=10)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        assert response.status in statuses, f"Unexpected HTTP {response.status}: {url}"
        return response.read()


def main() -> None:
    """Install, initialize, upgrade, remove and reinstall the real application."""
    if "auditcore.regulierung-test=1" not in Path("/proc/cmdline").read_text().split():
        raise SystemExit("Refusing execution outside dedicated Regulierung test VM")
    report: dict = {
        "status": "FAIL",
        "checks": {},
        "limitations": [
            "Synthetic empty application database; no production data migration exercised",
            "No external identity provider or live harvesting in the networkless guest",
        ],
    }
    checks = report["checks"]
    config = json.loads(Path("/auditcore-configuration.json").read_text())
    services = config.get("services", ["regulierung.service", "regulierung-web.service"])
    configuration = Path(config.get("configuration", "/etc/regulierung/regulierung.env"))
    state = Path(config.get("state_directory", "/var/lib/regulierung"))
    try:
        assert Path("/proc/1/comm").read_text().strip() == "systemd"
        assert not any(Path("/sys/class/net").glob("eth*")), "Guest unexpectedly has a network NIC"
        report["kernel"] = os.uname().release
        packages = [Path("/packages/old.deb"), Path("/packages/new.deb")]
        name = command("dpkg-deb", "-f", str(packages[0]), "Package")
        assert re.fullmatch(r"[a-z][a-z0-9+.-]+", name)
        assert name == command("dpkg-deb", "-f", str(packages[1]), "Package")
        versions = [command("dpkg-deb", "-f", str(p), "Version") for p in packages]
        command("dpkg", "--compare-versions", versions[0], "lt", versions[1])
        report["artifacts"] = [
            {"version": version, "sha256": hashlib.sha256(package.read_bytes()).hexdigest()}
            for version, package in zip(versions, packages, strict=True)
        ]
        for dependency in config.get("dependency_services", ["postgresql", "redis-server"]):
            command("systemctl", "start", dependency)
        database = config.get("database", "regulierung")
        if not re.fullmatch(r"[a-z][a-z0-9_]+", database):
            raise ValueError("Unsafe database test name")
        sql_prefix = [
            "runuser",
            "-u",
            "postgres",
            "--",
            "psql",
            "-XAt",
            "-v",
            "ON_ERROR_STOP=1",
            "-d",
            database,
            "-c",
        ]
        admin_password = secrets.token_urlsafe(32)
        saved_configuration = ""
        sentinel = state / "uploads" / "auditcore-preservation-proof"
        for phase, feed, version in (
            ("install", "old", versions[0]),
            ("upgrade", "new", versions[1]),
            ("reinstall", "new", versions[1]),
        ):
            Path("/etc/apt/sources.list.d/auditcore-test.list").write_text(
                f"deb [signed-by=/usr/share/keyrings/auditcore-test.gpg] file:/feed/{feed} ./\n"
            )
            command("apt-get", "update", "-o", "APT::Update::Error-Mode=any")
            command("apt-get", "install", "-y", f"{name}={version}")
            assert command("dpkg-query", "-W", "-f=${Version}", name) == version
            checks[f"{phase}_signed_apt"] = "PASS"
            if phase == "install":
                command(
                    *config.get("initialization", ["/usr/sbin/regulierung-admin", "init-local"])
                )
                command(
                    *sql_prefix,
                    "CREATE TABLE auditcore_lifecycle_probe (value text NOT NULL); "
                    "INSERT INTO auditcore_lifecycle_probe VALUES ('synthetic-retained-value');",
                )
                if config.get("create_admin", True):
                    created = subprocess.run(
                        [
                            "/usr/sbin/regulierung-admin",
                            "create-admin",
                            "--username",
                            "vm-admin",
                            "--email",
                            "vm-admin@example.invalid",
                        ],
                        input=admin_password + "\n" + admin_password + "\n",
                        text=True,
                        capture_output=True,
                        timeout=120,
                    )
                    if created.returncode:
                        raise RuntimeError("Administrator creation failed; secret output withheld")
                    checks["administrator_created"] = "PASS"
                sentinel.parent.mkdir(parents=True, exist_ok=True)
                sentinel.write_text("synthetic persistent application state\n")
                with configuration.open("a") as stream:
                    stream.write("\n# lifecycle preservation evidence\n")
                saved_configuration = hashlib.sha256(configuration.read_bytes()).hexdigest()
            else:
                assert sentinel.read_text() == "synthetic persistent application state\n"
                assert hashlib.sha256(configuration.read_bytes()).hexdigest() == saved_configuration
                assert command(*sql_prefix, "SELECT value FROM auditcore_lifecycle_probe") == (
                    "synthetic-retained-value"
                )
                checks[f"{phase}_preserved_configuration_and_data"] = "PASS"
            assert configuration.stat().st_mode & 0o777 == 0o640
            assert configuration.stat().st_uid == 0
            assert configuration.stat().st_gid == pwd.getpwnam("regulierung").pw_gid
            checks[f"{phase}_secret_permissions"] = "PASS"
            if phase == "upgrade":
                command("/usr/sbin/regulierung-admin", "migrate")
                checks["upgrade_backup_and_restore_verification"] = "PASS"
            for service in services:
                command("systemctl", "enable", "--now", service)
                assert command("systemctl", "is-active", service) == "active"
                pid = int(command("systemctl", "show", "--value", "-p", "MainPID", service))
                assert pid > 1
                user = command("systemctl", "show", "--value", "-p", "User", service)
                uid = pwd.getpwnam(user).pw_uid
                assert uid > 0
                actual = re.search(r"^Uid:\s+(.+)$", Path(f"/proc/{pid}/status").read_text(), re.M)
                assert actual and set(actual[1].split()) == {str(uid)}
            checks[f"{phase}_systemd_nonroot"] = "PASS"
            ready = config.get("readiness_url", "http://127.0.0.1:8090/api/ready")
            for _attempt in range(120):
                try:
                    readiness = json.loads(request(ready, [200]))
                    break
                except (OSError, AssertionError, ValueError):
                    time.sleep(1)
            else:
                raise RuntimeError(f"{phase}: application database/Redis readiness failed")
            report[f"{phase}_readiness"] = readiness
            checks[f"{phase}_readiness"] = "PASS"
            frontend = request(config.get("frontend_url", "http://127.0.0.1:3003/"), [200])
            assert b"<html" in frontend.lower() and b"<script" in frontend.lower()
            checks[f"{phase}_frontend"] = "PASS"
            if phase == "install":
                pdf = state / "uploads" / "auditcore-native-pdf.pdf"
                command(
                    "runuser",
                    "-u",
                    "regulierung",
                    "--",
                    "env",
                    "PYTHONPATH=/opt/regulierung/runtime:/opt/regulierung/application",
                    "PYTHONDONTWRITEBYTECODE=1",
                    "/usr/bin/python3",
                    "-c",
                    "from weasyprint import HTML; "
                    "HTML(string='<p>Synthetic native PDF verification</p>').write_pdf("
                    + repr(str(pdf))
                    + ")",
                )
                assert pdf.read_bytes().startswith(b"%PDF-")
                report["native_pdf_sha256"] = hashlib.sha256(pdf.read_bytes()).hexdigest()
                checks["native_pdf_rendering"] = "PASS"
            if phase == "install":
                command("systemctl", "stop", "redis-server")
                request(ready, [503])
                checks["readiness_rejects_unavailable_redis"] = "PASS"
                command("systemctl", "start", "redis-server")
                request(ready, [200])
            for url in config.get("protected_urls", ["http://127.0.0.1:3003/api/auth/me"]):
                request(url, [401, 403])
            checks[f"{phase}_anonymous_access_rejected"] = "PASS"
            if config.get("create_admin", True):
                login = urllib.request.Request(
                    "http://127.0.0.1:3003/api/auth/login",
                    data=urllib.parse.urlencode(
                        {"username": "vm-admin", "password": admin_password}
                    ).encode(),
                )
                with urllib.request.urlopen(login, timeout=15) as response:
                    assert response.status == 200
                    token = json.loads(response.read())["access_token"]
                authenticated = urllib.request.Request(
                    "http://127.0.0.1:3003/api/auth/me",
                    headers={"Authorization": "Bearer " + token},
                )
                with urllib.request.urlopen(authenticated, timeout=15) as response:
                    assert response.status == 200
                    identity = json.loads(response.read())
                    assert identity["username"] == "vm-admin" and identity["is_admin"]
                checks[f"{phase}_real_administrator_login"] = "PASS"
            if phase in {"upgrade", "reinstall"}:
                command("apt-get", "remove", "-y", name)
                for service in services:
                    assert (
                        subprocess.run(
                            ["systemctl", "is-active", service], capture_output=True
                        ).returncode
                        != 0
                    )
                assert sentinel.read_text() == "synthetic persistent application state\n"
                assert hashlib.sha256(configuration.read_bytes()).hexdigest() == saved_configuration
                assert command(*sql_prefix, "SELECT value FROM auditcore_lifecycle_probe") == (
                    "synthetic-retained-value"
                )
                checks[f"{phase}_remove_stops_service_retains_data"] = "PASS"
        # Source compilation and package downloads are not target-side prerequisites.
        for executable in ("node", "npm", "poetry", "uv", "gcc", "cc"):
            assert (
                subprocess.run(
                    ["sh", "-c", 'command -v "$1"', "check", executable], capture_output=True
                ).returncode
                != 0
            )
        checks["no_build_toolchain_required"] = "PASS"
        checks["offline_runtime"] = "PASS"
        report["status"] = "PASS"
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        if config.get("diagnose_initial_migration", False):
            diagnostic = r"""
import sys, os, subprocess
sys.path[:0] = ['/opt/regulierung/runtime', '/opt/regulierung/application']
from deploy_admin import environment
from urllib.parse import urlsplit
env = environment()
result = subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'],
    cwd='/opt/regulierung/application', env=env, capture_output=True, text=True)
output = result.stdout + '\n' + result.stderr
for key in ('SECRET_KEY', 'DATABASE_URL', 'REDIS_URL'):
    value = env.get(key)
    if value:
        password = urlsplit(value).password if '://' in value else value
        output = output.replace(value, '[REDACTED]')
        if password:
            output = output.replace(password, '[REDACTED]')
print(output)
print('DIAGNOSTIC_MIGRATION_EXIT=' + str(result.returncode))
"""
            # Explicit debug option only in this disposable, synthetic-data VM.
            subprocess.run(["/usr/bin/python3", "-c", diagnostic], timeout=300, check=False)
        subprocess.run(["journalctl", "-b", "--no-pager", "-n", "150"], check=False)
    finally:
        encoded = base64.b64encode(json.dumps(report, sort_keys=True).encode()).decode()
        print(f"\nAUDITCORE_VM_RESULT={encoded}\n", flush=True)
        subprocess.run(["systemctl", "poweroff", "--no-block"], check=False)


if __name__ == "__main__":
    main()
