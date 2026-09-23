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
    identifier_missing,
    missing_columns,
    name_similarity,
)
from .errors import DependencyError, InputError, ProfileError, RiskError
from .profiles import RiskProfile, Rule, available_profiles, load_profile, profile_from_dict
from .rules import KINDS

__version__ = "0.1.0"

__all__ = [
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
    "identifier_missing",
    "load_profile",
    "missing_columns",
    "name_similarity",
    "profile_from_dict",
]
