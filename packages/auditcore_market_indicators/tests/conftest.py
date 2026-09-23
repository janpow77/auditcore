from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import auditcore_market_indicators as mi  # noqa: E402

VERSION = "2026.09.1"


@pytest.fixture(scope="session")
def base() -> mi.IndicatorProfile:
    return mi.load_profile("krypto.indicators_base", VERSION)


@pytest.fixture(scope="session")
def rsi_macd() -> mi.IndicatorProfile:
    return mi.load_profile("krypto.scoring_rsi_macd", VERSION)


@pytest.fixture(scope="session")
def confluence() -> mi.IndicatorProfile:
    return mi.load_profile("krypto.scoring_confluence", VERSION)


@pytest.fixture(scope="session")
def hmm() -> mi.IndicatorProfile:
    return mi.load_profile("krypto.regime_hmm", VERSION)
