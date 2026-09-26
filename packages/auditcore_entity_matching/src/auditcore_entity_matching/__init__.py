"""Transparent entity normalisation, LEI checks and fuzzy match components."""

from .errors import DependencyError, EntityMatchingError, ProfileError
from .lei import LeiCheck, check_lei, extract_lei, is_lei_format, lei_check_digits, lei_checksum_ok
from .matching import PAIR_SCORERS, Candidate, MatchResult, best_match, classify, pair_score
from .normalize import normalize
from .profiles import Profile, available_profiles, load_profile, recommended_profile

__version__ = "0.2.3"

__all__ = [
    "Candidate",
    "DependencyError",
    "EntityMatchingError",
    "LeiCheck",
    "MatchResult",
    "PAIR_SCORERS",
    "Profile",
    "ProfileError",
    "__version__",
    "available_profiles",
    "best_match",
    "check_lei",
    "classify",
    "extract_lei",
    "is_lei_format",
    "lei_check_digits",
    "lei_checksum_ok",
    "load_profile",
    "normalize",
    "pair_score",
    "recommended_profile",
]
