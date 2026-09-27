"""Sample sizes after the Commission guidance EGESIF_16-0014-01 (status „nach Leitfaden“).

Clearly separate from the characterized legacy methods of
:mod:`auditcore_sampling.sizes`: every function here implements a formula of
the guidance (sections 6.1–6.4) or a legal minimum of the regulation, names
its source in each derivation step and carries the status
``GUIDANCE_EGESIF_16_0014_01``. Nothing is chosen silently: the method, the
factor profile (``kom_2017_tables`` or ``exact``) and the confidence level are
always explicit. Evaluation of the audited sample is ``auditcore_extrapolation``.
"""

from .equal_probability import (
    DIFFERENCE,
    SRS,
    equal_probability_size,
    stratified_equal_probability_size,
)
from .factors import (
    EF_TABLE,
    EXACT,
    FACTOR_PROFILES,
    KOM_TABLES,
    RF_TABLE,
    Z_TABLE,
    FactorProfile,
    expansion_factor,
    reliability_factor,
    z_value,
)
from .mus import (
    MUS_CONSERVATIVE,
    MUS_STANDARD,
    MUS_STRATIFIED,
    HighValueSplit,
    high_value_split,
    mus_conservative_size,
    mus_standard_size,
    mus_stratified_size,
)
from .nonstatistical import (
    NONSTATISTICAL,
    RULES,
    TABLE_6,
    CoverageBand,
    NonStatisticalRule,
    nonstatistical_minimum,
)
from .pilot import error_rate_sd, error_rates, error_sd
from .plan import MATERIALITY_RATE, GuidancePlan, StratumAllocation, StratumInput
from .sources import GUIDANCE, GUIDANCE_ID, GUIDANCE_STATUS, GUIDANCE_STATUS_LABEL, Step

__all__ = [
    "DIFFERENCE",
    "EF_TABLE",
    "EXACT",
    "FACTOR_PROFILES",
    "GUIDANCE",
    "GUIDANCE_ID",
    "GUIDANCE_STATUS",
    "GUIDANCE_STATUS_LABEL",
    "KOM_TABLES",
    "MATERIALITY_RATE",
    "MUS_CONSERVATIVE",
    "MUS_STANDARD",
    "MUS_STRATIFIED",
    "NONSTATISTICAL",
    "RF_TABLE",
    "RULES",
    "SRS",
    "TABLE_6",
    "Z_TABLE",
    "CoverageBand",
    "FactorProfile",
    "GuidancePlan",
    "HighValueSplit",
    "NonStatisticalRule",
    "Step",
    "StratumAllocation",
    "StratumInput",
    "equal_probability_size",
    "error_rate_sd",
    "error_rates",
    "error_sd",
    "expansion_factor",
    "high_value_split",
    "mus_conservative_size",
    "mus_standard_size",
    "mus_stratified_size",
    "nonstatistical_minimum",
    "reliability_factor",
    "stratified_equal_probability_size",
    "z_value",
]
