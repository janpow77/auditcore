"""Application transformation CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

from auditcore.exceptions import MigrationBlocked
from auditcore.tools.apprefactor.engine import ApplicationRefactorer, verify
from auditcore.tools.apprefactor.models import ApplicationRefactoringPlan
from auditcore.tools.common import emit, read_json


def main(argv: list[str] | None = None) -> int:
    """Inspect, plan, preview, migrate and verify application changes."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("inspect", "plan", "optimize", "verify", "handoff"):
        item = sub.add_parser(command)
        item.add_argument("repository", type=Path)
        item.add_argument("--safe", action="store_true")
        item.add_argument("--output", type=Path)
    apply = sub.add_parser("apply")
    apply.add_argument("plan", type=Path)
    apply.add_argument("--dry-run", action="store_true")
    apply.add_argument("--format", choices=["json", "text"], default="json")
    sub.add_parser("status")
    args = parser.parse_args(argv)
    refactorer = ApplicationRefactorer()
    try:
        if args.command == "apply":
            result = refactorer.apply(
                ApplicationRefactoringPlan(**read_json(args.plan)), args.dry_run
            )
        elif args.command == "inspect":
            result = refactorer.inspect(args.repository)
        elif args.command == "plan":
            emit(refactorer.plan(args.repository), args.output)
            return 0
        elif args.command == "optimize":
            from auditcore.tools.apprefactor.optimization import safe_import_cleanup

            config = args.repository / "auditcore-verification.json"
            result = safe_import_cleanup(
                args.repository,
                read_json(config) if config.exists() else {},
            )
        elif args.command == "handoff":
            result = refactorer.handoff(args.repository)
        elif args.command == "verify":
            config = args.repository / "auditcore-verification.json"
            result = verify(args.repository, read_json(config) if config.exists() else {})
        else:
            path = Path(".auditcore/refactor-result.json")
            result = read_json(path) if path.exists() else {"status": "NOT_EXECUTED"}
        emit(result, getattr(args, "output", None))
        return 1 if result.get("status") in {"FAIL", "MIGRATION_BLOCKED"} else 0
    except (MigrationBlocked, ValueError, RuntimeError, OSError) as exc:
        emit({"status": "MIGRATION_BLOCKED", "reason": str(exc)})
        return 1
