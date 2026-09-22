"""Audit sampling: sample sizes, systematic and random selection, allocation.

Every sample-size method is named and bound to its source; there is no
default method and no implicit random state. See README.md and
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
    MUS_POISSON,
    MUS_Z_ATTRIBUTE,
    SRS_FLOWSTAT,
    SRS_PORTAL,
    Method,
    SamplingInputError,
    SizePlan,
    mus_size,
    srs_size,
)

__version__ = "0.1.0"

__all__ = [
    "METHODS",
    "MUS_POISSON",
    "MUS_Z_ATTRIBUTE",
    "SRS_FLOWSTAT",
    "SRS_PORTAL",
    "Method",
    "MusSelection",
    "SamplingInputError",
    "SizePlan",
    "__version__",
    "draw_start",
    "first_reaching",
    "mus_size",
    "simple_random",
    "srs_size",
    "stratified_allocation",
    "systematic_mus",
]
