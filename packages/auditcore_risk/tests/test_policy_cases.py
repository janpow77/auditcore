"""Framework catalogue cases for this library (T-11, T-14); T-37/T-38 see tools/policy_proof.py."""

from __future__ import annotations

import ast
from pathlib import Path

import auditcore_risk
from auditcore_risk import evaluate, load_profile


def test_t14_library_writes_no_logs() -> None:
    package = Path(auditcore_risk.__file__).parent
    for path in package.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import | ast.ImportFrom):
                names = [a.name for a in node.names] + [getattr(node, "module", "") or ""]
                assert "logging" not in {n.split(".")[0] for n in names}, path.name


def test_t11_names_are_processed_in_memory_only() -> None:
    """Begünstigten-/Rechnungsstellernamen können natürliche Personen bezeichnen.

    The library compares them in memory; it keeps no state between calls and
    returns them only inside the caller's own evaluation result.
    """
    profile = load_profile("riskanalysis.legacy", "b5c523bf7eaa")
    import auditcore_risk.rules as rules

    before = {k: v for k, v in vars(rules).items() if not k.startswith("__")}
    rows = [
        {
            "bruttobetrag": 100.0,
            "Name": "Erika Mustermann",
            "zahlungsempfaenger": "Erika Mustermann",
        }
    ]
    result = evaluate(rows, profile)
    assert result.records[0].codes == ("RF09",)
    after = {k: v for k, v in vars(rules).items() if not k.startswith("__")}
    assert before == after
    second = evaluate([{"bruttobetrag": 1.0, "Name": "A", "zahlungsempfaenger": "B"}], profile)
    assert "Erika" not in repr(second.to_dict())
