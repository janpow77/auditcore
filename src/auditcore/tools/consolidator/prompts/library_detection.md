---
name: library_detection
version: 2.0
change_reason: ADR-001 domain distributions and conservative candidate selection
---

Find reusable business parsers, validators and calculations. Propose a domain distribution auditcore_{domain} under packages/, following ADR-001; the platform auditcore is not an automatic runtime dependency. Exclude tests, generated code, database migrations and application infrastructure. Keep generic helpers pending domain review. Similar names do not prove equivalent semantics. Embedded copies and identical revisions do not establish independent consumers. Unknown licenses require review, not automatic rejection.

Output structured JSON with classification OBSERVED, DERIVED or LLM_INFERRED, source references, uncertainty and required human decisions. Never label unexecuted tests PASS.
