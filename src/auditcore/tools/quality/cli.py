"""Command line quality interface."""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

from auditcore.tools.common import emit, read_json
from auditcore.tools.policy.framework import GitFrameworkPolicyProvider, context_from_project
from auditcore.tools.policy.models import ApplicabilityContext
from auditcore.tools.quality.engine import check


def main(argv: list[str] | None = None) -> int:
    """Run quality gates with explicit policy and execution evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--strict", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--no-external-tools", action="store_true")
    parser.add_argument("--api-snapshot", type=Path)
    parser.add_argument("--compare-api", type=Path)
    parser.add_argument("--supply-chain-report", type=Path)
    parser.add_argument("--framework", type=Path)
    parser.add_argument("--context", type=Path, help="Applicability context for this artifact")
    parser.add_argument("--artifact", help="Stable artifact identity for bound policy evidence")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--project", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    # Compatibility with literal paths used by specification 1.5.
    target = args.path
    if not target.exists() and str(target).startswith("src/auditcore.tools."):
        target = Path(str(target).replace("auditcore.tools.", "auditcore/tools/"))
    try:
        provider = GitFrameworkPolicyProvider(
            args.framework,
            offline=args.offline,
            cache=args.project / ".auditcore/framework-cache.json",
            artifact=args.artifact or str(target),
            artifact_root=target,
            evidence=read_json(args.project / ".auditcore/policy-evidence.json")
            if (args.project / ".auditcore/policy-evidence.json").exists()
            else None,
            decisions=read_json(args.project / ".auditcore/policy-decisions.json")
            if (args.project / ".auditcore/policy-decisions.json").exists()
            else None,
        )
        context = (
            ApplicabilityContext.from_dict(read_json(args.context))
            if args.context
            else context_from_project(args.project)
        )
        policy = provider.evaluate(context)
        report = check(
            target,
            policy=policy,
            external=not args.no_external_tools,
            compare_api=args.compare_api,
            snapshot_path=args.api_snapshot,
            project=args.project,
            supply_chain_report=args.supply_chain_report,
        )
        if args.format == "json":
            emit(report.to_dict(), args.output)
        else:
            if args.output:
                from auditcore.tools.common import write_json

                write_json(args.output, report.to_dict())
            print(f"Quality: {report.status}; {len(report.findings)} findings")
            for finding in report.findings:
                print(
                    f"{finding.status} {finding.code} {finding.path}:{finding.line} "
                    f"{finding.message}"
                )
        config_path = args.project / "pyproject.toml"
        config = tomllib.loads(config_path.read_text()) if config_path.exists() else {}
        configured_strict = (
            config.get("tool", {}).get("auditcore-bibquality", {}).get("strict", False)
        )
        return report.exit_code(configured_strict if args.strict is None else args.strict)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Quality error: {type(exc).__name__}", file=sys.stderr)
        return 2
