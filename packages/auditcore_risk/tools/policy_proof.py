"""Execute the applicable framework catalogue cases and bind the results to the source tree.

Run from the package directory with the development environment on PATH::

    python tools/policy_proof.py --framework <verwaltung-app-framework checkout>

Evidence is written to ``.auditcore/policy-evidence.json`` only for requirements
whose mapped pytest cases all passed; it is bound to ``src/<package>``, the
applicability context and the framework commit (auditcore-quality checks it).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path

from auditcore.tools.common import write_json
from auditcore.tools.policy import GitFrameworkPolicyProvider, evidence_binding
from auditcore.tools.policy.framework import context_from_project

ARTIFACT = "auditcore_risk"
CASES: dict[str, tuple[str, list[str]]] = {
    "T-11": (
        "Namen (Begünstigte, Rechnungssteller) werden nur im Speicher verglichen",
        ["tests/test_policy_cases.py::test_t11_names_are_processed_in_memory_only"],
    ),
    "T-14": (
        "Bibliothek protokolliert nicht selbst",
        ["tests/test_policy_cases.py::test_t14_library_writes_no_logs"],
    ),
    "T-31": (
        "Gleiche Daten, Version und Profil ergeben dasselbe Ergebnis; Ergebnis nennt "
        "Bibliothek, Profil, Version und Fingerabdruck",
        ["tests/test_reproducibility.py"],
    ),
    "T-38": (
        "Laufzeit nur Standardbibliothek, eigenes Paket und auditcore_entity_matching; "
        "pandas/rapidfuzz/auditcore_procurement nur lazy",
        ["tests/test_architecture.py"],
    ),
    "F-15-profiles": (
        "Benannte, quellengebundene, versionierte Regelprofile mit Fingerabdruck ohne "
        "Standardprofil; Legacyprofile reproduzieren die ausgeführten Quellen",
        [
            "tests/test_profiles.py",
            "tests/test_replay_riskanalysis.py::test_fixture_scope_and_environment",
            "tests/test_replay_flowstat.py::test_fixture_scope_and_sources",
            "tests/test_replay_flowinvoice_risk_checker.py::test_fixture_scope",
            "tests/test_replay_flowinvoice_fraud.py::test_fixture_scope",
            "tests/test_replay_flowinvoice_verwk.py::test_fixture_scope",
            "tests/test_fraud_contract.py::test_profiles_are_explicit_and_kind_checked",
        ],
    ),
}
REQUIREMENTS = {
    "F-09": ("LIBRARY_SOURCE_ARCHITECTURE", ["T-38"]),
    "F-15": ("VERSIONED_SOURCE_BOUND_RULE_PROFILES", ["F-15-profiles"]),
    "F-17": ("REPRODUCIBLE_ANALYTICAL_RUNS", ["T-31"]),
}


def run_pytest(name: str, targets: list[str], output: Path) -> dict[str, object]:
    """Run pytest for one case and summarise its JUnit report."""
    report = output / f"{name}.xml"
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            f"--junitxml={report}",
            *targets,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    suite = ElementTree.parse(report).getroot()  # nosec B314 - own pytest report
    suite = suite if suite.tag == "testsuite" else suite[0]
    counts = {k: int(suite.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}
    passed = process.returncode == 0 and counts["tests"] > 0 and not counts["skipped"]
    return {
        "status": "PASS" if passed else "FAIL",
        **counts,
        "targets": targets,
        "junit_sha256": hashlib.sha256(report.read_bytes()).hexdigest(),
    }


def main() -> int:
    """Run cases, write proof and bound evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--framework", type=Path, required=True)
    args = parser.parse_args()
    root = Path.cwd()
    source_root = root / "src" / ARTIFACT
    output = root / ".auditcore" / "policy"
    output.mkdir(parents=True, exist_ok=True)
    checks = {
        case: {"scope": scope, **run_pytest(case, targets, output)}
        for case, (scope, targets) in CASES.items()
    }
    context = context_from_project(root)
    provider = GitFrameworkPolicyProvider(
        checkout=args.framework, artifact=ARTIFACT, artifact_root=source_root
    )
    source = provider.load_requirements()
    binding = evidence_binding(source_root, ARTIFACT, context)
    proof = {
        "status": "PASS" if all(c["status"] == "PASS" for c in checks.values()) else "FAIL",
        "binding": binding,
        "framework_commit": source.commit_sha,
        "checks": checks,
    }
    write_json(root / ".auditcore" / "policy-proof.json", proof)
    evidence = {
        requirement: {
            "status": "VERIFIED",
            "source_commit": source.commit_sha,
            **binding,
            "references": [".auditcore/policy-proof.json"],
            "scope": scope,
        }
        for requirement, (scope, cases) in REQUIREMENTS.items()
        if all(checks[c]["status"] == "PASS" for c in cases)
    }
    write_json(root / ".auditcore" / "policy-evidence.json", evidence)
    print(
        json.dumps(
            {
                "status": proof["status"],
                "verified": sorted(evidence),
                "checks": {k: v["status"] for k, v in checks.items()},
            }
        )
    )
    return 0 if proof["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
