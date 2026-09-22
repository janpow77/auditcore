"""Execute the framework catalogue cases that apply to this library and bind the results.

Run from the package directory with the development environment on PATH::

    python tools/policy_proof.py --framework <verwaltung-app-framework checkout>

Evidence is written only for requirements whose mapped cases all passed; it is
bound to the source digest of ``src/auditcore_funding_sources``, the
applicability context and the framework commit. F-05, F-07.ASSESS and T-12
depend on consumer facts (``personal_data``/``dsfa_required``/``protection_need``)
and stay open.
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

ARTIFACT = "auditcore_funding_sources"

CASES: dict[str, tuple[str, list[str]]] = {
    "T-09": (
        "Übergabe enthält jede Zeile mit Rohwert, Profil-/Adapterversion und Provenienz; "
        "Replay aller Originalausgaben exakt",
        [
            "tests/test_policy_cases.py::test_t09_handover_contains_every_row_with_versions_and_raw_values",
            "tests/test_adapters.py",
            "tests/test_snapshot.py",
        ],
    ),
    "T-14": (
        "Bibliothek protokolliert nicht; Ergebnisse und Ereignisse ohne Konfiguration/Zugangsdaten",
        [
            "tests/test_policy_cases.py::test_t14_no_logging_and_results_without_configuration_secrets"
        ],
    ),
    "T-30": (
        "Umbenannte/fehlende Quellspalten werden sichtbar, Zahlen-/Datumsformate folgen dem "
        "benannten, versionierten Profil",
        [
            "tests/test_policy_cases.py::test_t30_renamed_or_missing_columns_are_visible_not_silent",
            "tests/test_policy_cases.py::test_t30_number_and_date_formats_follow_the_named_profile",
            "tests/test_tables.py",
        ],
    ),
    "T-38": (
        "Laufzeitmodule: Standardbibliothek, eigenes Paket, auditcore_harvest nur in adapters.py, "
        "openpyxl nur lazy; kein DB-/HTTP-/Logging-Zugriff",
        ["tests/test_architecture.py"],
    ),
}

REQUIREMENTS = {
    "F-04": ("SOURCE_RECORD_HANDOVER", ["T-09"]),
    "F-07": ("LIBRARY_PROTOCOLS_AND_SUPPLY_CHAIN", ["T-14", "T-37"]),
    "F-09": ("LIBRARY_SOURCE_ARCHITECTURE", ["T-38"]),
    "F-15": ("VERSIONED_SOURCE_BOUND_RULE_PROFILES", []),
    "F-16": ("VERSIONED_IMPORT_PROFILES", ["T-30"]),
}
PROFILE_TESTS = ["tests/test_profiles.py", "tests/test_cumulation.py"]


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
        "scope": "Quellengebundene, versionierte Profile mit Fingerprint; Ergebnisse nennen "
        "Profil-ID/-Version; Kumulierungsprofil REVIEW_REQUIRED sichtbar",
        **run_pytest("F-15", PROFILE_TESTS, output),
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
            "F-05": "Personenbezug (Namen natürlicher Personen in Listen/Register) ist beim "
            "Consumer zu bewerten; dsfa_required UNKNOWN",
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
