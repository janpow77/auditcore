"""Projection of sample errors and error rates for audit authorities.

Projected error, precision and upper limit of error for the sampling methods
of the Commission guidance EGESIF_16-0014-01 (simple random sampling with
mean-per-unit and ratio estimation, difference estimation, monetary unit
sampling – standard, stratified and conservative – and non-statistical
sampling), the total error rate (TER) with systemic and anomalous errors and,
strictly separate, the residual error rate (RER) after financial corrections
along the template CPRE_23-0013-01 Annex 3. See README.md.
"""

from .conservative import Allowance, incremental_allowances
from .design import Stratum, TopStratum, split_top_stratum, split_top_stratum_for_plan
from .equal_probability import (
    EstimatorCheck,
    estimator_check,
    mean_per_unit_error,
    precision,
    ratio_error,
    ratio_q_values,
    stratified_precision,
)
from .errors import ExtrapolationInputError
from .evaluation import (
    INCONCLUSIVE,
    MATERIAL,
    MATERIALITY_RATE,
    NOT_MATERIAL,
    Assessment,
    DifferenceFigures,
    TotalErrorRate,
    assess,
    conclude,
    evaluate,
)
from .factors import (
    EXACT,
    KOM_TABLES,
    PROFILES,
    RECOMMENDED_PROFILE,
    FactorProfile,
    basic_reliability_factor,
    poisson_factor,
    reliability_factor,
    z_value,
)
from .methods import METHODS, Method, project
from .mus import mus_precision, tainting_projection
from .projection import Projection, StratumResult
from .residual import ResidualErrorRate, ResidualInputs, residual_error_rate, residual_from_total
from .sources import Step
from .units import ErrorClasses, SampleUnit

__version__ = "0.1.0"

__all__ = [
    "EXACT",
    "INCONCLUSIVE",
    "KOM_TABLES",
    "MATERIAL",
    "MATERIALITY_RATE",
    "METHODS",
    "NOT_MATERIAL",
    "PROFILES",
    "RECOMMENDED_PROFILE",
    "Allowance",
    "Assessment",
    "DifferenceFigures",
    "ErrorClasses",
    "EstimatorCheck",
    "ExtrapolationInputError",
    "FactorProfile",
    "Method",
    "Projection",
    "ResidualErrorRate",
    "ResidualInputs",
    "SampleUnit",
    "Step",
    "Stratum",
    "StratumResult",
    "TopStratum",
    "TotalErrorRate",
    "__version__",
    "assess",
    "basic_reliability_factor",
    "conclude",
    "estimator_check",
    "evaluate",
    "incremental_allowances",
    "mean_per_unit_error",
    "mus_precision",
    "poisson_factor",
    "precision",
    "project",
    "ratio_error",
    "ratio_q_values",
    "reliability_factor",
    "residual_error_rate",
    "residual_from_total",
    "split_top_stratum",
    "split_top_stratum_for_plan",
    "stratified_precision",
    "tainting_projection",
    "z_value",
]
