"""Contract runner: reference implementations pass, known bugs are reported."""

from __future__ import annotations

from pathlib import Path

import pytest
from helper_contracts_support import CASES, FIXTURES, node_or_skip

from auditcore.tools.helpers.cases import load_cases
from auditcore.tools.helpers.compare import Outcome, as_decimal, compare, normalise_csv
from auditcore.tools.helpers.contracts import FAIL, SKIP, build_args, run_contracts
from auditcore.tools.helpers.manifest import Binding, Manifest, load_manifest
from auditcore.tools.helpers.model import HelperToolError, redact, write_json

LIBRARY = load_cases(CASES)


def _runs(app: str, language: str) -> dict[str, list[str]]:
    root = FIXTURES / app
    manifest = load_manifest(root / ".auditcore/helpers.json")
    selected = Manifest(bindings=tuple(b for b in manifest.bindings if b.language == language))
    runs = run_contracts(selected, LIBRARY, root)
    assert all(not run.load_error for run in runs), [run.load_error for run in runs]
    return {run.binding.id: [v.case for v in run.violations] for run in runs}


def test_python_reference_fulfils_every_contract() -> None:
    violations = _runs("reference", "python")
    assert violations and all(cases == [] for cases in violations.values()), violations


def test_typescript_reference_fulfils_every_contract() -> None:
    node_or_skip()
    violations = _runs("reference", "ts")
    assert len(violations) == 12
    assert all(cases == [] for cases in violations.values()), violations


def test_python_bug_is_reported_per_case() -> None:
    violations = _runs("buggy", "python")["py-parse"]
    assert "de-mehrdeutig-punkt" in violations and "de-euro-vorn" in violations
    assert "de-tausender-dezimal" not in violations


def test_typescript_bugs_are_reported_per_case() -> None:
    node_or_skip()
    violations = _runs("buggy", "ts")
    assert {"de-mehrdeutig-punkt", "de-leer"} <= set(violations["ts-parse"])
    assert {"reines-datum", "utc-abend-winter", "leer-null"} <= set(violations["ts-date"])
    assert "detail-422-liste" in violations["ts-error"]


def test_skipped_cases_need_a_reason_and_are_reported(tmp_path: Path) -> None:
    manifest = {
        "schema_version": 1,
        "bindings": [
            {
                "contract": "format-date",
                "language": "python",
                "module": "x",
                "export": "f",
                "skip": {"reines-datum": " "},
            }
        ],
    }
    write_json(tmp_path / "m.json", manifest)
    with pytest.raises(HelperToolError):
        load_manifest(tmp_path / "m.json")
    root = FIXTURES / "reference"
    binding = Binding(
        "b",
        "format-date",
        "python",
        "refapp.helpers",
        "format_date",
        skip={"reines-datum": "nur Zeitstempel"},
        python_path=("backend",),
    )
    [run] = run_contracts(Manifest(bindings=(binding,)), LIBRARY, root)
    assert [r.case for r in run.results if r.status == SKIP] == ["reines-datum"]
    assert not [r for r in run.results if r.status == FAIL]


def test_load_error_counts_as_one_violation() -> None:
    binding = Binding("b", "iban-valid", "python", "gibt.es.nicht", "f")
    [run] = run_contracts(Manifest(bindings=(binding,)), LIBRARY, FIXTURES / "reference")
    assert run.load_error and run.keys() == ["contract|b|laden"]


def test_argument_mapping() -> None:
    case = LIBRARY.contract("api-error-message").cases[0]
    spec = ({"path": "error.response.data"}, {"literal": "x"}, {"object": {"fb": "fallback"}})
    data, literal, options = build_args(spec, (), case)
    assert data == {"detail": "Vorhaben nicht gefunden"} and literal == "x"
    assert options == {"fb": "Unbekannter Fehler"}


def test_comparators() -> None:
    assert as_decimal(1234.56) == as_decimal("1234.56") == as_decimal({"$decimal": "1234.560"})
    assert compare("decimal", {"invalid": True}, Outcome(value={"$nan": True}))[0]
    assert compare("decimal", {"invalid": True}, Outcome(error="ValueError"))[0]
    assert not compare("decimal", {"invalid": True}, Outcome(value=0))[0]
    assert not compare("boolean", {"value": True}, Outcome(value=1))[0]
    assert compare(
        "text-contains", {"contains": ["a"], "not_contains": ["b"]}, Outcome(value="xa")
    )[0]
    assert not compare("text-contains", {"contains": ["a"]}, Outcome(value=["a"]))[0]
    assert normalise_csv("a\r\nb\r\n") == "a\nb"


def test_load_errors_never_echo_input_values(tmp_path: Path) -> None:
    (tmp_path / "settings_app.py").write_text(
        'raise ValueError("1 validation error for Settings\\n'
        "api_key\\n  Extra inputs [input_value='streng-geheim', input_type=str]\")\n"
    )
    binding = Binding("s", "iban-valid", "python", "settings_app", "f")
    [run] = run_contracts(Manifest(bindings=(binding,)), LIBRARY, tmp_path)
    assert "validation error" in run.load_error
    assert "streng-geheim" not in run.load_error


def test_redaction_of_echoed_values() -> None:
    text = "ValidationError: x input_value='abc' and input=\"def\"\nzweite Zeile"
    assert redact(text) == "ValidationError: x input_value=*** and input=***"
    assert redact("a\nb\n", last=True) == "b"
