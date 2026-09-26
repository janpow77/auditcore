"""Apply the documented krypto migration to a *copy* of a krypto checkout.

    python tools/migrate_krypto.py <krypto checkout copy>

Replaces the indicator arithmetic in the six characterized call sites with
calls into ``auditcore_market_indicators`` (profiles ``krypto.*`` 2026.09.1)
and keeps every public name and signature, so pipeline, scoring and tests are
unchanged. The tool refuses to run on a checkout whose files are not the
pinned blobs and never commits, pushes or touches a database.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import subprocess
from pathlib import Path

PINNED = {
    "backend/app/services/indicators/base.py": "1bad05faad43915662f87971ef0d8ae55a1b4fe0",
    "backend/app/services/indicators/pipeline.py": "56c3cfa2f8a9e5dc1e259d517a84c5cb2970d4e2",
    "backend/app/services/scoring/rsi_macd.py": "a3e8960b35f650c10e24451786d57fba404ae764",
    "backend/app/services/scoring/confluence.py": "52af074e196f454ce2715d316131841157de58cc",
    "backend/app/services/regime/hmm.py": "2ae11f35cd4a87ab74395a0a589dbfcab4f15d4e",
    "backend/app/services/scoring/ma_crossover.py": "1266032a8d8eaf96576095eb815d3f7a70d973e1",
    "backend/app/services/pipelines/hourly.py": "aa8dc53c4c998446b2e10502331382183a0e47f3",
    "backend/app/services/pipelines/four_hour.py": "3422f7e37885aafc4486f6df2f64e17bb3fb60a8",
    "backend/app/services/pipelines/daily.py": "bd6b0a27c6371fcc58ecc8e48506b82faacc1810",
}
#: Nutzerentscheidung vom 23.09.2026 („5. 250 kerzen“): Rückblick der Pipeline.
LOOKBACK_CALLS = {
    "backend/app/services/pipelines/hourly.py": "lookback=60,",
    "backend/app/services/pipelines/four_hour.py": "lookback=60,",
    "backend/app/services/pipelines/daily.py": "lookback=90,",
}

BASE = '''"""Vektorisierte Indikator-Grundfunktionen nach Pflichtenheft §7.1-7.7.

Die Berechnung liegt in ``auditcore_market_indicators`` (Profil
``krypto.entschieden`` 2026.09.1: Nutzerentscheidung vom 23.09.2026 auf Basis
des aus dieser Datei charakterisierten Profils ``krypto.indicators_base``).
Dieses Modul behält Namen, Signaturen, Serien-Namen und Rückgabetypen bei.
Fehlende oder undefinierte Werte sind ``None`` (nie NaN/inf); NaN in den
Eingaben wird abgewiesen. ATR nach Wilder, RSI ohne jede Bewegung = 50,
empfohlener Mindest-Rückblick ``PROFILE.min_lookback`` = 250 Kerzen.
"""

from __future__ import annotations

import polars as pl
from auditcore_market_indicators import RECOMMENDED_PROFILE, load_profile
from auditcore_market_indicators import polars_adapter as _mi

PROFILE = load_profile(*RECOMMENDED_PROFILE)


def returns(close: pl.Series, periods: int) -> pl.Series:
    return _mi.returns(close, periods)


def log_returns(close: pl.Series) -> pl.Series:
    return _mi.log_returns(close)


def sma(series: pl.Series, n: int) -> pl.Series:
    return _mi.sma(series, n)


def ema(series: pl.Series, n: int) -> pl.Series:
    return _mi.ema(series, n, profile=PROFILE)


def rsi(close: pl.Series, n: int = 14) -> pl.Series:
    return _mi.rsi(close, n, profile=PROFILE)


def atr(high: pl.Series, low: pl.Series, close: pl.Series, n: int = 14) -> pl.Series:
    return _mi.atr(high, low, close, n, profile=PROFILE)


def adx(
    high: pl.Series, low: pl.Series, close: pl.Series, n: int = 14
) -> tuple[pl.Series, pl.Series, pl.Series]:
    return _mi.adx(high, low, close, n, profile=PROFILE)


def historical_volatility(
    close: pl.Series, n: int = 20, annualization_factor: float = 365.0
) -> pl.Series:
    return _mi.historical_volatility(close, n, annualization_factor)


def volume_factor(volume: pl.Series, n: int = 20) -> pl.Series:
    return _mi.volume_factor(volume, n)


def zscore(series: pl.Series, n: int = 20) -> pl.Series:
    return _mi.zscore(series, n)


def normalized_range(close: pl.Series, n: int = 20) -> pl.Series:
    return _mi.normalized_range(close, n)


def breakout(
    close: pl.Series,
    volume: pl.Series,
    n: int = 20,
    vf_threshold: float = 1.8,
) -> tuple[pl.Series, pl.Series]:
    """Flag ``null`` statt ``False``, wenn nicht auswertbar (``bool(None)`` bleibt False)."""
    return _mi.breakout(close, volume, n, vf_threshold)
'''

HELPERS = '''

def _to_values(arr: object) -> list[float | None]:
    """numpy-Array → Werteliste; NaN ist eine Lücke (None)."""
    return [None if v != v else float(v) for v in np.asarray(arr, dtype=float).tolist()]


def _to_array(values: list[float | None]) -> np.ndarray:
    return np.array([np.nan if v is None else v for v in values], dtype=float)
'''

REPLACEMENTS = {
    "backend/app/services/scoring/rsi_macd.py": {
        "compute_rsi": '''def compute_rsi(
    closes: Sequence[float], period: int = 14
) -> float | None:
    """RSI mit Wilder-Glättung (auditcore_market_indicators, Profil krypto.scoring_rsi_macd)."""
    values = _to_values(closes)
    if len(values) < period + 1:
        return None
    return _mi.rsi(values, period, profile=_PROFILE)[-1]
''',
        "_ema": '''def _ema(arr: np.ndarray, period: int) -> np.ndarray:
    """EMA (SMA-Start, Lücken halten) aus auditcore_market_indicators."""
    return _to_array(_mi.ema(_to_values(arr), period, profile=_PROFILE))
''',
    },
    "backend/app/services/scoring/confluence.py": {
        "_ema_numpy": '''def _ema_numpy(arr: np.ndarray, n: int) -> np.ndarray:
    """EMA mit SMA-Start (auditcore_market_indicators, Profil krypto.scoring_confluence)."""
    return _to_array(_mi.ema(_to_values(arr), n, profile=_PROFILE))
''',
    },
    "backend/app/services/regime/hmm.py": {
        "_ema": '''def _ema(values: np.ndarray, span: int) -> np.ndarray:
    """EMA mit erstem Wert als Start (auditcore_market_indicators, Profil krypto.regime_hmm)."""
    return _to_array(_mi.ema(_to_values(values), span, profile=_PROFILE))
''',
        "_annualized_vol": '''def _annualized_vol(
    returns: np.ndarray, window: int = 20
) -> np.ndarray:
    """Rollierende Stichproben-Std (auditcore_market_indicators) · √365."""
    std = _mi.rolling_std(_to_values(returns), window)
    return _to_array([None if v is None else v * math.sqrt(365.0) for v in std])
''',
    },
    "backend/app/services/scoring/ma_crossover.py": {
        "_rolling_mean": '''def _rolling_mean(arr: np.ndarray, window: int) -> np.ndarray:
    """Einfacher gleitender Mittelwert aus auditcore_market_indicators."""
    return _to_array(_mi.sma(_to_values(arr), window))
''',
    },
}
PROFILES = {
    "backend/app/services/scoring/rsi_macd.py": "krypto.scoring_rsi_macd",
    "backend/app/services/scoring/confluence.py": "krypto.scoring_confluence",
    "backend/app/services/regime/hmm.py": "krypto.regime_hmm",
    "backend/app/services/scoring/ma_crossover.py": None,
}


def git_blob(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def replace_functions(source: str, functions: dict[str, str]) -> str:
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    spans = sorted(
        (
            (node.lineno - 1 - len(node.decorator_list), node.end_lineno or node.lineno, node.name)
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name in functions
        ),
        reverse=True,
    )
    if {name for *_, name in spans} != set(functions):
        raise SystemExit(f"Funktionen nicht gefunden: {set(functions)}")
    for start, end, name in spans:
        lines[start:end] = [functions[name]]
    return "".join(lines)


def add_imports(source: str, profile: str | None) -> str:
    """Imports after ``import numpy``; profile and helpers after the last import."""
    anchor = "import numpy as np\n"
    if anchor not in source:
        raise SystemExit("numpy-Import als Anker nicht gefunden")
    block = "from auditcore_market_indicators import indicators as _mi\n"
    if profile:
        block += "from auditcore_market_indicators import load_profile\n"
    source = source.replace(anchor, anchor + block, 1)
    tree = ast.parse(source)
    last = max(
        node.end_lineno or node.lineno
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
    )
    lines = source.splitlines(keepends=True)
    addition = ""
    if profile:
        addition += f'\n_PROFILE = load_profile("{profile}", "2026.09.1")\n'
    addition += HELPERS
    lines.insert(last, addition)
    return "".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("--ruff", help="ruff der krypto-Umgebung: sortiert danach die Importe")
    args = parser.parse_args()
    root = args.checkout.resolve()
    for relative, blob in PINNED.items():
        if git_blob(root / relative) != blob:
            raise SystemExit(f"{relative} ist nicht der gepinnte Stand")
    (root / "backend/app/services/indicators/base.py").write_text(BASE, encoding="utf-8")
    pipeline = root / "backend/app/services/indicators/pipeline.py"
    text = pipeline.read_text(encoding="utf-8")
    old = "vma_20 = vol.rolling_mean(window_size=20, min_samples=20)"
    if old not in text:
        raise SystemExit("pipeline.py: vma_20-Zeile nicht gefunden")
    text = text.replace(old, "vma_20 = sma(vol, 20)")
    if "    lookback: int = 60," not in text:
        raise SystemExit("pipeline.py: lookback-Vorgabe nicht gefunden")
    text = text.replace("    lookback: int = 60,", "    lookback: int = 250,", 1)
    pipeline.write_text(text, encoding="utf-8")
    for relative, call in LOOKBACK_CALLS.items():
        path = root / relative
        source = path.read_text(encoding="utf-8")
        if source.count(call) != 1:
            raise SystemExit(f"{relative}: {call} nicht eindeutig")
        path.write_text(source.replace(call, "lookback=250,"), encoding="utf-8")
    for relative, functions in REPLACEMENTS.items():
        path = root / relative
        text = add_imports(path.read_text(encoding="utf-8"), PROFILES[relative])
        path.write_text(replace_functions(text, functions), encoding="utf-8")
    requirements = root / "backend/pyproject.toml"
    text = requirements.read_text(encoding="utf-8")
    if "auditcore_market_indicators" not in text:
        text = text.replace(
            '    "polars>=1.12",',
            '    "polars>=1.21",\n    "auditcore_market_indicators[polars]==0.1.0",',
            1,
        )
        requirements.write_text(text, encoding="utf-8")
    if args.ruff:
        files = [str(root / r) for r in (*REPLACEMENTS, "backend/app/services/indicators/base.py")]
        subprocess.run([args.ruff, "check", "--fix", "--select", "I", *files], check=True)
    print(
        "krypto-Kopie umgestellt:", ", ".join(["indicators/base.py", "pipeline.py", *REPLACEMENTS])
    )


if __name__ == "__main__":
    main()
