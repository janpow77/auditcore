"""Parity of the value-share draw with recorded runs of the source implementation.

``fixtures/intermediate_body_observed.json.gz`` holds 240 synthetic payment
claims drawn by flowinvoice (``tools/capture_intermediate_body.py``, pinned
Git blob) with fixed seeds: inputs, derived seed, the NumPy permutation and
the drawn positions with their ladder stage. The library must reproduce the
seed derivation, the ladder and – given the same order – every draw exactly;
with NumPy installed the order itself is regenerated from the seed.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

import pytest

from auditcore_sampling.intermediate_body import (
    PROFILES,
    VALUE_SHARE_ESCALATION,
    derived_seed,
    escalation_ladder,
    value_share_draw,
)

FIXTURE = Path(__file__).parent / "fixtures" / "intermediate_body_observed.json.gz"
OBSERVED: dict[str, Any] = json.loads(gzip.decompress(FIXTURE.read_bytes()))
BASE = PROFILES[VALUE_SHARE_ESCALATION]


def test_fixture_is_pinned_to_the_source() -> None:
    assert OBSERVED["source"]["commit"].startswith("fb2d18568d2e")
    assert len(OBSERVED["cases"]) == 240
    assert {max(c["stages"], default=0) for c in OBSERVED["cases"]} >= {0, 1, 2, 5}


@pytest.mark.parametrize("row", OBSERVED["ladders"], ids=lambda r: str(r["start_share"]))
def test_ladder_parity(row: dict[str, Any]) -> None:
    chosen = BASE.with_parameters(start_share=row["start_share"])
    assert list(escalation_ladder(chosen)) == row["ladder"]


@pytest.mark.parametrize("case", OBSERVED["cases"], ids=lambda c: c["claim"])
def test_draw_parity(case: dict[str, Any]) -> None:
    assert derived_seed(case["base_seed"], case["claim"]) == case["derived_seed"]
    chosen = BASE.with_parameters(start_share=case["start_share"], escalate=case["escalate"])
    result = value_share_draw(case["amounts"], case["errors"], case["order"], chosen)
    assert list(result.positions) == case["drawn"]
    assert list(result.stages) == case["stages"]


def test_numpy_order_parity() -> None:
    """The recorded order is ``default_rng(derived_seed).permutation(n)`` of NumPy."""
    np = pytest.importorskip("numpy")
    for case in OBSERVED["cases"]:
        order = np.random.default_rng(case["derived_seed"]).permutation(len(case["amounts"]))
        assert [int(i) for i in order] == case["order"]
