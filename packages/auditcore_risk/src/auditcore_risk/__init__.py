"""Risk flags from explicit, versioned, source-bound rule profiles.

The mechanics evaluate exactly one explicitly selected profile. Legacy
profiles reproduce their source applications; nothing here combines profiles
into a common score or changes weights and thresholds. Pandas is only needed
for :mod:`auditcore_risk.frame` (extra ``pandas``), rapidfuzz for name
matching (extra ``fuzzy``), year-bound procurement thresholds come from
``auditcore_procurement`` (extra ``procurement``).
"""

from .engine import (
    DatasetFinding,
    Evaluation,
    FlagHit,
    RecordResult,
    evaluate,
    flatten_record,
    identifier_missing,
    missing_columns,
    name_similarity,
)
from .errors import DependencyError, InputError, ProfileError, RiskError
from .fraud import (
    DuplicateMatch,
    FraudProfile,
    SignalAssessment,
    TedAssessment,
    assess_contractor,
    available_fraud_profiles,
    find_duplicates,
    load_fraud_profile,
    score_signals,
    select_contracts,
)
from .profiles import RiskProfile, Rule, available_profiles, load_profile, profile_from_dict
from .rules import KINDS

__version__ = "0.3.2"

__all__ = [
    "DuplicateMatch",
    "FraudProfile",
    "SignalAssessment",
    "TedAssessment",
    "assess_contractor",
    "available_fraud_profiles",
    "find_duplicates",
    "load_fraud_profile",
    "score_signals",
    "select_contracts",
    "KINDS",
    "DatasetFinding",
    "DependencyError",
    "Evaluation",
    "FlagHit",
    "InputError",
    "ProfileError",
    "RecordResult",
    "RiskError",
    "RiskProfile",
    "Rule",
    "__version__",
    "available_profiles",
    "evaluate",
    "flatten_record",
    "identifier_missing",
    "load_profile",
    "missing_columns",
    "name_similarity",
    "profile_from_dict",
]
