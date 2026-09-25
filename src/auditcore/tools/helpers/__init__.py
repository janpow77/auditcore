"""Helper contracts for application repositories (``auditcore-helpers``).

Makes the one-off helper inventories (``docs/reports/app-helfer-*.md``) a
permanent check: a scanner for helper functions and duplicates of auditcore
library functions, declarative lint rules for known error patterns, and a
runner for the shared contract cases in ``contracts/common-cases``. Results are
ratcheted per app against ``.auditcore/helpers-baseline.json``.
"""
