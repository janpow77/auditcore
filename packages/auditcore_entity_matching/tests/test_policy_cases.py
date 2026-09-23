"""Framework catalogue cases for this library (T-11, T-14); T-37/T-38 see tools/policy_proof.py."""

from __future__ import annotations

import ast
from pathlib import Path

import auditcore_entity_matching
from auditcore_entity_matching import check_lei, load_profile, normalize


def test_t14_library_writes_no_logs() -> None:
    package = Path(auditcore_entity_matching.__file__).parent
    for path in package.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] + [getattr(node, "module", "") or ""]
                assert "logging" not in {n.split(".")[0] for n in names}, path.name


def test_t11_personal_names_are_processed_in_memory_only() -> None:
    """Names of natural persons may be passed in; nothing is retained or stored."""
    profile = load_profile("flowworkshop.sanctions", "2026.09.1")
    before = dict(vars(auditcore_entity_matching.normalize))
    assert normalize("José Strauß", profile) == "jose strauss"
    assert dict(vars(auditcore_entity_matching.normalize)) == before
    assert check_lei("529900T8BM49AURSDO55").normalized == "529900T8BM49AURSDO55"
