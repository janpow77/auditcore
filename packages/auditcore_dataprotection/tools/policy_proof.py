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

ARTIFACT = "auditcore_dataprotection"

#: Catalogue test → (scope, pytest node ids or -k expressions).
CASES: dict[str, tuple[str, list[str]]] = {
    "T-01": (
        "Objekte eines Mandanten sind unter einem anderen weder lesbar noch änderbar "
        "noch exportierbar; Repository-Fremdobjekte werden erkannt",
        [
            "tests/test_assessment_workflow.py::test_c12_tenant_binding",
            "tests/test_assessment_workflow.py::test_c12_repository_returning_foreign_record_is_detected",
            "tests/test_register.py::test_tenant_separation_and_authorization",
            "tests/test_ports_contract.py",
        ],
    ),
    "T-02": (
        "Operation ohne Berechtigung wird im Dienst verweigert (Authorizer-Port), "
        "unabhängig von einer Oberfläche",
        [
            "tests/test_register.py::test_tenant_separation_and_authorization",
            "tests/test_assessment_workflow.py::test_deny_all_and_missing_actor",
        ],
    ),
    "T-03": (
        "Entzogene Rechte wirken bei der nächsten Operation",
        ["tests/test_policy_cases.py::test_t03_revoked_rights_apply_to_the_next_operation"],
    ),
    "T-05": (
        "Unzulässige Übergänge abgewiesen, Rückgabe nach inhaltlicher Änderung, Historie erhalten",
        [
            "tests/test_assessment_workflow.py::test_guard_sequence_and_messages_match_legacy",
            "tests/test_assessment_workflow.py::test_c10_content_change_resets_decision_and_dpo",
            "tests/test_assessment_workflow.py::test_register_change_review_and_reassessment",
            "tests/test_register.py::test_release_supersedes_and_keeps_history_immutable",
        ],
    ),
    "T-06": (
        "Selbstfreigabe abgewiesen (alle Bearbeiter, Entscheider, DSB); "
        "Korrektur erzeugt Folgefassung",
        [
            "tests/test_assessment_workflow.py::test_self_release_is_refused_like_legacy",
            "tests/test_assessment_workflow.py::test_c13_all_editors_and_decider_are_excluded_from_release",
            "tests/test_assessment_workflow.py::test_c14_dpo_statement_is_attributed_and_dpo_cannot_release",
            "tests/test_register.py::test_c13_release_requires_person_who_did_not_edit",
            "tests/test_assessment_workflow.py::test_register_change_review_and_reassessment",
        ],
    ),
    "T-09": (
        "Export enthält genau die gewählte Fassung mit Zahl, Metadaten, Version und Profil",
        [
            "tests/test_policy_cases.py::test_t09_register_export_contains_exactly_the_version_with_metadata",
            "tests/test_exports.py::test_assessment_report_is_complete_and_serialisable",
            "tests/test_exports.py::test_register_report_groups_and_checks",
        ],
    ),
    "T-10": (
        "Formeleingaben werden als Text geschrieben; HTML maskiert Eingaben",
        [
            "tests/test_legacy_exports.py::test_register_workbook_matches_except_corrected_formula",
            "tests/test_legacy_exports.py::test_formula_text_is_literal_after_round_trip",
            "tests/test_exports.py::test_register_xlsx_is_literal_text",
            "tests/test_exports.py::test_html_escapes_input_and_shows_profile_and_gaps",
        ],
    ),
    "T-14": (
        "Bibliothek protokolliert nicht selbst; Audit-Ereignisse ohne Inhaltsdaten",
        [
            "tests/test_policy_cases.py::test_t14_library_writes_no_logs_and_audit_events_carry_no_content"
        ],
    ),
    "T-20": (
        "Parallele Änderung mit veralteter Revision wird abgewiesen, kein stilles Überschreiben",
        [
            "tests/test_assessment_workflow.py::test_stale_revision_and_profile_integrity",
            "tests/test_register.py::test_draft_lifecycle_and_revisions",
        ],
    ),
    "T-38": (
        "Laufzeitmodule nutzen nur Standardbibliothek/eigenes Paket, optionale Renderer nur lazy; "
        "keine Umgehung von Rechte-, Mandanten- oder Freigaberegeln",
        ["tests/test_architecture.py"],
    ),
}

#: Framework requirement → catalogue tests that must all pass.
REQUIREMENTS = {
    "F-01": ("MULTI_TENANT_LIBRARY_CONTRACT", ["T-01"]),
    "F-02": ("AUTHORIZER_PORT_ENFORCED_IN_SERVICES", ["T-02", "T-03"]),
    "F-03": ("STATE_MACHINE_AND_CONCURRENCY", ["T-05", "T-20"]),
    "F-04": ("REPORT_JSON_HTML_XLSX_EXPORTS", ["T-09", "T-10"]),
    "F-06": ("FOUR_EYES_AND_IMMUTABLE_RELEASES", ["T-06"]),
    "F-07": ("LIBRARY_PROTOCOLS_AND_SUPPLY_CHAIN", ["T-14", "T-37"]),
    "F-09": ("LIBRARY_SOURCE_ARCHITECTURE", ["T-38"]),
    "F-15": ("VERSIONED_SOURCE_BOUND_RULE_PROFILES", []),
}
PROFILE_TESTS = ["tests/test_profiles.py"]


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
        "scope": "Zwei quellengebundene Regelprofile mit Version, Fingerprint, Herkunft; "
        "Bewertungen speichern Profil-ID/-Version/-Fingerprint, "
        "geänderte Profile werden abgewiesen",
        **run_pytest(
            "F-15",
            [
                *PROFILE_TESTS,
                "tests/test_assessment_workflow.py::test_stale_revision_and_profile_integrity",
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
            "F-05": "Datenschutzbewertung der Bibliothek selbst hängt am Consumer; "
            "dsfa_required UNKNOWN",
            "F-07.ASSESS": "Schutzbedarf der Bibliothek nicht festgelegt (protection_need UNKNOWN)",
            "T-12": "Anwendbarkeit UNKNOWN; die Fälle selbst sind in test_assessment_workflow "
            "(C01, Prüfbedarf) ausgeführt, werden aber nicht als Anforderungsnachweis gebunden",
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
