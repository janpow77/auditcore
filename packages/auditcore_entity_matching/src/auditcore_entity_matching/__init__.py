"""Transparent entity normalisation, LEI checks and fuzzy match components."""

from .errors import DependencyError, EntityMatchingError, ProfileError
from .lei import LeiCheck, check_lei, extract_lei, is_lei_format, lei_check_digits, lei_checksum_ok
from .matching import Candidate, MatchResult, best_match, classify
from .normalize import normalize
from .profiles import Profile, available_profiles, load_profile

__version__ = "0.1.0"

__all__ = [
    "Candidate",
    "DependencyError",
    "EntityMatchingError",
    "LeiCheck",
    "MatchResult",
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
]
