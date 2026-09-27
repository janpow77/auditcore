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

from .attribute_variants import (
    SequentialEvaluation,
    evaluate_discovery,
    evaluate_stop_or_go,
    upper_deviation_limit,
)
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
from .groups import (
    Group,
    GroupResult,
    GroupsAssessment,
    assess_groups,
    assess_groups_over_periods,
)
from .methods import METHODS, Method, project
from .mus import mus_precision, tainting_projection
from .negative import (
    DeclaredUnit,
    NegativeCheck,
    NegativeReview,
    PopulationSplit,
    review_negative_units,
    split_population,
)
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
    "DeclaredUnit",
    "DifferenceFigures",
    "ErrorClasses",
    "EstimatorCheck",
    "ExtrapolationInputError",
    "FactorProfile",
    "Group",
    "GroupResult",
    "GroupsAssessment",
    "Method",
    "NegativeCheck",
    "NegativeReview",
    "Period",
    "PopulationSplit",
    "Projection",
    "ResidualErrorRate",
    "ResidualInputs",
    "SampleUnit",
    "SequentialEvaluation",
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
    "assess_groups_over_periods",
    "assess_periods",
    "basic_reliability_factor",
    "combined_precision",
    "conclude",
    "estimator_check",
    "evaluate",
    "evaluate_attributes",
    "evaluate_discovery",
    "evaluate_stop_or_go",
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
    "review_negative_units",
    "split_population",
    "split_top_stratum",
    "split_top_stratum_for_plan",
    "stratified_precision",
    "system_confidence_level",
    "tainting_projection",
    "unit_from_subsample",
    "upper_deviation_limit",
    "z_value",
]
