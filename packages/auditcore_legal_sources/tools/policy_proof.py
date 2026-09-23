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

ARTIFACT = "auditcore_legal_sources"

#: Catalogue test → (scope, pytest node ids).
CASES: dict[str, tuple[str, list[str]]] = {
    "T-09": (
        "JSON-Datensätze enthalten Identität, Profil (ID/Version/Fingerprint), Provenienz und "
        "Contenthash; Zahl und Inhalt der gelieferten Datensätze stimmen mit der Quelle überein",
        [
            "tests/test_sources.py::test_content_hash_identity_and_dedup_are_source_compatible",
            "tests/test_adapters.py::test_dip_pages_keywords_by_cursor_and_sends_key_only_as_header",
            "tests/test_adapters.py::test_eurlex_first_occurrence_wins_and_dates_are_parsed",
        ],
    ),
    "T-14": (
        "Bibliothek protokolliert nicht; Ergebnisse und Ereignisse des Harvest-Laufs enthalten "
        "keine Zugangsdaten (Contract-Fall secret_free)",
        [
            "tests/test_sources.py::test_runtime_modules_use_only_stdlib_and_no_network_or_io",
            "tests/test_adapters.py::test_contract_suite",
        ],
    ),
    "T-30": (
        "Fehlende/umbenannte Quellfelder werden als Fehler mit Fundort gemeldet, Datumsformate "
        "explizit behandelt, jede Normalisierung nennt Profil-ID/-Version/-Fingerprint",
        [
            "tests/test_sources.py::test_ls_c03_defective_items_are_errors_not_empty_documents",
            "tests/test_sources.py::test_ls_c01_dates_are_parsed_unlike_legacy",
            "tests/test_sources.py::test_ls_c05_sparql_parsing_is_strict",
            "tests/test_sources.py::test_profiles_are_explicit_versioned_and_tamper_evident",
            "tests/test_adapters.py::test_dip_defective_items_make_the_run_partial_not_silent",
        ],
    ),
    "T-38": (
        "Laufzeitmodule: Standardbibliothek, eigenes Paket und auditcore_harvest; kein Netz-, "
        "Datei-, Datenbank- oder Protokollzugriff; feedparser nur lazy im Extra",
        ["tests/test_sources.py::test_runtime_modules_use_only_stdlib_and_no_network_or_io"],
    ),
}

#: Framework requirement → catalogue tests that must all pass.
REQUIREMENTS = {
    "F-04": ("NORMALIZED_JSON_RECORDS", ["T-09"]),
    "F-07": ("LIBRARY_PROTOCOLS_AND_SUPPLY_CHAIN", ["T-14", "T-37"]),
    "F-09": ("LIBRARY_SOURCE_ARCHITECTURE", ["T-38"]),
    "F-15": ("VERSIONED_SOURCE_PROFILES", []),
    "F-16": ("VERSIONED_SOURCE_MAPPING", ["T-30"]),
}
PROFILE_TESTS = [
    "tests/test_sources.py::test_profiles_are_explicit_versioned_and_tamper_evident",
    "tests/test_sources.py::test_profile_content_equals_executed_sources",
    "tests/test_feeds.py::test_profile_feed_urls_equal_the_source",
    "tests/test_legacy_replay.py::test_designer_profile_differs_and_is_not_merged",
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
        "scope": "Zwei getrennte quellengebundene Profile mit Version, Fingerprint und Herkunft; "
        "Inhalt gleich dem ausgeführten Original, Manipulation erkennbar, keine Harmonisierung",
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
            "F-05": "Datenschutzbewertung der Bibliothek selbst hängt am Consumer; "
            "dsfa_required UNKNOWN",
            "F-07.ASSESS": "Schutzbedarf der Bibliothek nicht festgelegt (protection_need UNKNOWN)",
            "T-11": "Personenbezug möglich (Urheber/Autoren von Drucksachen); Abgleich mit "
            "einem VVT ist Aufgabe des Consumers",
            "T-12": "Anwendbarkeit UNKNOWN (dsfa_required UNKNOWN)",
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
