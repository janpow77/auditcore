"""Verify actual Regulierung packages in a disposable offline systemd QEMU guest.

The supplied guest image must provide repositories for every declared package dependency.
No target package, PostgreSQL cluster or service is installed on the host.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import uuid
from collections.abc import Callable
from pathlib import Path

DOCKERFILE = """ARG GUEST_IMAGE=ubuntu:24.04
FROM ${GUEST_IMAGE} AS guest
ENV DEBIAN_FRONTEND=noninteractive
RUN printf '#!/bin/sh\\nexit 101\\n' > /usr/sbin/policy-rc.d && chmod +x /usr/sbin/policy-rc.d
RUN apt-get update && apt-get install -y --no-install-recommends \\
 python3 systemd systemd-sysv linux-image-virtual ca-certificates gnupg apt-utils curl
COPY old.deb new.deb /packages/
# Target platform and reviewed database pins come from the package control fields
# (Regulierung-*); packages without them fall back to PostgreSQL 16, unpinned.
RUN . /etc/os-release \
 && field() { dpkg-deb -f /packages/new.deb "$1"; } \
 && pg=$(field Regulierung-PostgreSQL) && pg=${pg:-16} \
 && tsdb=$(field Regulierung-TimescaleDB) && postgis=$(field Regulierung-PostGIS) \
 && curl -fsSL https://packagecloud.io/timescale/timescaledb/gpgkey \
 | gpg --dearmor -o /usr/share/keyrings/timescaledb.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/timescaledb.gpg] \
https://packagecloud.io/timescale/timescaledb/ubuntu/ $VERSION_CODENAME main" \
 > /etc/apt/sources.list.d/timescaledb.list \
 && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc \
 | gpg --dearmor -o /usr/share/keyrings/pgdg.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/pgdg.gpg] \
https://apt.postgresql.org/pub/repos/apt $VERSION_CODENAME-pgdg main" \
 > /etc/apt/sources.list.d/pgdg.list \
 && apt-get update && apt-get install -y --no-install-recommends redis-server \
 postgresql-$pg postgresql-$pg-postgis-3${postgis:+=$postgis} \
 postgresql-$pg-postgis-3-scripts${postgis:+=$postgis} \
 timescaledb-2-postgresql-$pg${tsdb:+=$tsdb} timescaledb-2-loader-postgresql-$pg${tsdb:+=$tsdb} \
 && echo "shared_preload_libraries='timescaledb'" \
 >> /etc/postgresql/$pg/main/postgresql.conf
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
# Docker markers must not make systemd inside QEMU ignore the kernel command line.
RUN rm -f /guest/.dockerenv /guest/run/.containerenv /guest/run/systemd/container
RUN echo '127.0.0.1 localhost' > /guest/etc/hosts \
 && echo '::1 localhost' >> /guest/etc/hosts \
 && cp /guest/boot/vmlinuz-* /kernel && cp /guest/boot/initrd.img-* /initrd \\
 && truncate -s 12G /disk.raw && mkfs.ext4 -q -F -d /guest /disk.raw \\
 && chmod 0644 /kernel /initrd /disk.raw && rm -rf /guest
USER 65534:65534
# Accelerator and CPU model are appended at run time (see accelerator_arguments).
ENTRYPOINT ["qemu-system-x86_64", "-m", "4096", "-smp", "4", \\
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


KVM_DEVICE = Path("/dev/kvm")
#: Named CPU model under KVM instead of the host CPU, so a pass does not depend
#: on the test machine's extensions. Westmere = x86-64-v2 plus AES-NI and
#: PCLMULQDQ (QEMU's ``x86-64-v2-AES`` ABI model is missing in QEMU 8.2). The
#: regulierung runtime needs AES-NI/PCLMULQDQ: with Nehalem (plain x86-64-v2)
#: the backend of 2026.11.12-1 and 2026.11.13-1 crash-loops, with Westmere both
#: pass (measured 13.11.2026).
KVM_CPU = "Westmere"


def kvm_usable(device: Path = KVM_DEVICE) -> bool:
    """True when the KVM device is usable for the unprivileged container user.

    The guest runs as UID 65534 and reaches the device only through its group,
    so group read-write permission is required in addition to the caller's own
    access (``os.access`` is always true for root).
    """
    try:
        mode = device.stat().st_mode
    except OSError:
        return False
    group_rw = stat.S_IRGRP | stat.S_IWGRP
    return (
        stat.S_ISCHR(mode) and mode & group_rw == group_rw and os.access(device, os.R_OK | os.W_OK)
    )


def docker_passes_devices() -> bool:
    """True when the Docker daemon is local, rootful and without userns-remap.

    Only then does ``--device``/``--group-add`` give the container the host's
    /dev/kvm with the host's group ID.
    """
    host = os.environ.get("DOCKER_HOST", "")
    if host and not host.startswith("unix://"):
        return False
    try:
        info = subprocess.run(
            ["docker", "info", "--format", "{{json .SecurityOptions}}"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        ).stdout
        options = json.loads(info or "[]") or []
    except (OSError, subprocess.SubprocessError, ValueError):
        return False
    return not any("rootless" in o or "userns" in o for o in options)


def resolve_accelerator(
    requested: str,
    device: Path = KVM_DEVICE,
    daemon_ok: Callable[[], bool] = docker_passes_devices,
) -> str:
    """Map --accel auto|kvm|tcg to the accelerator actually used."""
    if requested == "tcg":
        return "tcg"
    if kvm_usable(device) and daemon_ok():
        return "kvm"
    if requested == "kvm":
        raise ValueError(
            f"--accel kvm requested, but {device} is not usable for the container "
            "(missing, no group read-write access, rootless/userns or remote Docker)"
        )
    return "tcg"


def accelerator_arguments(
    accelerator: str, device: Path = KVM_DEVICE
) -> tuple[list[str], list[str]]:
    """Return (docker run options, QEMU arguments) for the chosen accelerator.

    TCG emulates ``-cpu max`` (x86-64-v2 and newer, needed by the NumPy wheel).
    KVM uses the named baseline model `KVM_CPU`; the unprivileged container user
    gets the device's group so it can open /dev/kvm without capabilities.
    """
    if accelerator == "kvm":
        gid = device.stat().st_gid
        return (
            ["--device", str(device), "--group-add", str(gid)],
            ["-accel", "kvm", "-cpu", KVM_CPU],
        )
    return [], ["-accel", "tcg", "-cpu", "max"]


def host_cpu_model() -> str:
    """CPU model of the test machine for the report (empty when unknown)."""
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return ""


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
    parser.add_argument(
        "--accel",
        choices=("auto", "kvm", "tcg"),
        default="auto",
        help="QEMU accelerator: auto uses KVM when /dev/kvm is usable, otherwise TCG",
    )
    args = parser.parse_args()
    try:
        accelerator = resolve_accelerator(args.accel)
    except ValueError as exc:
        parser.error(str(exc))
    docker_options, qemu_arguments = accelerator_arguments(accelerator)
    args.output.mkdir(parents=True, exist_ok=True, mode=0o700)
    configuration = json.loads(args.configuration.read_text())
    run_id = uuid.uuid4().hex[:12]
    image = f"auditcore-regulierung-test:{run_id}"
    container = f"auditcore-regulierung-test-{run_id}"
    report: dict = {
        "status": "NOT_EXECUTED",
        "runtime": f"offline QEMU {accelerator.upper()}, real systemd",
        "accelerator": accelerator,
        "accelerator_requested": args.accel,
        "qemu_arguments": qemu_arguments,
        "host_cpu": host_cpu_model(),
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
                    *docker_options,
                    image,
                    *qemu_arguments,
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
