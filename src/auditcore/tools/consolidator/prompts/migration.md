---
name: migration
version: 1.0
change_reason: Initial source-grounded analysis contract
---

Propose a staged compatibility migration, rollback and consumer tests. Apprefactor owns changes. Never remove authorization, audit or validation boundaries.

Output structured JSON with classification OBSERVED, DERIVED or LLM_INFERRED, source references, uncertainty and required human decisions. Never label unexecuted tests PASS.
