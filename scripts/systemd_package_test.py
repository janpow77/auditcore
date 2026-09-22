"""Run offline Debian package lifecycle checks in a disposable, unprivileged QEMU VM.

Docker builds the test environment only; the host receives no packages or services.
QEMU uses CPU emulation, so KVM, host cgroups and privileged containers are unnecessary.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

DOCKERFILE = """FROM debian:bookworm-slim AS guest
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 adduser systemd systemd-sysv ca-certificates linux-image-amd64 \
    && rm -rf /var/lib/apt/lists/*
COPY old.deb new.deb /packages/
COPY systemd_guest_test.py /auditcore-test.py
COPY auditcore-test.service /etc/systemd/system/auditcore-test.service
RUN mkdir -p /run /proc /sys /dev /tmp

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends qemu-system-x86 e2fsprogs \
    && rm -rf /var/lib/apt/lists/*
COPY --from=guest / /guest/
RUN cp /guest/boot/vmlinuz-* /kernel && cp /guest/boot/initrd.img-* /initrd \
    && truncate -s 3G /disk.raw && mkfs.ext4 -q -F -d /guest /disk.raw \
    && chmod 0644 /kernel /initrd /disk.raw && rm -rf /guest
USER 65534:65534
ENTRYPOINT ["qemu-system-x86_64", "-accel", "tcg", "-m", "768", "-smp", "2", \
    "-nographic", "-no-reboot", "-nic", "none", "-kernel", "/kernel", "-initrd", "/initrd", \
    "-append", "root=/dev/vda rw console=ttyS0 \
systemd.unit=auditcore-test.service auditcore.package-test=1", \
    "-drive", "file=/disk.raw,format=raw,if=virtio,snapshot=on"]
"""

UNIT = """[Unit]
Description=Auditcore isolated package lifecycle verification
After=basic.target
Requires=basic.target
AllowIsolate=yes

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /auditcore-test.py
StandardOutput=journal+console
StandardError=journal+console
TimeoutStartSec=600
"""


def main() -> int:
    """Build an isolated test image and write artifact-bound runtime evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("--output", type=Path, default=Path(".auditcore/systemd-validation"))
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True, mode=0o700)
    report: dict = {
        "status": "NOT_EXECUTED",
        "started_at": datetime.now(UTC).isoformat(),
        "runtime": "QEMU TCG inside unprivileged Docker; no VM network",
        "release_authorization": "NOT_EVALUATED",
    }
    run_id = uuid.uuid4().hex[:12]
    image = f"auditcore-systemd-test:{run_id}"
    container = f"auditcore-systemd-test-{run_id}"
    try:
        with tempfile.TemporaryDirectory(prefix="auditcore-systemd-") as temporary:
            context = Path(temporary)
            for source, name in ((args.old, "old.deb"), (args.new, "new.deb")):
                shutil.copyfile(source, context / name)
            shutil.copyfile(
                Path(__file__).with_name("systemd_guest_test.py"), context / "systemd_guest_test.py"
            )
            (context / "Dockerfile").write_text(DOCKERFILE)
            (context / "auditcore-test.service").write_text(UNIT)
            with (args.output / "build.log").open("w") as log:
                subprocess.run(
                    ["docker", "build", "-t", image, str(context)],
                    check=True,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=1200,
                )
        report["image"] = subprocess.check_output(
            ["docker", "image", "inspect", image, "--format", "{{.Id}}"], text=True
        ).strip()
        with (args.output / "console.log").open("w") as log:
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--name",
                    container,
                    "--network",
                    "none",
                    "--cap-drop",
                    "ALL",
                    "--security-opt",
                    "no-new-privileges",
                    "--read-only",
                    "--tmpfs",
                    "/tmp:rw,nosuid,nodev,size=1g,mode=1777",
                    "--tmpfs",
                    "/var/tmp:rw,nosuid,nodev,size=1g,mode=1777",
                    "--memory",
                    "2g",
                    "--cpus",
                    "2",
                    "--pids-limit",
                    "128",
                    image,
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=args.timeout,
                check=False,
            )
        console = (args.output / "console.log").read_bytes()
        report["console_sha256"] = hashlib.sha256(console).hexdigest()
        report["vm_exit_code"] = result.returncode
        matches = re.findall(rb"AUDITCORE_VM_RESULT=([A-Za-z0-9+/=]+)", console)
        if len(matches) != 1:
            raise ValueError("Expected exactly one complete VM result; inspect console.log")
        guest = json.loads(base64.b64decode(matches[0], validate=True))
        report["guest"] = guest
        report["status"] = guest["status"] if result.returncode == 0 else "FAIL"
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        # Only this run's dedicated container is addressed, including after a timeout.
        subprocess.run(["docker", "rm", "-f", container], capture_output=True, check=False)
        report["finished_at"] = datetime.now(UTC).isoformat()
        result_path = args.output / "result.json"
        result_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        result_path.chmod(0o600)
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
