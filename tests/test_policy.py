"""Applicability and policy drift regression tests."""

from dataclasses import replace

import pytest

from auditcore.tools.common import read_json, write_json
from auditcore.tools.policy.framework import GitFrameworkPolicyProvider, trigger_value
from auditcore.tools.policy.models import ApplicabilityContext, Truth


def test_unknown_never_false():
    ctx = ApplicabilityContext()
    assert trigger_value({"field": "uploads", "in": [True]}, ctx) == Truth.UNKNOWN
    with pytest.raises(ValueError):
        ApplicabilityContext(uploads="false")
    with pytest.raises(ValueError):
        ApplicabilityContext(personal_data="unspecified")


@pytest.mark.parametrize(
    "left,right,expected",
    [
        ("FALSE", "UNKNOWN", "FALSE"),
        ("TRUE", "UNKNOWN", "UNKNOWN"),
        ("TRUE", "TRUE", "TRUE"),
    ],
)
def test_kleene_all(left, right, expected):
    assert (
        trigger_value({"all": [{"constant": left}, {"constant": right}]}, ApplicabilityContext())
        == expected
    )


def test_library_no_oidc_roles_or_four_eyes(policy_provider, library_context):
    report = policy_provider.evaluate(library_context)
    rows = {r.requirement_id: r for r in report.requirements}
    for identifier in ("F-01", "F-02", "F-06", "F-07", "F-14", "F-18"):
        assert rows[identifier].status == "NOT_APPLICABLE_WITH_REASON"
        assert rows[identifier].applicability_reason
    assert rows["F-01.ASSESS"].status == "IMPLEMENTED"
    assert report.tests["T-13"]["status"] == "NOT_APPLICABLE_WITH_REASON"
    assert report.tests["T-37"]["status"] == "NOT_EXECUTED"
    assert report.profiles == ["LIBRARY"]


def test_unknown_application_requires_review(policy_provider):
    report = policy_provider.evaluate(ApplicabilityContext())
    assert report.overall_status == "REVIEW_REQUIRED"
    assert report.tests["T-01"]["status"] == "REVIEW_REQUIRED"


def test_multiple_profiles_and_protection_provenance(library_context):
    ctx = replace(
        library_context,
        artifact_type="application",
        binding_decisions="yes",
        ai_usage="byok",
        protection_need="high",
        protection_need_source="LLM_INFERRED",
    )
    assert set(ctx.profiles()) == {"INTERNAL_APP", "PROCEDURAL_APP", "AI_ENABLED"}
    assert "HIGH_PROTECTION" in replace(ctx, protection_need_source="HUMAN_CONFIRMED").profiles()


def test_muss_conditional_soll_evidence(policy_provider, library_context):
    policy_provider.evidence = {"F-06": {"status": "MISSING"}}
    report = policy_provider.evaluate(replace(library_context, binding_decisions="yes"))
    assert "F-06" in report.blocking_requirements
    assert any(
        r.binding_level == "SOLL" and r.gate_status == "WARNING" for r in report.requirements
    )
    assert report.blocks({"F-06"})
    assert not report.blocks({"UNRELATED"})


def test_llm_cannot_approve_deviation(policy_provider, library_context):
    policy_provider.decisions = {
        "F-07": {"classification": "LLM_INFERRED", "reference": "proposal"}
    }
    report = policy_provider.evaluate(replace(library_context, external_interfaces=True))
    assert not report.approved_deviations
    assert (
        next(r for r in report.requirements if r.requirement_id == "F-07").status
        == "DEVIATION_PENDING"
    )


def test_human_deviation_requires_full_record(policy_provider, library_context):
    policy_provider.decisions = {
        "F-07": {
            "classification": "HUMAN_CONFIRMED",
            "authority": "synthetic responsible person",
            "reference": "decision/123",
            "reason": "synthetic",
            "consequences": "documented",
            "compensation": "documented",
            "framework_commit": "15f5338f783f2c7d5760a9bb299be06d27326be0",
        }
    }
    assert (
        "F-07"
        in policy_provider.evaluate(
            replace(library_context, external_interfaces=True)
        ).approved_deviations
    )


def test_source_drift_not_silently_accepted(policy_provider, library_context):
    source = read_json(policy_provider.cache)
    source["content"]["docs/verbindlichkeit.md"] += "\nNew binding requirement\n"
    write_json(policy_provider.cache, source)
    report = policy_provider.evaluate(library_context)
    assert all(r.gate_status == "REVIEW_REQUIRED" for r in report.requirements)


def test_offline_is_stale_missing_unavailable(policy_provider, tmp_path):
    assert policy_provider.load_requirements().source_status == "POLICY_SOURCE_STALE"
    provider = GitFrameworkPolicyProvider(cache=tmp_path / "absent", offline=True)
    assert provider.evaluate(ApplicabilityContext()).source_status == "POLICY_SOURCE_UNAVAILABLE"


def test_project_evidence_is_loaded_without_cross_project_leakage(
    policy_provider, library_context, tmp_path
):
    from dataclasses import asdict

    from auditcore.tools.common import write_json

    first, second = tmp_path / "first", tmp_path / "second"
    for root in (first, second):
        root.mkdir()
        context = {**asdict(library_context), "versioned_artifacts": True}
        write_json(root / "auditcore-context.json", context)
    source = policy_provider.load_requirements()
    write_json(
        first / ".auditcore/policy-evidence.json",
        {
            "F-09": {
                "status": "VERIFIED",
                "references": ["synthetic"],
                "source_commit": source.commit_sha,
            }
        },
    )
    one = policy_provider.evaluate_project(first)
    two = policy_provider.evaluate_project(second)
    assert next(r for r in one.requirements if r.requirement_id == "F-09").status == "VERIFIED"
    assert next(r for r in two.requirements if r.requirement_id == "F-09").status != "VERIFIED"


@pytest.mark.parametrize(
    "value,expected", [(False, "FALSE"), (True, "TRUE"), ("UNKNOWN", "UNKNOWN")]
)
def test_additional_security_checks_depend_on_actual_exposure(
    policy_provider, library_context, value, expected
):
    report = policy_provider.evaluate(replace(library_context, external_interfaces=value))
    row = next(r for r in report.requirements if r.requirement_id == "F-07")
    assert row.applicable == expected
    if value == "UNKNOWN":
        assert row.gate_status == "REVIEW_REQUIRED"
