---
name: library_detection
version: 1.0
change_reason: Initial source-grounded analysis contract
---

Find duplicate parsers, validators and calculations. Prefer a domain module inside auditcore. Similar names do not prove equivalent semantics.

Output structured JSON with classification OBSERVED, DERIVED or LLM_INFERRED, source references, uncertainty and required human decisions. Never label unexecuted tests PASS.
