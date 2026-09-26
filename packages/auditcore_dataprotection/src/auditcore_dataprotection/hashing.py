"""Canonical JSON digests that bind results to exact profile and register content.

Veraltet: die Funktion liegt in ``auditcore_common.hashing``.
"""

from __future__ import annotations

import warnings
from collections.abc import Mapping

from auditcore_common import hashing as _common


def canonical_sha256(data: Mapping[str, object]) -> str:
    """Veraltet: :func:`auditcore_common.hashing.canonical_sha256` (gleiches Ergebnis)."""
    warnings.warn(
        "auditcore_dataprotection.hashing.canonical_sha256 ist veraltet; "
        "auditcore_common.hashing.canonical_sha256 verwenden.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _common.canonical_sha256(data)
