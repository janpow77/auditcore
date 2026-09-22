"""Fake-provider inventory, revision reuse, candidate and resource tests."""

from dataclasses import asdict

import pytest

from auditcore.exceptions import InvalidTransition
from auditcore.tools.consolidator.analysis import (
    analyze_sources,
    detect_candidates,
    load_policy,
    load_prompt,
)
from auditcore.tools.consolidator.inventory import GlobalInventory, JsonInventory
from auditcore.tools.consolidator.models import RepositoryRecord
from auditcore.tools.consolidator.providers.knowledge import KiraKnowledgeStore
from auditcore.tools.workflow import (
    CONSOLIDATION_STATES,
    DEPLOY_STATES,
    REFACTOR_STATES,
    StateMachine,
)


def test_ast_inventory():
    source = (
        "from fastapi import FastAPI\n"
        "class Parser:\n"
        "    def parse(self, x):\n"
        "        return helper(x)\n"
        "def helper(x):\n"
        "    return x\n"
    )
    symbols, edges, errors = analyze_sources({"parser.py": source}, "owner/repo", "abc")
    assert not errors
    assert {s.symbol for s in symbols} == {"Parser", "Parser.parse", "helper"}
    assert next(s for s in symbols if s.symbol == "helper").callers
    assert any(e["kind"] == "call" for e in edges)
    assert symbols[0].framework_dependencies


def test_candidates_conflicts_and_security():
    def symbols(repo, constant, name="calculate_risk"):
        source = (
            f"def {name}(value):\n    total = value * {constant}\n"
            "    result = total + 1\n    return result\n"
        )
        return [asdict(s) for s in analyze_sources({"risk.py": source}, repo, "abc")[0]]

    identical = detect_candidates(symbols("a", 3) + symbols("b", 3))
    assert identical[0].conflict_status == "IDENTICAL"
    conflicting = detect_candidates(symbols("a", 3) + symbols("b", 5))
    assert conflicting[0].decision_status == "HUMAN_DECISION_REQUIRED"
    assert detect_candidates(symbols("a", 3, "authorize") + symbols("b", 3, "authorize")) == []


def test_incremental_inventory(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "helpers.py").write_text("def parse(x):\n    return x\n")

    class FakeGitHub:
        calls = 0
        commit = "one"

        def repositories(self):
            return [
                RepositoryRecord(
                    "owner/repo",
                    "owner",
                    "private",
                    "main",
                    False,
                    False,
                    "Python",
                    commit_sha=self.commit,
                    languages=["Python"],
                )
            ]

        def checkout(self, record):
            self.calls += 1
            return source

    provider = FakeGitHub()
    store = JsonInventory(tmp_path / "inventory")
    inventory = GlobalInventory(provider, store, workers=1)
    assert inventory.scan_authenticated_account()["symbols"] == 1
    assert inventory.scan_authenticated_account()["reused"] == 1
    assert provider.calls == 1
    provider.commit = "two"
    assert inventory.scan_authenticated_account()["reused"] == 0
    assert provider.calls == 2
    assert store.load("symbols")[0]["commit_sha"] == "two"


@pytest.mark.parametrize("states", [CONSOLIDATION_STATES, REFACTOR_STATES, DEPLOY_STATES])
def test_state_machine_rejects_jumps(states):
    machine = StateMachine(states)
    with pytest.raises(InvalidTransition):
        machine.transition(states[-1], {"status": "PASS", "reference": "synthetic"})
    for target in states[1:]:
        machine.transition(target, {"status": "PASS", "reference": "synthetic"})
    with pytest.raises(InvalidTransition):
        machine.transition("FAILED", {})


def test_human_decision_gate():
    machine = StateMachine(CONSOLIDATION_STATES)
    machine.transition("WAITING_FOR_HUMAN_DECISION", {})
    with pytest.raises(InvalidTransition):
        machine.transition("CREATED", {"classification": "LLM_INFERRED"})
    machine.transition("CREATED", {"classification": "HUMAN_CONFIRMED"})


def test_resources_installed():
    assert load_policy("consolidation")["default_target"] == "auditcore_{domain}"
    prompt = load_prompt("consolidation")
    assert prompt["version"] == "1.0" and len(prompt["sha256"]) == 64


def test_kira_config_and_stale(tmp_path, monkeypatch):
    monkeypatch.delenv("KIRA_MEMORY_URL", raising=False)
    monkeypatch.delenv("MEMORY_API_KEY", raising=False)
    store = KiraKnowledgeStore(ledger=tmp_path / "ledger.json")
    assert store.sync([])["status"] == "NOT_CONFIGURED"
    assert store.search("parser")["status"] == "NOT_CONFIGURED"
    assert store.freshness({"commit_sha": "old"}, "new") == "STALE"


def test_kira_idempotent_screening(tmp_path):
    class FakeKira(KiraKnowledgeStore):
        calls = []

        def _request(self, method, path, body=None):
            self.calls.append((method, path))
            return {"id": "synthetic-id", "content": body["content"]}

    store = FakeKira("https://example.invalid/api/memory", "synthetic-key", tmp_path / "ledger")
    record = {
        "type": "SYMBOL",
        "repository": "owner/repo",
        "branch": "main",
        "commit_sha": "one",
        "path": "source.py",
        "symbol": "parse",
        "classification": "OBSERVED",
    }
    assert store.sync([record])["stored"] == 1
    assert store.sync([record])["unchanged"] == 1
    assert store.sync([{**record, "commit_sha": "two"}])["stored"] == 1
    assert store.calls[-1][0] == "PUT"
    assert store.sync([{**record, "secret": "ghp_" + "SYNTHETIC" * 5}])["screening_blocked"] == 1


def test_kira_rejects_non_http_and_remote_cleartext(tmp_path):
    for url in ("file:///etc/passwd", "http://remote.example.invalid/api/memory"):
        store = KiraKnowledgeStore(url, "synthetic", tmp_path / "ledger")
        with pytest.raises(ValueError):
            store._request("GET", "/entries")


def test_catalog_generation_atomic_reader(tmp_path):
    store = JsonInventory(tmp_path)
    store.commit({"repositories": [{"commit": "old"}], "symbols": [{"commit": "old"}]})
    store.save("repositories", [{"commit": "incomplete-new"}])
    assert store.load("repositories")[0]["commit"] == "old"
    store.commit({"repositories": [{"commit": "new"}], "symbols": [{"commit": "new"}]})
    assert store.load("symbols")[0]["commit"] == "new"


def test_kira_merged_response_is_not_acknowledged(tmp_path):
    class MergingKira(KiraKnowledgeStore):
        def _request(self, method, path, body=None):
            return {"id": "synthetic", "content": "a different merged document"}

    store = MergingKira("https://example.invalid", "synthetic", tmp_path / "ledger")
    result = store.sync(
        [
            {
                "type": "SYMBOL",
                "repository": "owner/repo",
                "branch": "main",
                "commit_sha": "one",
                "path": "source.py",
                "symbol": "parse",
                "classification": "OBSERVED",
            }
        ]
    )
    assert result["status"] == "FAIL"
    assert result["errors"][0]["error"] == "RESPONSE_CONTENT_MISMATCH"
    assert not store.ledger.exists()
