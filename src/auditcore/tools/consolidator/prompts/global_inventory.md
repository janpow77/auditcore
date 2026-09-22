---
name: global_inventory
version: 1.0
change_reason: Initial source-grounded analysis contract
---

Compare all discovered repositories, retain exclusions and exact commits. Do not modify applications during inventory.

Output structured JSON with classification OBSERVED, DERIVED or LLM_INFERRED, source references, uncertainty and required human decisions. Never label unexecuted tests PASS.
