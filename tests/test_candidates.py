"""Domain distributions must not be inferred from infrastructure duplicates."""

from dataclasses import asdict

import pytest

from auditcore.tools.consolidator.analysis import (
    analyze_sources,
    candidate_exclusion,
    detect_candidates,
    domain,
)


def symbol(repository="owner/one", path="risk.py", name="calculate_risk", imports=""):
    source = (
        imports
        + f"def {name}(value):\n    total = value * 3\n    result = total + 1\n    return result\n"
    )
    return asdict(analyze_sources({path: source}, repository, "a" * 40)[0][0])


@pytest.mark.parametrize(
    "path,name,imports",
    [
        ("tests/risk.py", "calculate_risk", ""),
        ("test_risk.py", "calculate_risk", ""),
        ("alembic/env.py", "run_migrations_online", ""),
        ("generated/documents.py", "parse_document", ""),
        ("document_pb2.py", "parse_document", ""),
        ("api/routers/documents.py", "parse_document", ""),
        ("documents.py", "health_check", ""),
        ("risk.py", "calculate_risk", "from fastapi import Depends\n"),
        ("risk.py", "calculate_risk", "import sqlalchemy\n"),
        ("helpers.py", "parse", ""),
    ],
)
def test_infrastructure_and_unclassified_helpers_are_not_candidates(path, name, imports):
    one = symbol(path=path, name=name, imports=imports)
    assert candidate_exclusion(one)
    assert detect_candidates([one, {**one, "repository": "owner/two"}]) == []


def test_domain_distributions_and_unknown_licenses_require_review():
    one = symbol()
    other = {**one, "repository": "owner/two", "commit_sha": "b" * 40}
    candidate = detect_candidates(
        [one, other], [{"repository": one["repository"], "license": "MIT"}]
    )[0]
    assert candidate.target_module == candidate.target_distribution == "auditcore_risk"
    assert candidate.package_directory == "packages/auditcore_risk"
    assert candidate.license_status == "REVIEW_REQUIRED"
    assert candidate.recommendation != "REJECT"
    assert candidate.repositories == candidate.potential_consumers == ["owner/one", "owner/two"]
    assert candidate.consumers == []
    assert candidate.consumer_status == "NOT_VERIFIED"
    assert candidate.independent_origins_status == "UNKNOWN"


@pytest.mark.parametrize("same_revision", [True, False])
def test_observed_copies_are_not_claimed_as_independent_consumers(same_revision):
    one = symbol(repository="owner/flowstat", path="backend/risk.py")
    other = {
        **one,
        "repository": "owner/portal",
        "path": "embedded/flowstat/backend/risk.py",
        "commit_sha": one["commit_sha"] if same_revision else "b" * 40,
    }
    candidate = detect_candidates([one, other])[0]
    assert candidate.origin_groups == [["owner/flowstat", "owner/portal"]]
    assert candidate.independent_origins_status == "SHARED_ORIGIN_OBSERVED"
    assert candidate.consumers == []
    assert candidate.origin_evidence[0]["evidence"] == (
        "IDENTICAL_GIT_COMMIT" if same_revision else "IDENTICAL_SYMBOL_AT_EMBEDDED_REPOSITORY_PATH"
    )


def test_generator_domain_requires_business_generator_evidence():
    one = symbol(path="backend/generator.py")
    one["symbol"] = "TestDataGenerator.generate_iban"
    other = {**one, "repository": "owner/two", "commit_sha": "b" * 40}
    assert detect_candidates([one, other])[0].target_distribution == "auditcore_dummygenerator"
    assert domain("backend/generator.py.get_optimal_workers") == "utils"
    assert domain("context.py.health_check") == "utils"


def test_different_domains_are_not_harmonized_due_to_same_ast_shape():
    one = symbol(path="risk.py")
    other = {**one, "repository": "owner/two", "path": "reporting.py", "symbol": "format_report"}
    assert detect_candidates([one, other]) == []


def test_privacy_business_logic_retains_security_review():
    one = symbol(path="pseudonymization.py", name="pseudonymize")
    one["security_sensitive"] = True
    candidate = detect_candidates([one, {**one, "repository": "owner/two"}])[0]
    assert candidate.target_distribution == "auditcore_privacy"
    assert candidate.decision_status == "SECURITY_OR_POLICY_REVIEW_REQUIRED"
