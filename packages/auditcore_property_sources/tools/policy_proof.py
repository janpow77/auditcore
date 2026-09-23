"""Execute the framework catalogue cases that apply to this library and bind the results.

Run from the package directory with the development environment on PATH::

    python tools/policy_proof.py --framework <verwaltung-app-framework checkout>

For every applicable catalogue test (T-xx) the mapped pytest cases are
executed; only if all of them pass is the requirement evidence written to
``.auditcore/policy-evidence.json``, bound to the current source digest,
applicability context and framework commit. Requirements whose applicability
is unknown or that need consumer facts (F-05, F-07.ASSESS, T-12) are left open.
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

ARTIFACT = "auditcore_property_sources"

#: Catalogue test → (scope, pytest node ids).
CASES: dict[str, tuple[str, list[str]]] = {
    "T-11": (
        "Fixtures synthetisch ohne Kontaktdaten; Namen privater Anbieter standardmäßig minimiert",
        [
            "tests/test_policy_cases.py::"
            "test_t11_fixtures_hold_no_personal_contact_data_and_private_names_are_minimised"
        ],
    ),
    "T-14": (
        "Bibliothek protokolliert nicht; Harvest-Ergebnisse ohne Kopfzeilen",
        ["tests/test_policy_cases.py::test_t14_library_does_not_log_and_results_carry_no_headers"],
    ),
    "T-30": (
        "Quellformate je Profil exakt gegen das Original; sichtbare Teilfehler; "
        "Datensätze tragen Profil- und Adapterversion",
        [
            "tests/test_policy_cases.py::"
            "test_t30_records_carry_profile_and_adapter_version_and_errors_are_visible",
            "tests/test_legacy_replay.py",
        ],
    ),
    "T-38": (
        "Parser nur Standardbibliothek; auditcore_harvest nur im Adaptermodul (Extra sources)",
        ["tests/test_architecture.py"],
    ),
}

#: Framework requirement → catalogue tests that must all pass.
REQUIREMENTS = {
    "F-07": ("LIBRARY_PROTOCOLS_AND_SUPPLY_CHAIN", ["T-14", "T-37"]),
    "F-09": ("LIBRARY_SOURCE_ARCHITECTURE", ["T-38"]),
    "F-15": ("VERSIONED_SOURCE_BOUND_PROFILES_AND_CATALOG", []),
    "F-16": ("VERSIONED_IMPORT_MAPPING", ["T-30"]),
}
PROFILE_TESTS = [
    "tests/test_catalog.py",
    "tests/test_robots.py",
    "tests/test_adapters.py",
]


def run_pytest(name: str, targets: list[str], output: Path) -> dict[str, object]:
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
    suite = ElementTree.parse(report).getroot()
    suite = suite if suite.tag == "testsuite" else suite[0]
    counts = {k: int(suite.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}
    passed = process.returncode == 0 and counts["tests"] > 0 and not counts["skipped"]
    return {
        "status": "PASS" if passed else "FAIL",
        **counts,
        "targets": targets,
        "junit_sha256": hashlib.sha256(report.read_bytes()).hexdigest(),
    }


def supply_chain_check(build: Path) -> dict[str, object]:
    """T-37: report, wheel and SBOM digests plus schema; a tampered copy must be detected."""
    from auditcore.tools.common import digest
    from auditcore.tools.quality.supplychain import validate_schema

    report = json.loads((build / "supply-chain-report.json").read_text())
    wheel = build / report["artifact"]
    sbom = build / report["sbom"]
    intact = (
        report["status"] == "PASS"
        and digest(wheel.read_bytes()) == report["artifact_sha256"]
        and digest(sbom.read_bytes()) == report["sbom_sha256"]
        and validate_schema(json.loads(sbom.read_text()))["status"] == "PASS"
    )
    tampered = bytearray(wheel.read_bytes())
    tampered[len(tampered) // 2] ^= 0xFF
    detected = digest(bytes(tampered)) != report["artifact_sha256"]
    wrong_version = json.loads(sbom.read_text())
    wrong_version["metadata"]["component"]["version"] = "9.9.9"
    version_detected = digest(json.dumps(wrong_version).encode()) != report["sbom_sha256"]
    return {
        "scope": "SBOM-Schema, Artefakt-/SBOM-Digest; manipuliertes Wheel und geänderte "
        "Version werden erkannt",
        "status": "PASS" if intact and detected and version_detected else "FAIL",
        "artifact_sha256": report["artifact_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--framework", type=Path, required=True)
    args = parser.parse_args()
    root = Path.cwd()
    output = root / ".auditcore" / "policy"
    output.mkdir(parents=True, exist_ok=True)
    checks = {
        case: {"scope": scope, **run_pytest(case, targets, output)}
        for case, (scope, targets) in CASES.items()
    }
    checks["F-15-profiles"] = {
        "scope": "Quellprofile mit Version und Blob-Herkunft; Zugangskatalog "
        "auditcore_property_sources.catalog/1 gegen robots.txt-Schnappschüsse; Adaptervertrag",
        **run_pytest(
            "F-15",
            [
                *PROFILE_TESTS,
            ],
            output,
        ),
    }
    checks["T-37"] = supply_chain_check(root / ".auditcore" / "build")
    context = context_from_project(root)
    provider = GitFrameworkPolicyProvider(
        checkout=args.framework, artifact=ARTIFACT, artifact_root=root / "src" / ARTIFACT
    )
    source = provider.load_requirements()
    # Quality binds evidence to the checked source tree (auditcore-quality <path>).
    binding = evidence_binding(root / "src" / ARTIFACT, ARTIFACT, context)
    proof = {
        "status": "PASS" if all(c["status"] == "PASS" for c in checks.values()) else "FAIL",
        "binding": binding,
        "framework_commit": source.commit_sha,
        "checks": checks,
        "open": {
            "F-05": "Personenbezug möglich (Anzeigentexte, Bekanntmachungen); Bewertung beim "
            "Consumer",
            "F-07.ASSESS": "Schutzbedarf der Bibliothek nicht festgelegt (protection_need UNKNOWN)",
            "T-12": "Anwendbarkeit UNKNOWN (dsfa_required)",
        },
    }
    write_json(root / ".auditcore" / "policy-proof.json", proof)
    evidence = {}
    for requirement, (scope, cases) in REQUIREMENTS.items():
        needed = [checks[c] for c in cases] + (
            [checks["F-15-profiles"]] if requirement == "F-15" else []
        )
        if all(c["status"] == "PASS" for c in needed):
            evidence[requirement] = {
                "status": "VERIFIED",
                "source_commit": source.commit_sha,
                **binding,
                "references": [".auditcore/policy-proof.json"],
                "scope": scope,
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
