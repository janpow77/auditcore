"""Projection of sample errors and error rates for audit authorities.

Projected error, precision and upper limit of error for the sampling methods
of the Commission guidance EGESIF_16-0014-01 (simple random sampling with
mean-per-unit and ratio estimation, difference estimation, monetary unit
sampling – standard, stratified and conservative – and non-statistical
sampling), samples in several periods of the year, two- and three-stage
sampling (sub-samples within units, also for ETC programmes), the total error
rate (TER) with systemic and anomalous errors, the recalculation of the
confidence level, groups of programmes, attribute sampling for tests of
controls and, strictly separate, the residual error rate (RER) after financial
corrections along the template CPRE_23-0013-01 Annex 3. See README.md.
"""

from .attributes import AttributeEvaluation, evaluate_attributes
from .confidence import (
    SYSTEM_ASSESSMENT_LEVELS,
    ConfidenceRecalculation,
    recalculate_confidence,
    recalculated_level,
    system_confidence_level,
)
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
from .exclusion import extension_factor
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
from .groups import Group, GroupResult, GroupsAssessment, assess_groups
from .methods import METHODS, Method, project
from .mus import mus_precision, tainting_projection
from .periods import Period, assess_periods, combined_precision, project_periods
from .projection import Projection, StratumResult
from .residual import ResidualErrorRate, ResidualInputs, residual_error_rate, residual_from_total
from .sources import Step
from .subsampling import (
    SUBSAMPLE_ESTIMATORS,
    SubSample,
    SubSampleResult,
    project_subsample,
    unit_from_subsample,
)
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
    "SUBSAMPLE_ESTIMATORS",
    "SYSTEM_ASSESSMENT_LEVELS",
    "Allowance",
    "Assessment",
    "AttributeEvaluation",
    "ConfidenceRecalculation",
    "DifferenceFigures",
    "ErrorClasses",
    "EstimatorCheck",
    "ExtrapolationInputError",
    "FactorProfile",
    "Group",
    "GroupResult",
    "GroupsAssessment",
    "Method",
    "Period",
    "Projection",
    "ResidualErrorRate",
    "ResidualInputs",
    "SampleUnit",
    "Step",
    "Stratum",
    "StratumResult",
    "SubSample",
    "SubSampleResult",
    "TopStratum",
    "TotalErrorRate",
    "__version__",
    "assess",
    "assess_groups",
    "assess_periods",
    "basic_reliability_factor",
    "combined_precision",
    "conclude",
    "estimator_check",
    "evaluate",
    "evaluate_attributes",
    "extension_factor",
    "incremental_allowances",
    "mean_per_unit_error",
    "mus_precision",
    "poisson_factor",
    "precision",
    "project",
    "project_periods",
    "project_subsample",
    "ratio_error",
    "ratio_q_values",
    "recalculate_confidence",
    "recalculated_level",
    "reliability_factor",
    "residual_error_rate",
    "residual_from_total",
    "split_top_stratum",
    "split_top_stratum_for_plan",
    "stratified_precision",
    "system_confidence_level",
    "tainting_projection",
    "unit_from_subsample",
    "z_value",
]
