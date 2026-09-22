"""KIRA Memory API adapter with pre-index screening and source revision checks."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from auditcore.tools.common import digest, now, read_json, write_json
from auditcore.tools.quality.scanners import scan_sensitive


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> None:
        """Never forward a KIRA credential to a redirected endpoint."""
        return None


class KiraKnowledgeStore:
    """Use the existing /entries and /search API; credentials stay outside reports."""

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        ledger: Path = Path(".auditcore/kira-ledger.json"),
    ) -> None:
        self.url = (url or os.environ.get("KIRA_MEMORY_URL", "")).rstrip("/")
        self.api_key = api_key or os.environ.get("MEMORY_API_KEY", "")
        self.ledger = ledger

    @property
    def configured(self) -> bool:
        """Whether both endpoint and credential were explicitly supplied."""
        return bool(self.url and self.api_key)

    def _request(self, method: str, path: str, body: Any = None) -> Any:
        parsed = urllib.parse.urlsplit(self.url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username:
            raise ValueError(
                "KIRA requires an explicit HTTP(S) endpoint without embedded credentials"
            )
        if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("Remote KIRA credentials require HTTPS")
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(
            self.url + path,
            data=data,
            method=method,
            headers={"X-Memory-API-Key": self.api_key, "Content-Type": "application/json"},
        )
        opener = urllib.request.build_opener(_NoRedirect())
        with opener.open(request, timeout=30) as response:
            content = response.read()
            return json.loads(content) if content else {}

    def sync(self, documents: list[dict[str, Any]]) -> dict[str, Any]:
        """Idempotently store screened structured records, retaining failed entries."""
        if not self.configured:
            return {"status": "NOT_CONFIGURED", "stored": 0, "reason": "KIRA URL/key missing"}
        ledger = read_json(self.ledger) if self.ledger.exists() else {}
        stored = skipped = blocked = failed = 0
        errors: list[dict[str, Any]] = []
        consecutive_failures = 0
        pending = 0
        for index, document in enumerate(documents):
            if consecutive_failures >= 3:
                pending = len(documents) - index
                break
            required = {
                "repository",
                "branch",
                "commit_sha",
                "path",
                "symbol",
                "type",
                "classification",
            }
            if not required.issubset(document) or document["classification"] not in {
                "OBSERVED",
                "DERIVED",
                "LLM_INFERRED",
                "HUMAN_CONFIRMED",
            }:
                blocked += 1
                continue
            content = json.dumps(document, sort_keys=True, ensure_ascii=False)
            if scan_sensitive(content):
                blocked += 1
                continue
            identity = ":".join(
                str(document[k]) for k in ("repository", "branch", "type", "path", "symbol")
            )
            reference = "auditcore:" + digest(identity)
            fingerprint = digest(content)
            previous = ledger.get(reference, {})
            if previous.get("digest") == fingerprint:
                skipped += 1
                continue
            payload = {
                "content": content,
                "category": "graph",
                "project": document["repository"],
                "source_type": "agent",
                "source_ref": reference,
                "tags": ["auditcore", document["type"], document["classification"]],
                "confidence": 1.0 if document["classification"] == "OBSERVED" else 0.5,
            }
            try:
                if previous.get("id"):
                    result = self._request(
                        "PUT",
                        "/entries/" + urllib.parse.quote(previous["id"]),
                        {k: payload[k] for k in ("content", "tags", "confidence")},
                    )
                else:
                    result = self._request("POST", "/entries", payload)
                identifier = result.get("id") or previous.get("id")
                if not identifier or result.get("content") != content:
                    failed += 1
                    consecutive_failures += 1
                    errors.append({"reference": reference, "error": "RESPONSE_CONTENT_MISMATCH"})
                    continue
                ledger[reference] = {
                    "id": identifier,
                    "digest": fingerprint,
                    "commit_sha": document["commit_sha"],
                    "indexed_at": now(),
                }
                write_json(self.ledger, ledger)
                stored += 1
                consecutive_failures = 0
            except (OSError, ValueError, urllib.error.URLError) as exc:
                failed += 1
                consecutive_failures += 1
                validation: list[dict[str, Any]] = []
                if isinstance(exc, urllib.error.HTTPError) and exc.code == 422:
                    try:
                        detail = json.loads(exc.read()).get("detail", [])
                        if isinstance(detail, str) and (
                            "blacklist" in detail.lower() or "blocked" in detail.lower()
                        ):
                            validation = [{"type": "REMOTE_CONTENT_REJECTED"}]
                        elif isinstance(detail, list):
                            # Never retain error input values: these may contain source or secrets.
                            validation = [
                                {"location": item.get("loc"), "type": item.get("type")}
                                for item in detail
                                if isinstance(item, dict)
                            ]
                    except (ValueError, OSError):
                        pass
                errors.append(
                    {
                        "validation": validation,
                        "reference": reference,
                        "error": type(exc).__name__,
                        "http_status": getattr(exc, "code", None),
                    }
                )
        return {
            "status": "FAIL" if failed else "REVIEW_REQUIRED" if blocked else "PASS",
            "stored": stored,
            "unchanged": skipped,
            "screening_blocked": blocked,
            "failed": failed,
            "pending": pending,
            "errors": errors,
        }

    def search(self, query: str) -> dict[str, Any]:
        """Semantic search; an empty index is not proof that code does not exist."""
        if not self.configured:
            return {"status": "NOT_CONFIGURED", "results": []}
        if scan_sensitive(query):
            return {"status": "REVIEW_REQUIRED", "results": [], "reason": "Query screening"}
        try:
            response = self._request(
                "POST", "/search", {"query": query, "limit": 20, "category": "graph"}
            )
            results = response.get("results", []) if isinstance(response, dict) else response
            return {
                "status": "PASS" if results else "NOT_FOUND_IN_CURRENT_INDEX",
                "results": results,
            }
        except (OSError, ValueError, urllib.error.URLError):
            return {"status": "NOT_EXECUTED", "results": []}

    @staticmethod
    def freshness(document: dict[str, Any], github_commit: str) -> str:
        """Compare indexed revision with source-of-truth revision."""
        return "CURRENT" if document.get("commit_sha") == github_commit else "STALE"


class KiraSemanticAnalysis:
    """Source-linked semantic candidates, explicitly unconfirmed until compared."""

    def __init__(self, store: KiraKnowledgeStore) -> None:
        self.store = store

    def compare(self, symbols: list[dict[str, Any]]) -> dict[str, Any]:
        """Search names and domain labels; never assert equivalence from retrieval."""
        query = " ".join(str(s.get("symbol", "")) for s in symbols[:10])
        return {
            **self.store.search(query),
            "classification": "LLM_INFERRED",
            "semantic_equivalence": "REVIEW_REQUIRED",
        }
