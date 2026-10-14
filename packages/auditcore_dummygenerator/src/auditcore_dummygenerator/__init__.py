"""Synthetic test data generation without application or platform dependencies."""

from auditcore_dummygenerator.company_names import (
    ENTITY_FORMS,
    company_name_at,
    company_name_count,
    draw_company_name,
)
from auditcore_dummygenerator.generator import (
    JOBLIB_AVAILABLE,
    BatchGenerationError,
    TestDataGenerator,
    get_optimal_workers,
)
from auditcore_dummygenerator.profiles import list_profiles, profile_reference

__version__ = "0.2.0"

__all__ = [
    "ENTITY_FORMS",
    "JOBLIB_AVAILABLE",
    "BatchGenerationError",
    "TestDataGenerator",
    "company_name_at",
    "company_name_count",
    "draw_company_name",
    "get_optimal_workers",
    "list_profiles",
    "profile_reference",
]
