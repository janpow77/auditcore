"""Uncertain remote writes must survive restarts without duplicate submissions."""

import json

import pytest

from auditcore.tools.common import read_json
from auditcore.tools.consolidator.providers.knowledge import KiraKnowledgeStore


@pytest.fixture
def record():
    return {
        "repository": "owner/repo",
        "branch": "main",
        "commit_sha": "one",
        "path": "source.py",
        "symbol": "parse",
        "type": "SYMBOL",
        "classification": "OBSERVED",
    }


def test_timeout_survives_restart_and_exact_readback_recovers(tmp_path, record):
    rows = []
    methods = []

    class Remote(KiraKnowledgeStore):
        def _request(self, method, path, body=None):
            methods.append(method)
            if method == "GET":
                return rows
            rows.append(
                {"id": "confirmed", "source_ref": body["source_ref"], "content": body["content"]}
            )
            raise TimeoutError("credential-containing diagnostic must never be persisted")

    ledger = tmp_path / "ledger.json"
    store = Remote("https://example.invalid", "synthetic", ledger)
    assert store.sync([record])["failed"] == 1
    restarted = Remote(store.url, store.api_key, ledger)
    assert restarted.sync([record])["deferred"] == 1
    assert methods == ["POST"]
    assert "credential-containing" not in store.pending_ledger.read_text()
    assert restarted.reconcile([record])["recovered"] == 1
    assert restarted.sync([record])["unchanged"] == 1
    assert methods == ["POST", "GET"]
    assert read_json(store.pending_ledger) == {}


@pytest.mark.parametrize("kind", ["wrong_content", "wrong_reference", "duplicate", "page_limit"])
def test_reconciliation_does_not_accept_ambiguous_identity(tmp_path, record, kind):
    class Remote(KiraKnowledgeStore):
        def _request(self, method, path, body=None):
            assert method == "GET"
            row = {
                "id": "existing",
                "source_ref": self._reference(record),
                "content": json.dumps(record, sort_keys=True, ensure_ascii=False),
            }
            if kind == "wrong_content":
                row["content"] = "different"
            if kind == "wrong_reference":
                row["source_ref"] = "different"
            return [row] * (100 if kind == "page_limit" else 2 if kind == "duplicate" else 1)

    store = Remote("https://example.invalid", "synthetic", tmp_path / "ledger")
    result = store.reconcile([record], max_pages=1)
    assert result["status"] == "REVIEW_REQUIRED"
    assert result["recovered"] == 0
    assert not store.ledger.exists()
    assert store.sync([record])["deferred"] == 1


def test_mismatch_not_retried_for_changed_content(tmp_path, record):
    class Remote(KiraKnowledgeStore):
        calls = 0

        def _request(self, method, path, body=None):
            self.calls += 1
            return {"id": "other", "content": "different"}

    store = Remote("https://example.invalid", "synthetic", tmp_path / "ledger")
    assert store.sync([record])["failed"] == 1
    result = store.sync([{**record, "commit_sha": "changed"}])
    assert result["status"] == "REVIEW_REQUIRED"
    assert result["deferred"] == 1
    assert store.calls == 1


def test_uncertain_update_does_not_reuse_previous_acknowledgement(tmp_path, record):
    class Remote(KiraKnowledgeStore):
        def _request(self, method, path, body=None):
            if method == "PUT":
                raise TimeoutError
            return {"id": "existing", "content": body["content"]}

    store = Remote("https://example.invalid", "synthetic", tmp_path / "ledger")
    assert store.sync([record])["stored"] == 1
    assert store.sync([{**record, "commit_sha": "two"}])["failed"] == 1
    result = store.sync([record])
    assert result["status"] == "REVIEW_REQUIRED"
    assert result["unchanged"] == 0
    assert result["deferred"] == 1


def test_reconciliation_reads_complete_pagination(tmp_path, record):
    class Remote(KiraKnowledgeStore):
        offsets = []

        def _request(self, method, path, body=None):
            self.offsets.append(path.rsplit("offset=", 1)[1])
            if self.offsets[-1] == "0":
                return [{"id": str(i), "source_ref": "unrelated"} for i in range(100)]
            return [
                {
                    "id": "existing",
                    "source_ref": self._reference(record),
                    "content": json.dumps(record, sort_keys=True, ensure_ascii=False),
                }
            ]

    store = Remote("https://example.invalid", "synthetic", tmp_path / "ledger")
    assert store.reconcile([record])["status"] == "PASS"
    assert store.offsets == ["0", "100"]
