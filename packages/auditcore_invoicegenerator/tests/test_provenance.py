"""Validate installed profile identity and immutable content references."""

import hashlib
import json
from datetime import date, datetime
from importlib.resources import files
from pathlib import Path


def test_installed_profile_metadata_binds_exact_content_and_fork():
    package = files("auditcore_invoicegenerator")
    metadata = json.loads(package.joinpath("provenance.json").read_text())
    artifacts = metadata["versioned_artifacts"]
    assert len({artifact["artifact_id"] for artifact in artifacts}) == 2
    for artifact in artifacts:
        # Existing rule profiles retain their version when a separate renderer is added.
        assert artifact["version"] == "0.1.0"
        assert artifact["title"] and artifact["type"] == "rulebook/template"
        assert artifact["status"] == "DRAFT"
        assert artifact["predecessor_version"] is None
        assert artifact["author"] == artifact["organization"] == "UNKNOWN"
        assert datetime.fromisoformat(artifact["created_at"]).tzinfo is not None
        assert datetime.fromisoformat(artifact["modified_at"]) >= datetime.fromisoformat(
            artifact["created_at"]
        )
        assert artifact["review"]["human_release_approval"] == "NOT_GRANTED"
        for name, digest in artifact["content_hashes"].items():
            assert hashlib.sha256(package.joinpath(name).read_bytes()).hexdigest() == digest
    parent = artifacts[0]["fork_parent"]
    assert parent["commit"] == metadata["source_commit"]
    assert parent["sha256"] == metadata["source_sha256"]
    assert artifacts[1]["fork_parent"] is None
    renderer = metadata["renderer"]
    assert renderer["version"] == metadata["version"] == "0.2.0"
    assert hashlib.sha256(package.joinpath("pdf.py").read_bytes()).hexdigest() == renderer["sha256"]


def test_source_metadata_copies_match_installed_profile_contract():
    package_root = Path(__file__).resolve().parents[1]
    installed = json.loads(
        files("auditcore_invoicegenerator").joinpath("provenance.json").read_text()
    )
    for path in [package_root / "provenance.json", package_root / "docs/provenance.json"]:
        assert json.loads(path.read_text()) == installed


def test_stable_artifact_ids_map_to_actual_runtime_profile_ids():
    from auditcore_invoicegenerator import FLOWINVOICE_DEMO_PROFILE, InvoiceScenario

    metadata = json.loads(
        files("auditcore_invoicegenerator").joinpath("provenance.json").read_text()
    )
    profiles = {row["artifact_id"]: row for row in metadata["versioned_artifacts"]}
    legacy = profiles["auditcore_invoicegenerator:flowinvoice-demo-fb2d185"]
    assert legacy["runtime_profile_id"] == FLOWINVOICE_DEMO_PROFILE
    scenario = profiles["auditcore_invoicegenerator:invoice-scenario-v1"]
    record = InvoiceScenario(42, base_date=date(2026, 1, 1)).generate(1)
    assert scenario["runtime_profile_id"] == record["metadata"]["profile"]
    assert scenario["runtime_profile_reference"] == "InvoiceRecord.metadata.profile"
