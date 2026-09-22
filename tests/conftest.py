"""Synthetic, network-independent fixtures."""

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from auditcore.tools.common import now, run, write_json
from auditcore.tools.policy.framework import GitFrameworkPolicyProvider
from auditcore.tools.policy.models import ApplicabilityContext


@pytest.fixture
def library_context():
    return ApplicabilityContext(
        artifact_type="library",
        data_space="single_project",
        user_model="no_users",
        personal_data="none",
        binding_decisions="none",
        workflow="calculation_only",
        authentication="none",
        uploads=False,
        external_interfaces=False,
        ai_usage="none",
        deployment_target="internal_test",
        protection_need="normal",
        protection_need_source="project_configuration",
        interactive_workspace=False,
        real_data_for_test_generation=False,
        graphical_ui=False,
        international_users=False,
        modular_capabilities=False,
        versioned_artifacts=False,
        structured_imports=False,
        analytical_runs=False,
        exports=False,
        documents=False,
        delegation=False,
        dsfa_required=False,
    )


@pytest.fixture
def policy_provider(tmp_path):
    # Fixtures contain the exact public source version used by the executable mapping.
    content = json.loads((Path(__file__).parent / "fixtures/framework.json").read_text())
    cache = tmp_path / "framework.json"
    write_json(
        cache,
        {
            "repository": "janpow77/verwaltung-app-framework",
            "commit_sha": "15f5338f783f2c7d5760a9bb299be06d27326be0",
            "captured_at": now(),
            "content": content,
            "source_status": "POLICY_SOURCE_CURRENT",
        },
    )
    provider = GitFrameworkPolicyProvider(cache=cache, offline=True)
    return provider


@pytest.fixture
def git_project(tmp_path, library_context):
    root = tmp_path / "application"
    root.mkdir()
    run(["git", "init", "-q"], root)
    run(["git", "config", "user.email", "test@example.invalid"], root)
    run(["git", "config", "user.name", "Synthetic Test"], root)
    write_json(root / "auditcore-context.json", asdict(library_context))
    (root / "legacy.py").write_text(
        'def normalize(value: str) -> str:\n    """Trim input."""\n    return value.strip()\n'
    )
    run(["git", "add", "."], root)
    run(["git", "commit", "-qm", "synthetic baseline"], root)
    return root
