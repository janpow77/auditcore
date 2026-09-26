"""Audit sampling: sample sizes, systematic and random selection, allocation.

Every sample-size method is named and bound to its source. The decided MUS
method is ``portal.mus_poisson`` (``recommended_mus_size``, decision of
2026-09-23); there is no implicit random state. See README.md and
docs/behavior-changes.md.
"""

from .selection import (
    MusSelection,
    draw_start,
    first_reaching,
    simple_random,
    stratified_allocation,
    systematic_mus,
)
from .sizes import (
    METHODS,
    MUS_DECISION,
    MUS_POISSON,
    MUS_Z_ATTRIBUTE,
    RECOMMENDED_MUS_METHOD,
    SRS_FLOWSTAT,
    SRS_PORTAL,
    Method,
    SamplingInputError,
    SizePlan,
    mus_size,
    recommended_mus_method,
    recommended_mus_size,
    srs_size,
)

__version__ = "0.2.3"

__all__ = [
    "METHODS",
    "MUS_DECISION",
    "MUS_POISSON",
    "MUS_Z_ATTRIBUTE",
    "SRS_FLOWSTAT",
    "SRS_PORTAL",
    "Method",
    "RECOMMENDED_MUS_METHOD",
    "MusSelection",
    "SamplingInputError",
    "SizePlan",
    "__version__",
    "draw_start",
    "first_reaching",
    "mus_size",
    "recommended_mus_method",
    "recommended_mus_size",
    "simple_random",
    "srs_size",
    "stratified_allocation",
    "systematic_mus",
]
