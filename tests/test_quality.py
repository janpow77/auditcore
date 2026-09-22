"""Negative quality cases must fail without leaking matched secret values."""

import ast

import pytest

from auditcore.models import CheckStatus
from auditcore.tools.quality.engine import check
from auditcore.tools.quality.scanners import api_snapshot, architecture, scan_sensitive


@pytest.mark.parametrize(
    "source", ["import fastapi", "from flask import Flask", "from django.views import View"]
)
def test_framework_imports(source):
    assert architecture(ast.parse(source), "domain.py", [], True)[0].status == CheckStatus.FAIL
    assert not architecture(ast.parse(source), "tools/client.py", [], False)


def test_comments_not_imports():
    assert not architecture(ast.parse('# import fastapi\nx = "import flask"'), "x.py", [], True)


@pytest.mark.parametrize(
    "source",
    [
        "from sqlalchemy.orm import Session",
        "import httpx",
        "from auditcore import tools",
        "from . import tools",
    ],
)
def test_infrastructure_direction(source):
    assert architecture(ast.parse(source), "x.py", [], True)


def test_secret_redaction():
    secret = "ghp_" + "SYNTHETIC" * 5
    findings = scan_sensitive(secret)
    assert findings and all(secret not in r.message for r in findings)


@pytest.mark.parametrize(
    "value",
    [
        "127.0.0.1",
        "2001:db8::1",
        "machine.internal",
        "person@example.invalid",
        r"C:\data\file.txt",
        "/home/test/x",
    ],
)
def test_privacy_is_review(value):
    assert any(r.status == CheckStatus.REVIEW_REQUIRED for r in scan_sensitive(value))


def test_api_breaks_detected(tmp_path, policy_provider, library_context):
    (tmp_path / "domain.py").write_text(
        'def calculate(x: int) -> int:\n    """Calculate."""\n    return x\n'
    )
    baseline = tmp_path / "api.json"
    check(tmp_path, snapshot_path=baseline, external=False)
    (tmp_path / "domain.py").write_text(
        'def calculate(x: str) -> str:\n    """Calculate."""\n    return x\n'
    )
    report = check(
        tmp_path,
        compare_api=baseline,
        external=False,
        policy=policy_provider.evaluate(library_context),
    )
    assert any(r.code == "AC-API-001" and r.status == CheckStatus.FAIL for r in report.findings)


def test_syntax_and_security_policy_first(tmp_path):
    (tmp_path / "bad.py").write_text("def invalid(")
    report = check(tmp_path, external=False)
    assert report.exit_code() == 1
    assert not any(f.code == "AC-SEC-001" for f in report.findings)


def test_ignore_is_reported(tmp_path, policy_provider, library_context):
    (tmp_path / "source.py").write_text(
        "# auditcore-quality: ignore-file AC-DOC-001\ndef undocumented(x):\n    return x\n"
    )
    result = check(tmp_path, external=False, policy=policy_provider.evaluate(library_context))
    assert any(f.code == "AC-DOC-001" for f in result.ignored)
    assert any(f.code == "AC-TYPE-001" for f in result.findings)


def test_api_models_and_exceptions():
    snapshot = api_snapshot(
        {"x.py": "class Model:\n    value: int\n\ndef f():\n    raise ValueError()\n"}
    )
    assert snapshot["x.Model"]["fields"] == "value: int"
    assert snapshot["x.f"]["raises"] == "ValueError"


@pytest.mark.parametrize(
    "source",
    [
        'importlib.import_module("fastapi")',
        '__import__("httpx")',
        "from ..tools.quality import check",
    ],
)
def test_dynamic_and_relative_forbidden_imports(source):
    assert architecture(ast.parse(source), "domain.py", [], True)


def test_detailed_documentation_is_executable():
    from auditcore.tools.quality.scanners import documentation_complexity

    tree = ast.parse('def f(value: int) -> int:\n    """Summary only."""\n    raise ValueError()\n')
    findings = documentation_complexity(tree, "x.py", detailed=True, bilingual=True)
    assert len([f for f in findings if f.code == "AC-DOC-001"]) == 2


@pytest.mark.parametrize("filename", ["settings.json", ".env", "postinst.tmpl"])
def test_resource_secrets_checked_after_applicability(
    tmp_path, policy_provider, library_context, filename
):
    secret = "ghp_" + "SYNTHETIC" * 5
    (tmp_path / filename).write_text(secret)
    without_policy = check(tmp_path, external=False)
    assert not any(f.code == "AC-SEC-001" for f in without_policy.findings)
    report = check(tmp_path, external=False, policy=policy_provider.evaluate(library_context))
    assert any(f.code == "AC-SEC-001" and f.path == filename for f in report.findings)
    assert secret not in str(report.to_dict())


def test_resource_changes_invalidate_source_digest(tmp_path):
    path = tmp_path / "policy.json"
    path.write_text('{"version": "one"}')
    before = check(tmp_path, external=False).source_digest
    path.write_text('{"version": "two"}')
    assert check(tmp_path, external=False).source_digest != before


def test_stale_packaged_resource_fails_supply_chain(tmp_path, policy_provider, library_context):
    import zipfile

    from auditcore.tools.common import write_json
    from auditcore.tools.quality.supplychain import wheel_sbom

    source = tmp_path / "src/auditcore"
    source.mkdir(parents=True)
    (source / "__init__.py").write_text('"""Synthetic library."""\n')
    resource = source / "policy.json"
    resource.write_text('{"version": "one"}')
    wheel = tmp_path / "auditcore-0.1-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        for path in source.iterdir():
            archive.write(path, "auditcore/" + path.name)
        archive.writestr("auditcore-0.1.dist-info/METADATA", "Name: auditcore\nVersion: 0.1\n")
    supply = tmp_path / "supply.json"
    write_json(supply, wheel_sbom(wheel, tmp_path / "sbom.json"))
    policy = policy_provider.evaluate(library_context)
    before = check(
        source, project=tmp_path, policy=policy, external=False, supply_chain_report=supply
    )
    assert next(f for f in before.findings if f.code == "AC-SUPPLY-001").status == "PASS"
    resource.write_text('{"version": "two"}')
    after = check(
        source, project=tmp_path, policy=policy, external=False, supply_chain_report=supply
    )
    assert next(f for f in after.findings if f.code == "AC-SUPPLY-001").status == "FAIL"


def test_quoted_json_credential_is_redacted():
    secret = "synthetic-credential-value"
    findings = scan_sensitive('{"api_key": "' + secret + '"}')
    assert any(f.code == "AC-SEC-001" for f in findings)
    assert secret not in str(findings)
