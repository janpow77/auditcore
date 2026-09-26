"""Shipped profiles: complete, source-bound, fingerprinted and strictly validated."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from auditcore_price_analysis import (
    ProfileError,
    available_profiles,
    calculation_profile_from_dict,
    comparison_profile_from_dict,
    load_calculation_profile,
    load_comparison_profile,
)

ROOT = Path(__file__).parents[1]
PROVENANCE = json.loads((ROOT / "provenance.json").read_text(encoding="utf-8"))


def test_shipped_profiles_and_versions() -> None:
    rows = available_profiles()
    assert [(r["profile_id"], r["version"], r["type"], r["status"]) for r in rows] == [
        ("regulierung.hpp.nahwaerme", "2026.09.1", "calculation", "SOURCE_CHARACTERIZED"),
        ("regulierung.hpp.nahwaerme", "2026.09.2", "calculation", "DECIDED"),
        ("regulierung.hpp.vergleich", "2026.09.1", "comparison", "SOURCE_CHARACTERIZED"),
        ("regulierung.hpp.vergleich", "2026.09.2", "comparison", "DECIDED"),
        ("regulierung.hpp.wasser", "2026.09.1", "calculation", "SOURCE_CHARACTERIZED"),
        ("regulierung.hpp.wasser", "2026.09.2", "calculation", "DECIDED"),
    ]
    assert [r["recommended"] for r in rows] == [False, True] * 3
    assert all(len(r["fingerprint"]) == 64 for r in rows)
    listed = {f"{r['profile_id']}@{r['version']}" for r in rows}
    assert listed == set(PROVENANCE["profiles"])


def test_profiles_are_bound_to_the_characterized_source_blobs() -> None:
    blobs = {f["path"]: f["git_blob"] for f in PROVENANCE["sources"][0]["files"]}
    for name, version in (
        (n, v)
        for n in ("regulierung.hpp.nahwaerme", "regulierung.hpp.wasser")
        for v in ("2026.09.1", "2026.09.2")
    ):
        source = load_calculation_profile(name, version).source
        assert source["commit"] == PROVENANCE["sources"][0]["commit"]
        assert blobs[source["path"]] == source["git_blob"]
    comparison = load_comparison_profile("regulierung.hpp.vergleich", "2026.09.1").source
    assert {f["path"]: f["git_blob"] for f in comparison["files"]} == blobs


def test_version_must_be_explicit_and_known() -> None:
    with pytest.raises(ProfileError):
        load_calculation_profile("regulierung.hpp.nahwaerme", "2099.01.1")
    with pytest.raises(ProfileError):
        load_comparison_profile("regulierung.hpp.nahwaerme", "2026.09.1")


def test_units_and_levy_windows_are_explicit() -> None:
    nw = load_calculation_profile("regulierung.hpp.nahwaerme", "2026.09.1")
    units = {c.name: c.unit for c in nw.components}
    assert units["arbeitspreis_ct_kwh"] == "ct/kWh" and units["grundpreis_eur_kw"] == "EUR/(kW·a)"
    old = nw.component("umlagenpreis_ct_kwh")
    new = nw.component("waermeumlagenpreis_ct_kwh")
    assert str(old.valid_until) == "2025-06-30" and str(new.valid_from) == "2025-07-01"
    wa = load_calculation_profile("regulierung.hpp.wasser", "2026.09.1")
    assert wa.tiers is not None and wa.tiers.open_last and wa.tiers.unit == "EUR/m³"
    assert {c.name: str(c.legacy_default) for c in wa.consumption} == {"q3": "4", "m3": "150"}


def _raw(name: str) -> dict[str, Any]:
    profile = load_calculation_profile(name, "2026.09.1")
    return json.loads(json.dumps(profile.raw))


@pytest.mark.parametrize(
    "change",
    [
        lambda d: d.update(schema="x"),
        lambda d: d.pop("source"),
        lambda d: d["components"][0].update(basis="unbekannt"),
        lambda d: d["components"][0].update(factor=1),
        lambda d: d["components"].append(dict(d["components"][0])),
        lambda d: d["rounding"]["money"].update(mode="ROUND_WHATEVER"),
        lambda d: d["rounding"]["money"].update(places="0"),
        lambda d: d["mixed_price"].update(basis="q"),
        lambda d: d["components"][1].update(valid_from="2025-13-01"),
    ],
)
def test_malformed_calculation_profiles_are_rejected(change: Any) -> None:
    data = _raw("regulierung.hpp.nahwaerme")
    change(data)
    with pytest.raises(ProfileError):
        calculation_profile_from_dict(data)


def test_tier_rule_must_be_referenced() -> None:
    data = _raw("regulierung.hpp.wasser")
    data["components"][1].pop("tiered_by")
    with pytest.raises(ProfileError):
        calculation_profile_from_dict(data)


@pytest.mark.parametrize(
    "change",
    [
        lambda d: d["traffic_light"].update(threshold_pct="-1"),
        lambda d: d["traffic_light"].update(yellow_from_fraction="1.5"),
        lambda d: d["statistics"].update(stddev="robust"),
        lambda d: d.update(type="calculation"),
    ],
)
def test_malformed_comparison_profiles_are_rejected(change: Any) -> None:
    data = json.loads(
        json.dumps(load_comparison_profile("regulierung.hpp.vergleich", "2026.09.1").raw)
    )
    change(data)
    with pytest.raises(ProfileError):
        comparison_profile_from_dict(data)


def test_fingerprint_changes_with_any_rule() -> None:
    data = _raw("regulierung.hpp.nahwaerme")
    base = calculation_profile_from_dict(data).fingerprint
    data["rounding"]["money"]["mode"] = "ROUND_HALF_EVEN"
    assert calculation_profile_from_dict(data).fingerprint != base
