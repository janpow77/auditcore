"""Profiles are explicit, versioned, source-bound and validated without defaults."""

from __future__ import annotations

import copy
import json
from importlib import resources
from typing import Any

import pytest
from replay import fixture

import auditcore_market_indicators as mi
from auditcore_market_indicators.profiles import fingerprint

PACKAGED = [
    ("krypto.indicators_base", "2026.09.1"),
    ("krypto.regime_hmm", "2026.09.1"),
    ("krypto.scoring_confluence", "2026.09.1"),
    ("krypto.scoring_rsi_macd", "2026.09.1"),
]


def document(name: str) -> dict[str, Any]:
    entry = resources.files("auditcore_market_indicators.profile_data").joinpath(
        f"{name}-2026.09.1.json"
    )
    data: dict[str, Any] = json.loads(entry.read_text(encoding="utf-8"))
    return data


def test_packaged_profiles_are_listed_and_none_is_a_default() -> None:
    assert mi.available_profiles() == tuple(PACKAGED)
    assert not hasattr(mi, "DEFAULT_PROFILE")


@pytest.mark.parametrize(("profile_id", "version"), PACKAGED)
def test_profiles_are_source_bound_and_fingerprinted(profile_id: str, version: str) -> None:
    profile = mi.load_profile(profile_id, version)
    data = document(profile_id)
    assert profile.fingerprint == fingerprint(data)
    assert profile.reference == {
        "id": profile_id,
        "version": version,
        "fingerprint": profile.fingerprint,
    }
    source = profile.source
    assert source["repository"] == "janpow77/krypto"
    assert source["commit"] == fixture()["source"]["commit"]
    assert fixture()["source"]["files"][source["path"]]["git_blob"] == source["git_blob"]
    assert source["rights"] == "USER_AUTHORIZED_MIT"
    assert profile.status == "CHARACTERIZED" and "keine" in profile.legal_status
    json.dumps(mi.profile_document(profile))


def test_profile_rules_equal_the_characterized_sources() -> None:
    base = mi.load_profile("krypto.indicators_base", "2026.09.1")
    assert (base.summation, base.ema, base.atr) == (
        "neumaier",
        mi.profiles.EmaRule("sma", "skip"),
        mi.profiles.AtrRule("sma"),
    )
    assert base.rsi == mi.profiles.RsiRule("wilder", 100.0, "zero_move")
    scoring = mi.load_profile("krypto.scoring_rsi_macd", "2026.09.1")
    assert scoring.summation == "numpy_pairwise" and scoring.macd
    assert scoring.ema == mi.profiles.EmaRule("sma", "hold")
    assert scoring.rsi == mi.profiles.RsiRule("wilder", 50.0, "zero_move")
    hmm = mi.load_profile("krypto.regime_hmm", "2026.09.1")
    assert hmm.ema == mi.profiles.EmaRule("first_value", "error") and hmm.rsi is None


def mutate(path: tuple[str, ...], value: Any) -> dict[str, Any]:
    data = copy.deepcopy(document("krypto.indicators_base"))
    target = data
    for key in path[:-1]:
        target = target[key]
    if value is KeyError:
        del target[path[-1]]
    else:
        target[path[-1]] = value
    return data


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("schema",), "x/1", "Profilschema"),
        (("id",), "", "nicht leerer Text"),
        (("summation",), "kahan", "zulässige Variante"),
        (("ema", "seed"), "wma", "zulässige Variante"),
        (("ema", "gaps"), "fill", "zulässige Variante"),
        (("rsi", "smoothing"), "cutler", "zulässige Variante"),
        (("rsi", "flat_value"), 120.0, "zwischen 0 und 100"),
        (("rsi", "flat_value"), True, "Zahl"),
        (("atr", "smoothing"), "rma", "zulässige Variante"),
        (("adx",), KeyError, "fehlt"),
        (("adx",), [], "Objekt oder null"),
        (("source",), "x", "source"),
        (("status",), KeyError, "unvollständig"),
    ],
)
def test_invalid_profile_documents_are_rejected(
    path: tuple[str, ...], value: Any, message: str
) -> None:
    with pytest.raises(mi.ProfileError, match=message):
        mi.profile_from_dict(mutate(path, value))


def test_structural_profile_errors() -> None:
    data = document("krypto.scoring_confluence")
    data["ema"] = None
    data["macd"] = {}
    with pytest.raises(mi.ProfileError, match="setzt einen ema"):
        mi.profile_from_dict(data)
    data["macd"] = None
    with pytest.raises(mi.ProfileError, match="keinen Indikator"):
        mi.profile_from_dict(data)
    with pytest.raises(mi.ProfileError, match="nicht vorhanden"):
        mi.load_profile("krypto.indicators_base", "1999.01.1")
    with pytest.raises(mi.ProfileError, match="Ungültige"):
        mi.load_profile("../krypto", "x")
    with pytest.raises(mi.ProfileError, match="als Text"):
        mi.load_profile("krypto.indicators_base", 1)  # type: ignore[arg-type]


def test_own_profiles_can_be_built_but_change_the_fingerprint() -> None:
    data = document("krypto.indicators_base")
    data["id"] = "eigene.wilder_atr"
    data["atr"] = {"smoothing": "wilder"}
    own = mi.profile_from_dict(data)
    assert own.atr == mi.profiles.AtrRule("wilder")
    assert own.fingerprint != mi.load_profile("krypto.indicators_base", "2026.09.1").fingerprint
