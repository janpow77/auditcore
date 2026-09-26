"""Verify actual Regulierung packages in a disposable offline systemd QEMU guest.

The supplied guest image must provide repositories for every declared package dependency.
No target package, PostgreSQL cluster or service is installed on the host.
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
from pathlib import Path

DOCKERFILE = """ARG GUEST_IMAGE=ubuntu:24.04
FROM ${GUEST_IMAGE} AS guest
ENV DEBIAN_FRONTEND=noninteractive
RUN printf '#!/bin/sh\\nexit 101\\n' > /usr/sbin/policy-rc.d && chmod +x /usr/sbin/policy-rc.d
RUN apt-get update && apt-get install -y --no-install-recommends \\
 python3 systemd systemd-sysv linux-image-virtual ca-certificates gnupg apt-utils curl
RUN curl -fsSL https://packagecloud.io/timescale/timescaledb/gpgkey \
 | gpg --dearmor -o /usr/share/keyrings/timescaledb.gpg \
 && echo 'deb [signed-by=/usr/share/keyrings/timescaledb.gpg] \
https://packagecloud.io/timescale/timescaledb/ubuntu/ noble main' \
 > /etc/apt/sources.list.d/timescaledb.list \
 && apt-get update && apt-get install -y --no-install-recommends \
 postgresql-16 postgresql-16-postgis-3 timescaledb-2-postgresql-16 redis-server \
 && echo "shared_preload_libraries='timescaledb'" \
 >> /etc/postgresql/16/main/postgresql.conf
COPY old.deb new.deb /packages/
RUN apt-get satisfy -y "$(dpkg-deb -f /packages/old.deb Depends)" \\
 && apt-get satisfy -y "$(dpkg-deb -f /packages/new.deb Depends)"
RUN apt-get install -y --no-install-recommends initramfs-tools \
 && for kernel in /lib/modules/*; do update-initramfs -c -k "${kernel##*/}"; done
COPY regulierung_guest_test.py /auditcore-test.py
COPY configuration.json /auditcore-configuration.json
COPY auditcore-test.service /etc/systemd/system/auditcore-test.service
RUN mkdir -m 700 /signing && gpg --batch --homedir /signing --passphrase '' \\
 --quick-generate-key 'Disposable package verification' ed25519 sign 1d \\
 && gpg --homedir /signing --export > /usr/share/keyrings/auditcore-test.gpg \\
 && for phase in old new; do mkdir -p /feed/$phase; cp /packages/$phase.deb /feed/$phase/; \\
 cd /feed/$phase; apt-ftparchive packages . > Packages; \\
 apt-ftparchive release . > Release; \\
 gpg --batch --homedir /signing --clearsign -o InRelease Release; done \\
 && rm -rf /signing /etc/apt/sources.list /etc/apt/sources.list.d/* \\
 /var/lib/apt/lists/* /usr/sbin/policy-rc.d \\
 && mkdir -p /run /proc /sys /dev /tmp
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends qemu-system-x86 e2fsprogs \\
 && rm -rf /var/lib/apt/lists/*
COPY --from=guest / /guest/
RUN echo '127.0.0.1 localhost' > /guest/etc/hosts \
 && echo '::1 localhost' >> /guest/etc/hosts \
 && cp /guest/boot/vmlinuz-* /kernel && cp /guest/boot/initrd.img-* /initrd \\
 && truncate -s 12G /disk.raw && mkfs.ext4 -q -F -d /guest /disk.raw \\
 && chmod 0644 /kernel /initrd /disk.raw && rm -rf /guest
USER 65534:65534
ENTRYPOINT ["qemu-system-x86_64", "-accel", "tcg", "-cpu", "max", "-m", "4096", "-smp", "4", \\
 "-nographic", "-no-reboot", "-nic", "none", "-kernel", "/kernel", "-initrd", "/initrd", \\
 "-append", "root=/dev/vda rw console=ttyS0 \
systemd.unit=auditcore-test.service auditcore.regulierung-test=1", \\
 "-drive", "file=/disk.raw,format=raw,if=virtio,snapshot=on"]
"""
UNIT = """[Unit]
Description=Isolated actual Regulierung lifecycle verification
After=basic.target
Requires=basic.target
AllowIsolate=yes
[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /auditcore-test.py
StandardOutput=journal+console
StandardError=journal+console
TimeoutStartSec=3600
"""


def main() -> int:
    """Build and run the isolated guest, preserving exact package-bound evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("--guest-image", default="ubuntu:24.04")
    parser.add_argument(
        "--configuration",
        type=Path,
        required=True,
        help="Guest test contract JSON: initialization argv, service, URLs and paths",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=3600)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True, mode=0o700)
    configuration = json.loads(args.configuration.read_text())
    run_id = uuid.uuid4().hex[:12]
    image = f"auditcore-regulierung-test:{run_id}"
    container = f"auditcore-regulierung-test-{run_id}"
    report: dict = {
        "status": "NOT_EXECUTED",
        "runtime": "offline QEMU TCG, real systemd",
        "guest_script_sha256": hashlib.sha256(
            Path(__file__).with_name("regulierung_guest_test.py").read_bytes()
        ).hexdigest(),
        "dockerfile_sha256": hashlib.sha256(DOCKERFILE.encode()).hexdigest(),
        "configuration_sha256": hashlib.sha256(args.configuration.read_bytes()).hexdigest(),
        "packages": [
            {"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in (args.old, args.new)
        ],
    }
    try:
        with tempfile.TemporaryDirectory(prefix="regulierung-vm-") as temporary:
            context = Path(temporary)
            for package, target in ((args.old, "old.deb"), (args.new, "new.deb")):
                shutil.copyfile(package, context / target)
            shutil.copyfile(
                Path(__file__).with_name("regulierung_guest_test.py"),
                context / "regulierung_guest_test.py",
            )
            (context / "configuration.json").write_text(json.dumps(configuration))
            (context / "Dockerfile").write_text(DOCKERFILE)
            (context / "auditcore-test.service").write_text(UNIT)
            with (args.output / "build.log").open("w") as log:
                subprocess.run(
                    [
                        "docker",
                        "build",
                        "--build-arg",
                        f"GUEST_IMAGE={args.guest_image}",
                        "-t",
                        image,
                        str(context),
                    ],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=3600,
                    check=True,
                )
        report["image_id"] = subprocess.check_output(
            ["docker", "image", "inspect", image, "--format", "{{.Id}}"], text=True
        ).strip()
        with (args.output / "console.log").open("w") as log:
            completed = subprocess.run(
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
                    "/tmp:rw,nosuid,nodev,size=4g,mode=1777",
                    "--tmpfs",
                    "/var/tmp:rw,nosuid,nodev,size=4g,mode=1777",
                    "--memory",
                    "6g",
                    "--cpus",
                    "4",
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
        results = re.findall(rb"AUDITCORE_VM_RESULT=([A-Za-z0-9+/=]+)", console)
        if len(results) != 1:
            raise ValueError("Expected exactly one complete guest result; inspect console.log")
        report["guest"] = json.loads(base64.b64decode(results[0], validate=True))
        report["status"] = report["guest"]["status"] if completed.returncode == 0 else "FAIL"
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report.update(status="FAIL", error=f"{type(exc).__name__}: {exc}")
    finally:
        subprocess.run(["docker", "rm", "-f", container], capture_output=True, check=False)
        (args.output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
