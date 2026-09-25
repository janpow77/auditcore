"""Standard-library numerics with explicitly documented floating-point behavior.

``numpy_pairwise_sum`` and ``numpy_round`` reproduce the results of NumPy's
``add.reduce`` on contiguous float64 data and ``numpy.round`` so that legacy
outputs of pandas/NumPy code can be replayed bit-for-bit without NumPy. The
chi-square survival function is computed from the regularized upper
incomplete gamma function (series / continued fraction).
"""

from __future__ import annotations

import math

from auditcore_common.numeric import numpy_pairwise_sum, numpy_round

#: Same objects as in ``auditcore_common.numeric`` (differentially proven there).
__all__ = ["chi2_survival", "numpy_pairwise_sum", "numpy_round", "regularized_upper_gamma"]


def regularized_upper_gamma(a: float, x: float) -> float:
    """Q(a, x) = Γ(a, x) / Γ(a) for a > 0, x ≥ 0."""
    if a <= 0 or x < 0:
        raise ValueError("Q(a, x) ist nur für a > 0 und x ≥ 0 definiert.")
    if x == 0:
        return 1.0
    log_prefix = a * math.log(x) - x - math.lgamma(a)
    if x < a + 1:
        term = 1.0 / a
        total = term
        n = a
        for _ in range(10_000):
            n += 1
            term *= x / n
            total += term
            if abs(term) < abs(total) * 1e-17:
                break
        return max(0.0, 1.0 - total * math.exp(log_prefix))
    tiny = 1e-300
    b = x + 1 - a
    c = 1 / tiny
    d = 1 / b
    h = d
    for i in range(1, 10_000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-17:
            break
    return math.exp(log_prefix) * h


def chi2_survival(statistic: float, degrees_of_freedom: int) -> float:
    """P(X ≥ statistic) for a chi-square distribution."""
    if degrees_of_freedom < 1:
        raise ValueError("Die Freiheitsgrade müssen mindestens 1 betragen.")
    if statistic != statistic:
        return statistic
    if statistic <= 0:
        return 1.0
    return regularized_upper_gamma(degrees_of_freedom / 2.0, statistic / 2.0)
