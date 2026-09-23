"""Run with python -I after installing ``auditcore_market_indicators[polars]``."""

from importlib.metadata import distribution


def main() -> None:
    """The polars adapter keeps krypto's series names and dtypes."""
    import polars as pl

    extras = [
        r for r in distribution("auditcore_market_indicators").requires or [] if "polars" in r
    ]
    assert any(r.startswith("polars") and 'extra == "polars"' in r for r in extras)
    from auditcore_market_indicators import load_profile
    from auditcore_market_indicators import polars_adapter as mi

    base = load_profile("krypto.indicators_base", "2026.09.1")
    close = pl.Series("close", [100.0 + (i % 5) * 1.5 + i for i in range(40)])
    high, low = close + 1.0, close - 1.0
    assert mi.ema(close, 20, profile=base).name == "close"
    assert mi.atr(high, low, close, 14, profile=base).name == "tr"
    names = [s.name for s in mi.adx(high, low, close, 14, profile=base)]
    assert names == ["plus_di", "minus_di", "adx"]
    flag, strength = mi.breakout(close, pl.Series("volume", [1000.0] * 40), 20, 1.8)
    assert (str(flag.dtype), str(strength.dtype)) == ("Boolean", "Float64")
    print("PASS: installed auditcore_market_indicators[polars] adapter")


if __name__ == "__main__":
    main()
