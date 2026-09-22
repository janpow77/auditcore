---
name: repo_analysis
version: 1.0
change_reason: Initial source-grounded analysis contract
---

Identify imports, symbols, tests and dependencies at the supplied commit. Cite source paths and distinguish observed facts from inference.

Output structured JSON with classification OBSERVED, DERIVED or LLM_INFERRED, source references, uncertainty and required human decisions. Never label unexecuted tests PASS.
