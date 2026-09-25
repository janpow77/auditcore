"""Verify optional renderer installation and prepare hash-locked release requirements."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import urllib.parse
import urllib.request
import venv
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FEATURES = {
    "auditcore_invoicegenerator": "pdf",
    "auditcore_reporting": "excel",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build_output", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--release-version", default="0.2.0")
    parser.add_argument("--apt", action="store_true")
    parser.add_argument("--image", default="auditcore-package-test:bookworm")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", args.release_version):
        raise ValueError("Numeric release version required")
    build_output = args.build_output.resolve()
    builds = read_json(build_output / "result.json")
    if builds["status"] != "PASS":
        raise ValueError("Completed core installation verification required")
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError("New empty output required")
    output.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "scope": "OPTIONAL_RENDERER_INSTALLATION",
        "status": "RUNNING",
        "release_version": args.release_version,
        "features": {},
        "checks": {},
    }
    environment = {
        k: v
        for k, v in os.environ.items()
        if k not in {"PYTHONPATH", "PYTHONHOME"} and not k.startswith("PIP_")
    }

    def save() -> None:
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")

    def run(name: str, command: list[str]) -> None:
        process = subprocess.run(
            command, cwd=output, env=environment, capture_output=True, text=True, timeout=600
        )
        log = output / f"{name}.log"
        log.write_text(process.stdout + process.stderr)
        result["checks"][name] = {
            "status": "PASS" if process.returncode == 0 else "FAIL",
            "exit_code": process.returncode,
            "log_sha256": sha256(log),
        }
        save()
        if process.returncode:
            raise RuntimeError(f"{name} failed; see {log}")
        print(name, "PASS", flush=True)

    packages = {p["distribution"]: p for p in builds["packages"]}
    wheels = {}
    for name, package in packages.items():
        wheel = (
            build_output
            / "builds"
            / package["name"]
            / (f"{package['name']}-{package['version']}-py3-none-any.whl")
        )
        if sha256(wheel) != package["wheel_sha256"]:
            raise ValueError("Tested wheel digest changed")
        wheels[name] = wheel
    base = f"https://github.com/janpow77/auditcore/releases/download/v{args.release_version}"
    hashes_cache: dict[tuple[str, str], list[str]] = {}
    executed: list[str] = []
    for package_name, extra in FEATURES.items():
        distribution = package_name.replace("_", "-")
        if distribution not in packages:
            # Selective pull-request runs build only the affected packages.
            result["features"][extra] = {
                "package": package_name,
                "status": "NOT_EXECUTED",
                "reason": "Renderer-Paket in diesem Lauf nicht gebaut (selektive Prüfung)",
            }
            save()
            continue
        selected = {distribution}
        pending = [distribution]
        while pending:
            for requirement in packages[pending.pop()]["runtime_requirements"]:
                match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([0-9.]+)", requirement)
                if not match:
                    raise ValueError("Pinned internal dependency required")
                dependency = re.sub(r"[-_.]+", "-", match[1]).lower()
                if packages[dependency]["version"] != match[2]:
                    raise ValueError("Dependency version mismatch")
                if dependency not in selected:
                    selected.add(dependency)
                    pending.append(dependency)
        consumer = output / package_name
        venv.EnvBuilder(with_pip=True).create(consumer)
        python = str(consumer / "bin/python")
        install_report = output / f"{extra}-install.json"
        run(
            f"{extra}-install",
            [
                python,
                "-I",
                "-m",
                "pip",
                "--isolated",
                "install",
                "--index-url",
                "https://pypi.org/simple",
                "--report",
                str(install_report),
                *[
                    str(wheels[n]) + (f"[{extra}]" if n == distribution else "")
                    for n in sorted(selected)
                ],
            ],
        )
        smoke = output / f"smoke-{extra}.py"
        shutil.copyfile(
            ROOT / "packages" / package_name / "tests" / f"installed_{extra}_smoke.py", smoke
        )
        run(f"{extra}-smoke", [python, "-I", str(smoke)])
        run(
            f"{extra}-independence",
            [
                python,
                "-I",
                "-c",
                "import importlib.metadata,importlib.util; "
                "assert importlib.util.find_spec('auditcore') is None; "
                "actual={d.metadata['Name'].replace('_','-').lower() "
                "for d in importlib.metadata.distributions() "
                "if d.metadata['Name'].startswith('auditcore')}; "
                f"assert actual == {selected!r}, actual",
            ],
        )
        run(f"{extra}-pip-check", [python, "-I", "-m", "pip", "check"])
        lines = ["--index-url https://pypi.org/simple", "--require-hashes"]
        lock_wheels = {}
        for name in sorted(selected):
            wheel = wheels[name]
            suffix = f"[{extra}]" if name == distribution else ""
            lines.append(f"{name}{suffix} @ {base}/{wheel.name} --hash=sha256:{sha256(wheel)}")
            lock_wheels[wheel.name] = sha256(wheel)
        dependencies = {}
        for item in read_json(install_report)["install"]:
            name = re.sub(r"[-_.]+", "-", item["metadata"]["name"]).lower()
            if name in selected:
                continue
            version = item["metadata"]["version"]
            url = item["download_info"]["url"]
            if urllib.parse.urlsplit(url).hostname != "files.pythonhosted.org":
                raise ValueError("External renderer dependency must come from PyPI")
            key = (name, version)
            if key not in hashes_cache:
                metadata_url = (
                    "https://pypi.org/pypi/"
                    + urllib.parse.quote(name, safe="")
                    + "/"
                    + urllib.parse.quote(version, safe="")
                    + "/json"
                )
                with urllib.request.urlopen(metadata_url, timeout=60) as response:
                    upstream = json.load(response)
                hashes = sorted(
                    {u["digests"]["sha256"] for u in upstream["urls"] if not u.get("yanked")}
                )
                if not hashes or not all(re.fullmatch(r"[0-9a-f]{64}", h) for h in hashes):
                    raise ValueError("Valid distribution SHA256 hashes required")
                if item["download_info"]["archive_info"]["hashes"]["sha256"] not in hashes:
                    raise ValueError("Installed dependency is not among the upstream release files")
                hashes_cache[key] = hashes
            lines.append(
                f"{name}=={version} "
                + " ".join(f"--hash=sha256:{value}" for value in hashes_cache[key])
            )
            dependencies[name] = version
        lock = output / f"requirements-{package_name}-{extra}.txt"
        lock.write_text("\n".join(lines) + "\n")
        local_lock = output / f"local-{extra}.txt"
        contents = lock.read_text()
        for name in selected:
            contents = contents.replace(f"{base}/{wheels[name].name}", wheels[name].as_uri())
        local_lock.write_text(contents)
        run(
            f"{extra}-remove",
            [python, "-I", "-m", "pip", "uninstall", "-y", *selected, *dependencies],
        )
        run(
            f"{extra}-locked-install",
            [python, "-I", "-m", "pip", "--isolated", "install", "-r", str(local_lock)],
        )
        run(f"{extra}-locked-smoke", [python, "-I", str(smoke)])
        result["features"][extra] = {
            "package": package_name,
            "version": packages[distribution]["version"],
            "wheel_hashes": lock_wheels,
            "dependencies": dependencies,
            "requirements": lock.name,
            "requirements_sha256": sha256(lock),
            "smoke_sha256": sha256(smoke),
            "status": "PASS",
        }
        save()
        executed.append(extra)
    if args.apt and executed:
        if builds["checks"].get("apt-lifecycle", {}).get("status") != "PASS":
            raise ValueError("Signed core APT lifecycle required before renderer APT verification")
        commands = [
            "#!/bin/sh",
            "set -eu",
            "cd /tmp",
            "apt-get -o APT::Update::Error-Mode=any update",
            "apt-get install -y --no-install-recommends "
            "python3-reportlab python3-openpyxl python3-defusedxml",
            "dpkg --compare-versions \"$(dpkg-query -W -f='${Version}' python3-reportlab)\" "
            "ge 3.6.12-1+deb12u1",
            "dpkg-query -W python3-reportlab python3-openpyxl python3-defusedxml",
            "rm -f /etc/apt/sources.list /etc/apt/sources.list.d/*",
            "printf '%s\\n' 'deb [signed-by=/packages/test-keyring.gpg] "
            "file:/packages/apt-1 ./' > /etc/apt/sources.list.d/auditcore.list",
            "apt-get -o APT::Update::Error-Mode=any update",
            "apt-get install -y "
            + shlex.join(
                [f"python3-{p['distribution']}={p['version']}-1" for p in builds["packages"]]
            ),
            *(f"/usr/bin/python3 -I /proof/smoke-{extra}.py" for extra in executed),
            "apt-get remove -y "
            + shlex.join([f"python3-{p['distribution']}" for p in builds["packages"]]),
            "/usr/bin/python3 -I -c "
            + shlex.quote(
                "import importlib.util; "
                f"assert all(importlib.util.find_spec(n) is None for n in "
                f"{[p['name'] for p in builds['packages']]!r})"
            ),
        ]
        script = output / "apt-renderers.sh"
        script.write_text("\n".join(commands) + "\n")
        run(
            "apt-renderers",
            [
                "docker",
                "run",
                "--rm",
                "--mount",
                f"type=bind,src={build_output},dst=/packages,readonly",
                "--mount",
                f"type=bind,src={output},dst=/proof,readonly",
                args.image,
                "sh",
                "/proof/apt-renderers.sh",
            ],
        )
    else:
        result["checks"]["apt-renderers"] = {"status": "NOT_EXECUTED"}
    result["status"] = "PASS"
    save()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
