"""Applicability and policy drift regression tests."""

from dataclasses import replace

import pytest

from auditcore.tools.common import read_json, write_json
from auditcore.tools.policy.evidence import artifact_source_digest, evidence_binding
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


def test_muss_conditional_soll_evidence(policy_provider, library_context, tmp_path):
    root = tmp_path / "artifact"
    root.mkdir()
    (root / "domain.py").write_text("VALUE = 1\n")
    context = replace(library_context, binding_decisions="yes")
    policy_provider.artifact_root = root
    policy_provider.evidence = {
        "F-06": {
            "status": "MISSING",
            "references": ["synthetic missing implementation review"],
            "source_commit": policy_provider.load_requirements().commit_sha,
            **evidence_binding(root, policy_provider.artifact, context),
        }
    }
    report = policy_provider.evaluate(context)
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


def test_human_deviation_requires_full_record(policy_provider, library_context, tmp_path):
    root = tmp_path / "artifact"
    root.mkdir()
    (root / "domain.py").write_text("VALUE = 1\n")
    policy_provider.artifact_root = root
    context = replace(library_context, external_interfaces=True)
    policy_provider.decisions = {
        "F-07": {
            **evidence_binding(root, policy_provider.artifact, context),
            "classification": "HUMAN_CONFIRMED",
            "authority": "synthetic responsible person",
            "reference": "decision/123",
            "reason": "synthetic",
            "consequences": "documented",
            "compensation": "documented",
            "framework_commit": "15f5338f783f2c7d5760a9bb299be06d27326be0",
        }
    }
    assert "F-07" in policy_provider.evaluate(context).approved_deviations
    (root / "domain.py").write_text("VALUE = 2\n")
    assert not policy_provider.evaluate(context).approved_deviations


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


def test_deployment_context_fallback_is_loaded(tmp_path):
    from dataclasses import asdict

    from auditcore.tools.common import write_json
    from auditcore.tools.policy.framework import context_from_project

    root = tmp_path / "deployment"
    write_json(
        root / "deploy/apt/auditcore-context.json",
        {**asdict(ApplicabilityContext()), "ai_usage": "none"},
    )
    assert context_from_project(root).ai_usage == "none"


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
                **evidence_binding(
                    first, policy_provider.artifact, ApplicabilityContext.from_dict(context)
                ),
            }
        },
    )
    one = policy_provider.evaluate_project(first)
    two = policy_provider.evaluate_project(second)
    assert next(r for r in one.requirements if r.requirement_id == "F-09").status == "VERIFIED"
    assert next(r for r in two.requirements if r.requirement_id == "F-09").status != "VERIFIED"


@pytest.fixture
def bound_policy(policy_provider, library_context, tmp_path):
    root = tmp_path / "artifact"
    root.mkdir()
    (root / "domain.py").write_text("VALUE = 1\n")
    (root / "settings.json").write_text('{"rule": "one"}\n')
    policy_provider.artifact_root = root
    policy_provider.artifact = "synthetic-domain"
    policy_provider.evidence = {
        "F-09": {
            "status": "VERIFIED",
            "references": ["synthetic architecture test"],
            "source_commit": policy_provider.load_requirements().commit_sha,
            **evidence_binding(root, policy_provider.artifact, library_context),
        }
    }
    return policy_provider, root


def _f09(provider, context):
    return next(
        row for row in provider.evaluate(context).requirements if row.requirement_id == "F-09"
    )


def test_matching_artifact_evidence_is_verified(bound_policy, library_context):
    provider, _ = bound_policy
    assert _f09(provider, library_context).gate_status == "PASS"


@pytest.mark.parametrize("status", ["IMPLEMENTED", "MISSING"])
def test_stale_negative_or_partial_evidence_cannot_claim_a_status(
    bound_policy, library_context, status
):
    provider, root = bound_policy
    provider.evidence["F-09"]["status"] = status
    before = _f09(provider, library_context)
    assert before.gate_status == ("FAIL" if status == "MISSING" else "REVIEW_REQUIRED")
    (root / "domain.py").write_text("changed")
    after = _f09(provider, library_context)
    assert after.status == "EVIDENCE_INVALID"
    assert after.gate_status == "REVIEW_REQUIRED"


@pytest.mark.parametrize("filename", ["domain.py", "settings.json", "new-resource.txt"])
def test_source_changes_invalidate_evidence(bound_policy, library_context, filename):
    provider, root = bound_policy
    (root / filename).write_text("changed\n")
    assert _f09(provider, library_context).status == "EVIDENCE_INVALID"
    assert _f09(provider, library_context).gate_status == "REVIEW_REQUIRED"


@pytest.mark.parametrize(
    "key", ["artifact", "artifact_source_digest", "context_digest", "source_commit"]
)
def test_wrong_or_missing_evidence_binding_never_passes(bound_policy, library_context, key):
    provider, _ = bound_policy
    provider.evidence["F-09"][key] = "wrong"
    assert _f09(provider, library_context).gate_status == "REVIEW_REQUIRED"
    del provider.evidence["F-09"][key]
    assert _f09(provider, library_context).gate_status == "REVIEW_REQUIRED"


def test_other_artifact_and_context_invalidate_evidence(bound_policy, library_context):
    provider, _ = bound_policy
    assert (
        _f09(provider, replace(library_context, external_interfaces=True)).gate_status
        == "REVIEW_REQUIRED"
    )
    provider.artifact = "another-package"
    assert _f09(provider, library_context).gate_status == "REVIEW_REQUIRED"


def test_missing_artifact_root_never_accepts_verified_claim(bound_policy, library_context):
    provider, root = bound_policy
    provider.artifact_root = None
    assert _f09(provider, library_context).gate_status == "REVIEW_REQUIRED"
    provider.artifact_root = root / "missing"
    assert _f09(provider, library_context).gate_status == "REVIEW_REQUIRED"


def test_generated_evidence_and_build_outputs_do_not_change_digest(bound_policy):
    _, root = bound_policy
    before = artifact_source_digest(root)
    for directory in (".auditcore", "build", "dist", ".venv", "__pycache__"):
        path = root / directory / "artifact.log"
        path.parent.mkdir()
        path.write_text("generated")
    assert artifact_source_digest(root) == before


def test_external_symlink_cannot_hide_source(bound_policy, library_context, tmp_path):
    provider, root = bound_policy
    target = tmp_path / "outside.py"
    target.write_text("external")
    (root / "linked.py").symlink_to(target)
    assert _f09(provider, library_context).gate_status == "REVIEW_REQUIRED"


def test_nested_build_module_is_part_of_source(bound_policy):
    _, root = bound_policy
    before = artifact_source_digest(root)
    module = root / "src/package/build/config.json"
    module.parent.mkdir(parents=True)
    module.write_text('{"meaning": "source resource, not a build artifact"}')
    assert artifact_source_digest(root) != before


def test_internal_file_symlink_is_hashed(bound_policy):
    _, root = bound_policy
    (root / "alias.py").symlink_to("domain.py")
    before = artifact_source_digest(root)
    (root / "domain.py").write_text("changed")
    assert artifact_source_digest(root) != before


@pytest.mark.parametrize("references", [[], "claim", [None], [""]])
def test_malformed_reference_is_not_a_verification(bound_policy, library_context, references):
    provider, _ = bound_policy
    provider.evidence["F-09"]["references"] = references
    assert _f09(provider, library_context).gate_status == "REVIEW_REQUIRED"


def test_project_evidence_reloaded_each_time(bound_policy, library_context):
    from dataclasses import asdict

    provider, root = bound_policy
    write_json(root / "auditcore-context.json", asdict(library_context))
    provider.evidence["F-09"].update(evidence_binding(root, provider.artifact, library_context))
    path = root / ".auditcore/policy-evidence.json"
    write_json(path, provider.evidence)
    assert (
        next(
            r for r in provider.evaluate_project(root).requirements if r.requirement_id == "F-09"
        ).gate_status
        == "PASS"
    )
    write_json(path, {})
    assert (
        next(
            r for r in provider.evaluate_project(root).requirements if r.requirement_id == "F-09"
        ).gate_status
        == "REVIEW_REQUIRED"
    )
    path.unlink()
    assert (
        next(
            r for r in provider.evaluate_project(root).requirements if r.requirement_id == "F-09"
        ).gate_status
        == "REVIEW_REQUIRED"
    )


@pytest.mark.parametrize(
    "types,expected",
    [
        (("rulebook",), ("FALSE", "FALSE", "FALSE")),
        (("prompt",), ("TRUE", "TRUE", "TRUE")),
        (("agent",), ("FALSE", "FALSE", "TRUE")),
        (("prompt", "rulebook"), ("TRUE", "TRUE", "TRUE")),
        ("UNKNOWN", ("UNKNOWN", "UNKNOWN", "UNKNOWN")),
    ],
)
def test_versioned_artifact_types_control_actual_test_scope(
    policy_provider, library_context, types, expected
):
    context = replace(library_context, versioned_artifacts=True, versioned_artifact_types=types)
    result = policy_provider.evaluate(context)
    assert tuple(result.tests[key]["applicable"] for key in ("T-26", "T-27", "T-28")) == expected
    rule = next(row for row in result.requirements if row.requirement_id == "F-15")
    assert rule.applicable == "TRUE"
    assert rule.gate_status == "REVIEW_REQUIRED"
    if types == "UNKNOWN":
        assert {"T-26", "T-27", "T-28"}.issubset(result.review_required)


def test_artifact_type_validation_and_json_conversion(library_context):
    assert ApplicabilityContext.from_dict(
        {"versioned_artifacts": True, "versioned_artifact_types": ["rulebook"]}
    ).versioned_artifact_types == ("rulebook",)
    for value in ([], ["unsupported"], "prompt"):
        with pytest.raises(ValueError):
            replace(library_context, versioned_artifacts=True, versioned_artifact_types=value)
    with pytest.raises(ValueError):
        replace(library_context, versioned_artifacts=False, versioned_artifact_types=("prompt",))


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


@pytest.mark.parametrize(
    "documents,storage,expected",
    [
        (True, True, "TRUE"),
        (True, False, "FALSE"),
        (True, "UNKNOWN", "UNKNOWN"),
        (False, "UNKNOWN", "FALSE"),
        ("UNKNOWN", True, "UNKNOWN"),
        ("UNKNOWN", False, "FALSE"),
    ],
)
def test_document_integrity_test_requires_stored_documents(
    policy_provider, library_context, documents, storage, expected
):
    result = policy_provider.evaluate(
        replace(library_context, documents=documents, document_storage=storage)
    )
    assert result.tests["T-08"]["applicable"] == expected
    assert (
        result.tests["T-08"]["status"]
        == {
            "TRUE": "NOT_EXECUTED",
            "FALSE": "NOT_APPLICABLE_WITH_REASON",
            "UNKNOWN": "REVIEW_REQUIRED",
        }[expected]
    )
    if expected == "UNKNOWN":
        assert "T-08" in result.review_required


@pytest.mark.parametrize(
    "formats,expected",
    [
        (("json",), "FALSE"),
        (("json", "pdf", "xml", "txt", "html"), "FALSE"),
        *(
            ([format_name], "TRUE")
            for format_name in ("csv", "tsv", "xls", "xlsx", "ods", "zip", "tar", "archive")
        ),
        (("json", "xlsx"), "TRUE"),
        ("UNKNOWN", "UNKNOWN"),
    ],
)
def test_export_test_depends_on_table_or_archive_formats(
    policy_provider, library_context, formats, expected
):
    result = policy_provider.evaluate(
        replace(library_context, exports=True, export_formats=formats)
    )
    assert result.tests["T-10"]["applicable"] == expected
    assert (
        result.tests["T-10"]["status"]
        == {
            "TRUE": "NOT_EXECUTED",
            "FALSE": "NOT_APPLICABLE_WITH_REASON",
            "UNKNOWN": "REVIEW_REQUIRED",
        }[expected]
    )
    if expected == "UNKNOWN":
        assert "T-10" in result.review_required
    assert result.tests["T-09"]["applicable"] == "TRUE"


def test_legacy_context_retains_unknown_document_and_export_details(policy_provider):
    context = ApplicabilityContext.from_dict({"documents": True, "exports": True})
    assert context.document_storage == context.export_formats == "UNKNOWN"
    report = policy_provider.evaluate(context)
    assert {"T-08", "T-10"}.issubset(report.review_required)


def test_json_only_does_not_weaken_security_or_log_requirements(policy_provider, library_context):
    before = replace(library_context, exports=True, documents=True, external_interfaces=True)
    after = replace(before, document_storage=False, export_formats=("json",))
    baseline = policy_provider.evaluate(before)
    result = policy_provider.evaluate(after)
    assert result.requirements == baseline.requirements
    assert result.tests["T-14"] == baseline.tests["T-14"]
    assert result.tests["T-14"]["applicable"] == "TRUE"
    assert (
        next(row for row in result.requirements if row.requirement_id == "F-07").applicable
        == "TRUE"
    )


def test_export_format_validation_and_no_export_case(policy_provider):
    assert ApplicabilityContext.from_dict(
        {"exports": True, "export_formats": ["json", "csv", "json"]}
    ).export_formats == ("csv", "json")
    for value in ([], ["unsupported"], [False], "json", None):
        with pytest.raises(ValueError):
            ApplicabilityContext(exports=True, export_formats=value)
    with pytest.raises(ValueError):
        ApplicabilityContext(exports=False, export_formats=("json",))
    with pytest.raises(ValueError):
        ApplicabilityContext(document_storage="false")
    for formats in ((), "UNKNOWN"):
        result = policy_provider.evaluate(
            ApplicabilityContext(exports=False, export_formats=formats)
        )
        assert result.tests["T-10"]["applicable"] == "FALSE"
