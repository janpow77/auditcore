"""Chi-square test with critical values and z per digit (library and REST contract)."""

from __future__ import annotations

import math

import pytest

from auditcore_statistics import (
    StatisticsInputError,
    benford_test,
    chi2_critical_value,
    chi2_survival,
    chi_square_test,
    digit_z_test,
)
from auditcore_statistics.conformity import assess
from auditcore_statistics.web import ContractError, analyse, catalogue
from auditcore_statistics.web._http import decode

VALUES = [round(10 ** (1 + (i * 0.6180339887) % 3), 2) for i in range(400)] + [500] * 40


@pytest.mark.parametrize(
    ("dof", "level", "table"),
    [
        (8, 0.10, 13.362),
        (8, 0.05, 15.507),
        (8, 0.01, 20.090),
        (9, 0.05, 16.919),
        (89, 0.05, 112.022),
        (1, 0.05, 3.841),
    ],
)
def test_critical_values_match_the_chi_square_table(dof: int, level: float, table: float) -> None:
    value = chi2_critical_value(dof, level)
    assert round(value, 3) == table
    assert math.isclose(chi2_survival(value, dof), level, rel_tol=1e-12)


@pytest.mark.parametrize(("dof", "level"), [(0, 0.05), (8, 0.0), (8, 1.0), (8, True)])
def test_critical_value_rejects_invalid_arguments(dof: int, level: float) -> None:
    with pytest.raises(StatisticsInputError):
        chi2_critical_value(dof, level)


def test_chi_square_decides_only_with_an_explicit_level() -> None:
    result = benford_test(VALUES, digits=1)
    plain = chi_square_test(result, "first")
    assert plain.rejects is None and plain.critical_value is None
    assert [c.level for c in plain.critical_values] == [0.10, 0.05, 0.01]
    assert plain.chi2_statistic == result.chi2_statistic and plain.p_value == result.p_value
    chosen = chi_square_test(result, "first", significance_level=0.025)
    assert [c.level for c in chosen.critical_values] == [0.10, 0.05, 0.025, 0.01]
    assert chosen.rejects is (chosen.p_value < 0.025)
    assert chosen.critical_value == chi2_critical_value(8, 0.025)


def test_second_digit_test_uses_ten_classes_like_the_conformity_profile() -> None:
    result = benford_test(VALUES, digits=2, short_values="exclude")
    chi = chi_square_test(result, "second", significance_level=0.05)
    conformity = assess(result, "second", "nigrini.2012")
    assert chi.degrees_of_freedom == 9
    assert chi.chi2_statistic == conformity.chi2_statistic


def test_digit_z_marks_only_against_an_explicit_critical_value() -> None:
    result = benford_test(VALUES, digits=1)
    plain = digit_z_test(result, "first", continuity_correction=False)
    assert plain.exceeding_digits is None and {r.exceeds for r in plain.rows} == {None}
    marked = digit_z_test(result, "first", continuity_correction=False, z_critical=2.576)
    assert marked.exceeding_digits == tuple(r.digit for r in marked.rows if r.z > 2.576)
    assert 5 in (marked.exceeding_digits or ())


def test_digit_z_with_correction_equals_the_nigrini_profile() -> None:
    result = benford_test(VALUES, digits=1)
    z = digit_z_test(result, "first", continuity_correction=True, z_critical=1.96)
    conformity = assess(result, "first", "nigrini.2012")
    assert [r.z for r in z.rows] == [r.z for r in conformity.rows]
    assert z.exceeding_digits == conformity.exceeding_digits


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"continuity_correction": 1}, "true oder false"),
        ({"continuity_correction": False, "z_critical": 0}, "positive Zahl"),
    ],
)
def test_digit_z_rejects_invalid_parameters(kwargs: dict[str, object], message: str) -> None:
    result = benford_test(VALUES, digits=1)
    with pytest.raises(StatisticsInputError, match=message):
        digit_z_test(result, "first", **kwargs)  # type: ignore[arg-type]


def test_rest_catalogue_names_the_optional_metrics() -> None:
    data = catalogue()
    assert [m["id"] for m in data["metrics"]] == ["chi_square", "digit_z"]
    assert data["standard_levels"] == [0.1, 0.05, 0.01]


def test_rest_answer_is_unchanged_without_metrics() -> None:
    answer = analyse({"test": "first", "profile": "nigrini.2012", "values": VALUES})
    assert "metrics" not in answer


def test_rest_metrics_are_computed_on_request() -> None:
    body = decode(
        b'{"test": "first", "profile": "nigrini.2012", "values": ['
        + ",".join(str(v) for v in VALUES).encode()
        + b'], "metrics": {"chi_square": {"significance_level": 0.05}, '
        b'"digit_z": {"continuity_correction": false, "z_critical": 2.576}}}'
    )
    metrics = analyse(body)["metrics"]
    assert isinstance(metrics, dict)
    chi, z = metrics["chi_square"], metrics["digit_z"]
    assert round(chi["critical_value"], 3) == 15.507 and chi["degrees_of_freedom"] == 8
    assert chi["rejects"] is (chi["p_value"] < 0.05)
    assert z["z_critical"] == 2.576 and z["continuity_correction"] is False
    assert z["exceeding_digits"] == [r["digit"] for r in z["rows"] if r["exceeds"]]


@pytest.mark.parametrize(
    ("metrics", "message"),
    [
        ([], "'metrics' muss ein Objekt"),
        ({"mad": {}}, "Unbekannte Kennzahlen"),
        ({"chi_square": 1}, "muss ein Objekt"),
        ({"chi_square": {"alpha": 0.05}}, "unbekannte Felder"),
        ({"chi_square": {"significance_level": "0.05"}}, "muss eine Zahl"),
        ({"chi_square": {"significance_level": 1.5}}, "zwischen 0 und 1"),
        ({"digit_z": {}}, "continuity_correction"),
        ({"digit_z": {"continuity_correction": True, "z_critical": -1}}, "positive Zahl"),
    ],
)
def test_rest_rejects_invalid_metric_requests(metrics: object, message: str) -> None:
    body = {"test": "first", "profile": "nigrini.2012", "values": VALUES, "metrics": metrics}
    with pytest.raises(ContractError, match=message):
        analyse(body)
