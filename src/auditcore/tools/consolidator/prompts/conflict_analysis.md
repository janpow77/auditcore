---
name: conflict_analysis
version: 1.0
change_reason: Initial source-grounded analysis contract
---

Compare thresholds, legal assumptions, security boundaries and outputs. Emit HUMAN_DECISION_REQUIRED or SECURITY_OR_POLICY_REVIEW_REQUIRED for conflicts.

Output structured JSON with classification OBSERVED, DERIVED or LLM_INFERRED, source references, uncertainty and required human decisions. Never label unexecuted tests PASS.
