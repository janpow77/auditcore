"""auditcore_privacy: Deterministische, kollisionsfreie Pseudonymisierung und Maskierung."""

from .engine import PseudonymEngine, compute_original_hash, generate_salt
from .errors import CollisionError, PrivacyError, ScopeError
from .generators import is_valid_iban
from .mapping import MappingStore
from .masking import mask_text
from .models import (
    EntityType,
    MappingExport,
    PseudonymMapping,
    ReplacementKind,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "PrivacyError",
    "ScopeError",
    "CollisionError",
    "EntityType",
    "ReplacementKind",
    "PseudonymMapping",
    "MappingExport",
    "PseudonymEngine",
    "compute_original_hash",
    "generate_salt",
    "MappingStore",
    "mask_text",
    "is_valid_iban",
]
