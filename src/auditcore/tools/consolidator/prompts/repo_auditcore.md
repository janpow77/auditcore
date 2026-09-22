---
name: repo_auditcore
version: 1.0
change_reason: Initial source-grounded analysis contract
---

Search local code, auditcore, the inventory and KIRA before proposing new domain logic. Resolve hits against GitHub commits.

Output structured JSON with classification OBSERVED, DERIVED or LLM_INFERRED, source references, uncertainty and required human decisions. Never label unexecuted tests PASS.
