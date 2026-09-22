"""Build and validate Debian application packages."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from auditcore.exceptions import MigrationBlocked
from auditcore.tools.common import emit, read_json, serializable, write_json
from auditcore.tools.deployer.apt import AptRepository
from auditcore.tools.deployer.build import ApplicationInspection, DeploymentBuilder
from auditcore.tools.deployer.validation import DockerPackageTester


def main(argv: list[str] | None = None) -> int:
    """Inspect, plan, build, test and publish using explicit release inputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("inspect", "plan", "build"):
        item = sub.add_parser(command)
        item.add_argument("path", type=Path)
        item.add_argument("--dry-run", action="store_true")
        item.add_argument("--output", type=Path, default=Path("dist"))
        item.add_argument("--format", choices=["json", "text"], default="json")
    test = sub.add_parser("test-package")
    test.add_argument("package", type=Path)
    upgrade = sub.add_parser("test-upgrade")
    upgrade.add_argument("old", type=Path)
    upgrade.add_argument("new", type=Path)
    apt = sub.add_parser("apt-repo")
    apt.add_argument("action", choices=["build", "publish"])
    apt.add_argument("directory", type=Path)
    apt.add_argument("--signing-key")
    apt.add_argument("--destination", type=Path)
    sub.add_parser("status")
    args = parser.parse_args(argv)
    result: Any
    try:
        if args.command == "inspect":
            result = ApplicationInspection().inspect(args.path)
        elif args.command == "plan":
            result = DeploymentBuilder().plan(args.path)
        elif args.command == "build":
            result = DeploymentBuilder().build_application(args.path, args.output, args.dry_run)
        elif args.command in {"test-package", "test-upgrade"}:
            tester = DockerPackageTester()
            tester.prepare()
            result = (
                tester.test(args.package)
                if args.command == "test-package"
                else tester.test_upgrade(args.old, args.new)
            )
        elif args.command == "apt-repo":
            apt_repository = AptRepository()
            if args.action == "build":
                result = apt_repository.build(args.directory, args.signing_key)
            else:
                if not args.destination:
                    raise ValueError("Explicit publish destination required")
                apt_repository.publish(args.directory, args.destination)
                result = {"status": "PUBLISHED"}
        else:
            path = Path(".auditcore/deployer-status.json")
            result = read_json(path) if path.exists() else {"status": "NOT_EXECUTED"}
        emit(result)
        if args.command != "status" and not getattr(args, "dry_run", False):
            write_json(Path(".auditcore/deployer-status.json"), result)
        status = serializable(result).get("status", "UNKNOWN")
        return 1 if status in {"FAIL", "BLOCKED", "MIGRATION_BLOCKED"} else 0
    except (MigrationBlocked, OSError, RuntimeError, ValueError) as exc:
        emit({"status": "BLOCKED", "reason": str(exc)})
        return 1
