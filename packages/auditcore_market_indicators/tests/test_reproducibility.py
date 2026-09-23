"""Framework T-31 (F-17): same input, version and profile give the same, self-describing result."""

from __future__ import annotations

import json
import random

import auditcore_market_indicators as mi


def test_repeated_runs_are_identical_and_self_describing(base: mi.IndicatorProfile) -> None:
    rng = random.Random(17)
    close = [100.0]
    for _ in range(499):
        close.append(close[-1] * (1 + rng.gauss(0, 0.02)))
    high = [c * 1.01 for c in close]
    low = [c * 0.99 for c in close]
    first = (
        mi.ema(close, 20, profile=base),
        mi.rsi(close, 14, profile=base),
        list(mi.adx(high, low, close, 14, profile=base)),
        mi.zscore(close, 20),
    )
    second = (
        mi.ema(list(close), 20, profile=base),
        mi.rsi(tuple(close), 14, profile=base),
        list(mi.adx(high, low, close, 14, profile=base)),
        mi.zscore(close, 20),
    )
    assert json.dumps(first) == json.dumps(second)
    reference = mi.method_reference("rsi", profile=base, n=14)
    again = mi.method_reference("rsi", profile=mi.load_profile(base.id, base.version), n=14)
    assert reference == again
    assert reference["profile"]["fingerprint"] == base.fingerprint  # type: ignore[index]
