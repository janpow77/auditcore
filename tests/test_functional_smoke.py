"""Mandatory functional smoke after production deployments (synthetic transport)."""

import json
from dataclasses import asdict

import pytest
from test_deployer import package_project as package_project  # noqa: F401  (Fixture)

from auditcore.tools.deployer.build import DeploymentBuilder
from auditcore.tools.deployer.cli import main
from auditcore.tools.deployer.models import ApplicationDeploymentProfile
from auditcore.tools.deployer.smoke import (
    SMOKE_MARKER,
    is_health_path,
    load_cases,
    run_functional_smoke,
    smoke_required,
)

CASES = [
    {
        "name": "pipeline-upload",
        "changed_feature": "Dokumentpipeline (auditcore_documents)",
        "method": "POST",
        "path": "/api/documents",
        "json_body": {"title": f"{SMOKE_MARKER}-2026-09-24"},
        "expected_status": 201,
        "json_expect": {"status": "queued", "id": {"exists": True}},
        "headers_from_env": {"X-API-Key": "APP_SMOKE_KEY"},
    },
    {
        "name": "sanctions",
        "changed_feature": "Sanktionsabgleich (auditcore_registry_sources)",
        "path": "/api/sanctions/search?q=Test",
        "json_expect": {"results.0.score": {"min": 70}, "lists": {"contains": "EU"}},
    },
]


def fake(responses):
    calls = []

    def transport(method, url, headers, body, timeout):
        calls.append({"method": method, "url": url, "headers": dict(headers), "body": body})
        status, payload = responses[url.split("://", 1)[1].split("/", 1)[1]]
        return status, json.dumps(payload).encode()

    transport.calls = calls
    return transport


GOOD = {
    "api/documents": (201, {"status": "queued", "id": "d1"}),
    "api/sanctions/search?q=Test": (200, {"results": [{"score": 92}], "lists": ["EU", "UN"]}),
}


def test_all_functional_cases_pass_and_no_secret_or_body_is_stored():
    transport = fake(GOOD)
    result = run_functional_smoke(
        "https://app.example", CASES, transport=transport, environ={"APP_SMOKE_KEY": "geheim"}
    )
    assert result.status == "PASS" and not result.blockers
    assert transport.calls[0]["headers"]["X-API-Key"] == "geheim"
    stored = json.dumps(asdict(result))
    assert "geheim" not in stored and "d1" not in stored and "92" not in stored


def test_wrong_status_or_expectation_fails_the_deployment():
    bad = dict(GOOD, **{"api/sanctions/search?q=Test": (200, {"results": [], "lists": ["UN"]})})
    result = run_functional_smoke(
        "https://app.example", CASES, transport=fake(bad), environ={"APP_SMOKE_KEY": "x"}
    )
    assert result.status == "FAIL"
    failures = result.cases["sanctions"]["failures"]
    assert "Feld fehlt: results.0.score" in failures and "Erwartung verfehlt: lists" in failures


def test_missing_credentials_are_not_configured_and_block():
    result = run_functional_smoke("https://app.example", CASES, transport=fake(GOOD), environ={})
    assert result.status == "FAIL"
    assert result.cases["pipeline-upload"]["status"] == "NOT_CONFIGURED"


@pytest.mark.parametrize("path", ["/health", "/api/health", "/healthz/", "/ready", "/livez"])
def test_health_endpoints_never_count_as_functional_smoke(path):
    assert is_health_path(path)
    with pytest.raises(ValueError, match="kein fachlicher Rauchtest"):
        load_cases([{"name": "h", "changed_feature": "x", "path": path, "body_contains": ["ok"]}])


@pytest.mark.parametrize(
    ("case", "message"),
    [
        ({"name": "a", "changed_feature": "", "path": "/x", "body_contains": ["y"]}, "Pflicht"),
        ({"name": "a", "changed_feature": "f", "path": "/x"}, "fachliche Erwartung"),
        (
            {
                "name": "a",
                "changed_feature": "f",
                "method": "POST",
                "path": "/x",
                "json_body": {"t": "echt"},
                "body_contains": ["y"],
            },
            "markieren",
        ),
        (
            {"name": "a", "changed_feature": "f", "path": "https://x/y", "body_contains": ["y"]},
            "relativ",
        ),
    ],
)
def test_invalid_cases_are_rejected(case, message):
    with pytest.raises(ValueError, match=message):
        load_cases([case])


def test_empty_definition_is_blocked():
    result = run_functional_smoke("https://app.example", [], transport=fake(GOOD))
    assert result.status == "BLOCKED" and "Pflicht" in result.blockers[0]


def test_https_is_required_by_default_transport():
    result = run_functional_smoke("http://app.example", CASES[1:], environ={})
    assert result.status == "FAIL" and "ValueError" in result.cases["sanctions"]["reason"]


def test_plan_blocks_production_deployment_without_functional_smoke(package_project):
    root, _ = package_project
    profile_path = root / "auditcore-deploy.json"
    data = json.loads(profile_path.read_text())
    assert smoke_required("production") and not smoke_required("internal_test")
    profile_path.write_text(json.dumps({**data, "deployment_target": "production"}))
    plan = DeploymentBuilder().plan(root)
    assert any(b.startswith("Functional smoke required") for b in plan.blockers)
    profile_path.write_text(
        json.dumps({**data, "deployment_target": "production", "functional_smoke": CASES})
    )
    plan = DeploymentBuilder().plan(root)
    assert not any(b.startswith("Functional smoke required") for b in plan.blockers)


def test_internal_test_target_does_not_require_smoke(package_project):
    root, _ = package_project
    plan = DeploymentBuilder().plan(root)
    assert not any(b.startswith("Functional smoke required") for b in plan.blockers)
    raw = json.loads((root / "auditcore-deploy.json").read_text())
    assert ApplicationDeploymentProfile(**raw).functional_smoke == []


def test_cli_smoke_exits_nonzero_without_cases(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / "smoke.json"
    config.write_text(json.dumps({"functional_smoke": []}))
    assert main(["smoke", str(config), "--base-url", "https://app.example"]) == 1
    written = json.loads((tmp_path / ".auditcore/functional-smoke.json").read_text())
    assert written["status"] == "BLOCKED"
