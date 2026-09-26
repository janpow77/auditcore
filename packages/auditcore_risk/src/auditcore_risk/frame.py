"""pandas adapter (extra ``pandas``): drop-in functions for frame-based consumers.

``compute_red_flags`` returns a copy of the frame with one boolean column per
rule (``rule.column``), the profile's value columns (for example
``name_match``) and the code-list column, exactly like the riskanalysis
function it replaces. ``red_flag_summary`` recomputes the overview from those
columns, so it can run after the consumer reindexed or filtered the frame.
"""

from __future__ import annotations

import math
from datetime import date
from typing import Any

from auditcore_common.optional import require_module

from .engine import Evaluation, evaluate
from .errors import DependencyError, InputError, ProfileError
from .profiles import RiskProfile
from .summary import red_flag_entry
from .values import is_missing, strict_amount


def _pandas() -> Any:
    """The pandas module (extra ``pandas``); typed ``Any`` because it is imported lazily."""
    return require_module(
        "pandas", DependencyError, "Für DataFrames ist 'auditcore_risk[pandas]' zu installieren."
    )


def evaluate_frame(
    frame: Any, profile: RiskProfile, *, reference_date: date | None = None
) -> Evaluation:
    """:func:`auditcore_risk.evaluate` over the rows of a DataFrame (column set kept)."""
    pd = _pandas()
    if not isinstance(frame, pd.DataFrame):
        raise InputError("Ein pandas.DataFrame ist erforderlich.")
    columns = [str(c) for c in frame.columns]
    if len(set(columns)) != len(columns):
        raise InputError("Spaltennamen müssen eindeutig sein.")
    records = frame.to_dict("records")
    return evaluate(records, profile, columns=columns, reference_date=reference_date)


def annotate(frame: Any, evaluation: Evaluation, profile: RiskProfile) -> Any:
    """Copy of ``frame`` with flag, value and code columns of ``evaluation``."""
    pd = _pandas()
    if dict(evaluation.profile) != profile.reference:
        raise ProfileError("Auswertung und Profil stimmen nicht überein.")
    if len(evaluation.records) != len(frame):
        raise InputError("Auswertung und DataFrame haben unterschiedlich viele Zeilen.")
    out = frame.copy()
    for rule in profile.rules:
        if rule.scope != "record" or rule.column is None or rule.code in evaluation.skipped:
            continue
        values = [r.flags[rule.code] for r in evaluation.records]
        if any(v is None for v in values):
            out[rule.column] = pd.array(values, dtype="boolean")
        else:
            out[rule.column] = pd.Series(values, index=out.index, dtype=bool)
    for name in profile.output.get("value_columns", ()):
        out[name] = pd.Series(
            [r.values.get(name) for r in evaluation.records], index=out.index, dtype=float
        )
    codes = profile.output.get("codes_column")
    if codes:
        out[codes] = pd.Series(
            [list(r.codes) for r in evaluation.records], index=out.index, dtype=object
        )
    return out


def compute_red_flags(
    frame: Any, profile: RiskProfile, *, reference_date: date | None = None
) -> Any:
    """Evaluate and annotate in one step (riskanalysis ``compute_red_flags`` contract)."""
    evaluation = evaluate_frame(frame, profile, reference_date=reference_date)
    return annotate(frame, evaluation, profile)


def red_flag_summary(frame: Any, profile: RiskProfile) -> list[dict[str, Any]]:
    """Overview from the flag columns of an annotated frame (riskanalysis format).

    Rules whose column is absent are left out, as in the source. The volume is
    the correctly rounded sum of the profile's amount field over flagged rows.
    """
    _pandas()
    spec = profile.summary
    if spec["format"] != "riskanalysis.red_flag_summary":
        raise ProfileError(
            "Diese Zusammenfassung gilt nur für das riskanalysis-Format; "
            "sonst Evaluation.summary verwenden."
        )
    amount_field = spec["amount_field"]
    n = len(frame)
    amounts = [strict_amount(v, amount_field, None) for v in frame[amount_field].tolist()]
    out = []
    for rule in profile.rules:
        if rule.scope != "record" or rule.column is None or rule.column not in frame.columns:
            continue
        flags = [False if is_missing(v) else bool(v) for v in frame[rule.column].tolist()]
        hits = sum(flags)
        chosen = [a for a, f in zip(amounts, flags, strict=True) if f and a is not None]
        volume = math.fsum(chosen) if all(math.isfinite(a) for a in chosen) else sum(chosen)
        out.append(red_flag_entry(rule, hits, n, float(volume)))
    return out


__all__ = ["annotate", "compute_red_flags", "evaluate_frame", "red_flag_summary"]
