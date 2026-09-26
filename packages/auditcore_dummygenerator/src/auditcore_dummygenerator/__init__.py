"""Synthetic test data generation without application or platform dependencies."""

from auditcore_dummygenerator.generator import (
    JOBLIB_AVAILABLE,
    BatchGenerationError,
    TestDataGenerator,
    get_optimal_workers,
)
from auditcore_dummygenerator.profiles import list_profiles, profile_reference

__version__ = "0.1.3"

__all__ = [
    "JOBLIB_AVAILABLE",
    "BatchGenerationError",
    "TestDataGenerator",
    "get_optimal_workers",
    "list_profiles",
    "profile_reference",
]
