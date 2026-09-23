"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from importlib.metadata import distribution
from importlib.util import find_spec

import auditcore_market_indicators as mi


def main() -> None:
    """Indicators, packaged profiles and the error contract from the installed package."""
    package = distribution("auditcore_market_indicators")
    assert package.version == "0.1.0" and mi.__version__ == "0.1.0"
    assert not [r for r in package.requires or [] if "extra ==" not in r]
    assert find_spec("auditcore") is None
    assert len(mi.available_profiles()) == 4
    base = mi.load_profile("krypto.indicators_base", "2026.09.1")
    scoring = mi.load_profile("krypto.scoring_rsi_macd", "2026.09.1")
    close = [100.0, 101.5, 99.8, 102.3, 103.0, 101.2, 104.8, 106.1, 105.0, 107.4]
    high = [c + 1.0 for c in close]
    low = [c - 1.0 for c in close]
    assert mi.sma(close, 3)[2] == (100.0 + 101.5 + 99.8) / 3
    assert mi.ema([10.0, 10.0, 10.0, 20.0], 3, profile=base)[3] == 15.0
    assert mi.rsi([7.0] * 6, 3, profile=base)[-1] == 100.0
    assert mi.rsi([7.0] * 6, 3, profile=scoring)[-1] == 50.0
    assert mi.atr(high, low, close, 3, profile=base)[2] is not None
    plus, minus, adx = mi.adx(high * 3, low * 3, close * 3, 3, profile=base)
    assert adx[6] is not None and plus[3] is not None
    assert mi.zscore([10.0] * 5, 3)[4] is None
    try:
        mi.sma([1.0, float("nan")], 1)
    except mi.IndicatorInputError as error:
        assert "nicht endlich" in str(error)
    else:
        raise AssertionError("NaN must be rejected")
    if find_spec("polars") is None:
        from auditcore_market_indicators import polars_adapter

        try:
            polars_adapter.sma(None, 1)  # type: ignore[arg-type]
        except mi.DependencyError:
            pass
        else:
            raise AssertionError("missing polars must raise DependencyError")
    reference = mi.method_reference("rsi", profile=base, n=14)
    assert reference["profile"] == base.reference
    print("PASS: installed auditcore_market_indicators indicators, profiles and error contract")


if __name__ == "__main__":
    main()
