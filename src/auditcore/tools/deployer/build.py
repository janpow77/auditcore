"""Reproducible Debian staging without target-server build tooling or downloads."""

from __future__ import annotations

import email.parser
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from auditcore.exceptions import MigrationBlocked
from auditcore.tools.apprefactor.engine import source_digest
from auditcore.tools.common import digest, read_json, run, safe_path, write_json
from auditcore.tools.deployer.models import (
    ApplicationDeploymentProfile,
    DebianPackageBuild,
    DeploymentPlan,
)
from auditcore.tools.deployer.smoke import load_cases, smoke_required
from auditcore.tools.deployer.templating import render_template, template_manifest
from auditcore.tools.quality.scanners import scan_sensitive
from auditcore.tools.workflow import DEPLOY_STATES, StateMachine


class ApplicationInspection:
    """Manifest-based application discovery without executing build scripts."""

    def inspect(self, root: Path) -> dict[str, Any]:
        """Identify build, service and migration inputs; do not guess an entrypoint."""
        names = (
            "pyproject.toml",
            "package.json",
            "Dockerfile",
            "docker-compose.yml",
            "alembic.ini",
            "auditcore-deploy.json",
            "auditcore-context.json",
        )
        found = {
            name: sorted(
                p.relative_to(root).as_posix()
                for p in root.rglob(name)
                if not {"node_modules", ".venv", ".git"}.intersection(p.parts)
            )
            for name in names
        }
        return {
            "application": root.name,
            "files": found,
            "status": "PASS" if found["auditcore-deploy.json"] else "REVIEW_REQUIRED",
            "requirements": sorted(
                p.relative_to(root).as_posix() for p in root.glob("requirements*.txt")
            ),
        }


def _validate(profile: ApplicationDeploymentProfile) -> None:
    if profile.schema_version != 1:
        raise ValueError("Unsupported deployment schema")
    if not re.fullmatch(r"[a-z][a-z0-9+.-]{1,60}", profile.application):
        raise ValueError("Invalid Debian application name")
    if not re.fullmatch(r"[0-9][A-Za-z0-9.+:~\-]*", profile.version):
        raise ValueError("Invalid Debian version")
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,30}", profile.service_user or profile.application):
        raise ValueError("Invalid service user")
    if profile.service_user == "root":
        raise ValueError("Root service user is forbidden")
    if profile.package_architecture not in {"all", "amd64", "arm64"}:
        raise ValueError("Unsupported architecture")
    if profile.source_date_epoch <= 0:
        raise ValueError("Reproducible build requires source_date_epoch")
    if not profile.entrypoint or any(
        "\n" in arg or "\r" in arg or "%" in arg for arg in profile.entrypoint
    ):
        raise ValueError("Invalid service entrypoint")
    if profile.entrypoint[0] != "/usr/bin/python3":
        raise ValueError("Entrypoint must use the declared Debian Python runtime")
    for dependency in profile.system_dependencies:
        if not re.fullmatch(r"[a-z0-9][a-z0-9+.-]*(?: \([<>=]+ [A-Za-z0-9.+:~\-]+\))?", dependency):
            raise ValueError("Invalid Debian dependency")
    if profile.strategy not in {
        "DEBIAN_NATIVE_PYTHON",
        "WHEELHOUSE",
        "BUNDLED_VENV",
        "STATIC_FRONTEND",
    }:
        raise ValueError("Unsupported runtime strategy")
    if profile.strategy in {"WHEELHOUSE", "BUNDLED_VENV"} and not profile.wheel_hashes:
        raise ValueError("Offline runtime requires wheel hashes")
    for name in profile.persistent_directories:
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", name):
            raise ValueError("Invalid data directory")


def systemd_unit(profile: ApplicationDeploymentProfile) -> str:
    """Render a hardened service with a dedicated account and writable data only."""
    _validate(profile)
    name = profile.application
    user = profile.service_user or name
    entrypoint = list(profile.entrypoint)
    if profile.strategy == "BUNDLED_VENV":
        entrypoint[0] = f"/opt/{name}/runtime/bin/python3"
    runtime_path = f"/opt/{name}/runtime"
    if profile.strategy == "BUNDLED_VENV":
        runtime_path += "/site-packages"
    args = " ".join('"' + a.replace("\\", "\\\\").replace('"', '\\"') + '"' for a in entrypoint)
    return render_template("systemd", name=name, user=user, runtime_path=runtime_path, args=args)


def _copy_tree(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        if {"__pycache__", ".git", ".venv", "node_modules", ".auditcore"}.intersection(
            relative.parts
        ):
            continue
        if path.is_symlink():
            raise ValueError("Package inputs may not contain symlinks")
        if path.is_file():
            if path.name == ".env" or path.suffix in {".pem", ".key"}:
                raise ValueError("Secret-like file in package source")
            if path.suffix in {".py", ".json", ".toml", ".txt", ".env"}:
                findings = scan_sensitive(path.read_text(errors="replace"))
                if any(f.code == "AC-SEC-001" for f in findings):
                    raise ValueError("Credential-like content in package source")
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)


def build_sbom(stage: Path, profile: ApplicationDeploymentProfile) -> dict[str, Any]:
    """Generate CycloneDX 1.6 components from actual staged files and dist-info metadata."""
    components = []
    for path in sorted(stage.rglob("METADATA")):
        if not path.parent.name.endswith(".dist-info"):
            continue
        metadata = email.parser.Parser().parsestr(path.read_text())
        components.append(
            {
                "type": "library",
                "name": metadata["Name"],
                "version": metadata["Version"],
                "purl": f"pkg:pypi/{metadata['Name']}@{metadata['Version']}",
            }
        )
    for path in sorted(stage.rglob("*")):
        if path.is_symlink():
            components.append(
                {
                    "type": "file",
                    "name": path.relative_to(stage).as_posix(),
                    "properties": [{"name": "auditcore:symlink", "value": os.readlink(path)}],
                }
            )
        elif path.is_file():
            components.append(
                {
                    "type": "file",
                    "name": path.relative_to(stage).as_posix(),
                    "hashes": [{"alg": "SHA-256", "content": digest(path.read_bytes())}],
                }
            )
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "name": profile.application,
                "version": profile.version,
            },
            "tools": {
                "components": [{"type": "application", "name": "auditcore", "version": "0.1.0"}]
            },
        },
        "components": components,
        "properties": [
            {
                "name": "auditcore:system-dependencies",
                "value": json.dumps(profile.system_dependencies),
            },
            {
                "name": "auditcore:scope-limit",
                "value": "Staged payload; Debian dependency closure resolved at install",
            },
        ],
    }


class DeploymentBuilder:
    """Build only source-bound ready handoffs; package release needs install evidence."""

    def plan(self, root: Path) -> DeploymentPlan:
        """Load deployment configuration and validate the application handoff."""
        profile = ApplicationDeploymentProfile(**read_json(root / "auditcore-deploy.json"))
        _validate(profile)
        handoff_path = root / ".auditcore/deployment-handoff.json"
        handoff = read_json(handoff_path) if handoff_path.exists() else {}
        policy = handoff.get("policy", {})
        blockers = []
        if handoff.get("status") != "READY_FOR_DEPLOYMENT":
            blockers.append("READY_FOR_DEPLOYMENT handoff missing")
        if handoff.get("source_digest") != source_digest(root) or (
            profile.source_digest != source_digest(root)
        ):
            blockers.append("Stale source evidence")
        if profile.source_commit != run(["git", "rev-parse", "HEAD"], root).strip():
            blockers.append("Source commit mismatch")
        if (
            policy.get("overall_status") != "PASS"
            or policy.get("source_status") != "POLICY_SOURCE_CURRENT"
        ):
            blockers.append("Deployment policy unresolved")
        checks = handoff.get("tests", {}).get("checks", {})
        from auditcore.tools.apprefactor.engine import REQUIRED_VERIFICATION

        if any(checks.get(key, {}).get("status") != "PASS" for key in REQUIRED_VERIFICATION):
            blockers.append("Mandatory verification incomplete")
        deployment_checks = handoff.get("deployment_checks", {})
        required = (
            "protection_need",
            "service_user",
            "permissions",
            "secrets",
            "configuration",
            "logging",
            "backup_restore",
            "network",
            "proxy",
            "health",
            "dependencies",
            "sbom",
            "supply_chain",
            "updates",
        )
        for check in required:
            evidence = deployment_checks.get(check, {})
            if evidence.get("status") not in {"PASS", "NOT_APPLICABLE_WITH_REASON"} or not (
                evidence.get("reference") and evidence.get("reason")
            ):
                blockers.append(f"Deployment evidence required: {check}")
        if smoke_required(profile.deployment_target):
            try:
                load_cases(profile.functional_smoke)
            except (TypeError, ValueError) as exc:
                blockers.append(f"Functional smoke required: {exc}")
        name = profile.application
        return DeploymentPlan(
            profile,
            {
                "application": f"/opt/{name}/application",
                "runtime": f"/opt/{name}/runtime",
                "frontend": f"/opt/{name}/frontend",
                "config": f"/etc/{name}",
                "data": f"/var/lib/{name}",
                "systemd": "/usr/lib/systemd/system",
            },
            systemd_unit(profile),
            profile.health_url,
            policy.get("overall_status", "REVIEW_REQUIRED"),
            handoff.get("status", "NOT_EXECUTED"),
            "BLOCKED" if blockers else "PLANNED",
            blockers,
        )

    def _runtime(self, root: Path, stage: Path, profile: ApplicationDeploymentProfile) -> None:
        if profile.strategy not in {"WHEELHOUSE", "BUNDLED_VENV"}:
            return
        wheelhouse = safe_path(root, profile.wheelhouse)
        for name, expected in profile.wheel_hashes.items():
            path = safe_path(wheelhouse, name)
            if path.suffix != ".whl" or digest(path.read_bytes()) != expected:
                raise ValueError("Wheel digest mismatch")
            if profile.package_architecture == "all" and not path.name.endswith("none-any.whl"):
                raise ValueError("Native wheels require an explicit target architecture")
        if not profile.python_requirements or any(
            "==" not in r for r in profile.python_requirements
        ):
            raise ValueError("Offline requirements must be pinned")
        target = stage / f"opt/{profile.application}/runtime"
        if profile.strategy == "BUNDLED_VENV":
            (target / "bin").mkdir(parents=True)
            (target / "bin/python3").symlink_to("/usr/bin/python3")
            (target / "pyvenv.cfg").write_text(
                "home = /usr/bin\ninclude-system-site-packages = false\n"
            )
            target = target / "site-packages"
        # Install only explicitly hashed wheels; reject extra unreviewed files in wheelhouse.
        with tempfile.TemporaryDirectory() as temporary:
            approved = Path(temporary)
            for name in profile.wheel_hashes:
                shutil.copyfile(wheelhouse / name, approved / name)
            run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--no-index",
                    "--no-compile",
                    "--only-binary=:all:",
                    "--find-links",
                    str(approved),
                    "--target",
                    str(target),
                    *profile.python_requirements,
                ],
                timeout=300,
            )
        # pip scripts contain build-machine shebangs; service runs modules through /usr/bin/python3.
        scripts = target / "bin"
        if scripts.exists():
            shutil.rmtree(scripts)

    def _stage(self, root: Path, stage: Path, plan: DeploymentPlan) -> dict[str, Any]:
        profile, name = plan.profile, plan.profile.application
        control = stage / "DEBIAN"
        control.mkdir(parents=True)
        _copy_tree(safe_path(root, profile.source_directory), stage / f"opt/{name}/application")
        self._runtime(root, stage, profile)
        if profile.frontend_directory:
            frontend = safe_path(root, profile.frontend_directory)
            for command in profile.frontend_commands:
                run(command, frontend, timeout=300)
            _copy_tree(
                safe_path(frontend, profile.frontend_build_output), stage / f"opt/{name}/frontend"
            )
        config = stage / f"etc/{name}"
        config.mkdir(parents=True)
        conffiles = []
        configuration = {
            f"{name}.env": "# Deployment configuration; no embedded credentials.\n",
            **profile.configuration_files,
        }
        for filename, content in configuration.items():
            destination = safe_path(config, filename)
            if scan_sensitive(content):
                raise ValueError("Configuration requires secret/privacy review")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content)
            destination.chmod(0o640)
            conffiles.append(f"/etc/{name}/{filename}")
        (control / "conffiles").write_text("\n".join(sorted(conffiles)) + "\n")
        units = stage / "usr/lib/systemd/system"
        units.mkdir(parents=True)
        (units / f"{name}.service").write_text(plan.service_definition)
        (control / "control").write_text(
            render_template(
                "control",
                name=name,
                version=profile.version,
                architecture=profile.package_architecture,
                depends=", ".join(profile.system_dependencies),
            )
        )
        user = profile.service_user or name
        directories = " ".join(f"/var/lib/{name}/{d}" for d in profile.persistent_directories)
        (control / "postinst").write_text(
            render_template(
                "postinst",
                name=name,
                user=user,
                directories=directories,
                start_commands=(
                    f"systemctl enable {name}.service\nsystemctl restart {name}.service"
                    if profile.start_on_install
                    else ""
                ),
            )
        )
        (control / "prerm").write_text(render_template("prerm", name=name))
        (control / "postrm").write_text(render_template("postrm"))
        for script in ("postinst", "prerm", "postrm"):
            (control / script).chmod(0o755)
        manifest = {
            "application": name,
            "version": profile.version,
            "git_commit": profile.source_commit,
            "auditcore_version": profile.shared_library_versions.get("auditcore", "UNKNOWN"),
            "shared_libraries": profile.shared_library_versions,
            "built_at": datetime.fromtimestamp(profile.source_date_epoch, UTC).isoformat(),
            "quality_status": "PASS",
            "ci_run": profile.ci_run,
            "runtime_strategy": profile.strategy,
            "templates": template_manifest(),
            "entrypoint": profile.entrypoint,
            "health_url": profile.health_url,
            "service_user": profile.service_user or name,
            "source_digest": profile.source_digest,
            "release_status": "NOT_EXECUTED",
            "package_installation": "NOT_EXECUTED",
            "system_dependencies": profile.system_dependencies,
        }
        write_json(stage / f"opt/{name}/build-manifest.json", manifest)
        return manifest

    def build_application(
        self, root: Path | str, output: Path = Path("dist"), dry_run: bool = False
    ) -> DebianPackageBuild | DeploymentPlan:
        """Build a candidate .deb after policy/handoff validation, without deploying it."""
        root = Path(root).resolve()
        plan = self.plan(root)
        if dry_run:
            return plan
        if plan.blockers:
            raise MigrationBlocked("; ".join(plan.blockers))
        workflow = StateMachine(DEPLOY_STATES)
        for state in ("APPLICATION_INSPECTED", "DEPLOYMENT_PLAN_CREATED", "QUALITY_VERIFIED"):
            workflow.transition(state, {"status": "PASS", "reference": plan.profile.source_digest})
        output = output.resolve()
        output.mkdir(parents=True, exist_ok=True)
        profile = plan.profile
        basename = f"{profile.application}_{profile.version}_{profile.package_architecture}"
        package = output / f"{basename}.deb"
        with tempfile.TemporaryDirectory(prefix="auditcore-package-") as temporary:
            stage = Path(temporary) / "root"
            manifest = self._stage(root, stage, plan)
            for state in ("BACKEND_BUILT", "FRONTEND_BUILT", "PACKAGE_STAGED"):
                workflow.transition(
                    state,
                    {
                        "status": "NOT_APPLICABLE_WITH_REASON"
                        if state == "FRONTEND_BUILT" and not profile.frontend_directory
                        else "PASS",
                        "reference": profile.source_digest,
                        "reason": "Frontend only when configured",
                    },
                )
            sbom = build_sbom(stage, profile)
            sbom_path = output / f"{basename}_sbom.json"
            write_json(sbom_path, sbom)
            manifest["sbom_sha256"] = digest(sbom_path.read_bytes())
            for path in sorted(stage.rglob("*")):
                os.utime(
                    path,
                    (profile.source_date_epoch, profile.source_date_epoch),
                    follow_symlinks=False,
                )
                if path.is_symlink():
                    continue
                if path.is_dir():
                    path.chmod(0o755)
                elif path.parent.name != "DEBIAN" or path.name not in {
                    "postinst",
                    "prerm",
                    "postrm",
                }:
                    path.chmod(0o640 if "etc" in path.relative_to(stage).parts else 0o644)
            os.utime(stage, (profile.source_date_epoch, profile.source_date_epoch))
            environment = {**os.environ, "SOURCE_DATE_EPOCH": str(profile.source_date_epoch)}
            result = subprocess.run(
                ["dpkg-deb", "--root-owner-group", "--build", str(stage), str(package)],
                env=environment,
                capture_output=True,
                timeout=120,
                check=False,
            )
            if result.returncode:
                raise RuntimeError("Debian package build failed")
        sha = digest(package.read_bytes())
        workflow.transition("DEB_BUILT", {"status": "PASS", "reference": sha})
        write_json(output / f"{basename}_workflow.json", workflow.history)
        manifest_path = output / f"{basename}_build-manifest.json"
        write_json(manifest_path, {**manifest, "package_sha256": sha})
        checksums = output / f"{basename}_checksums.txt"
        checksums.write_text(
            "".join(
                f"{digest(p.read_bytes())}  {p.name}\n" for p in (package, manifest_path, sbom_path)
            )
        )
        return DebianPackageBuild(
            "DEB_BUILT", str(package), sha, str(manifest_path), str(sbom_path), str(checksums)
        )
