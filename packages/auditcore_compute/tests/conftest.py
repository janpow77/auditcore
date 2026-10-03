"""Shared fixtures: run a call through the compiled and through the Python path."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import TypeVar

import numpy as np
import pytest
from hypothesis import HealthCheck, settings

from auditcore_compute import _engine, use_python

T = TypeVar("T")

# The first example of a kernel includes its JIT compilation; no per-example deadline.
# The autouse engine fixture only switches a context variable for the whole test.
settings.register_profile(
    "compute", deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
settings.load_profile("compute")


@pytest.fixture(autouse=True, params=["engine", "python"])
def engine_path(request: pytest.FixtureRequest) -> Iterator[str]:
    """Run every test once with the configured engine and once forced to Python."""
    if request.param == "python":
        with use_python():
            yield request.param
    else:
        yield request.param


#: Numba loaded at import (installed and not disabled by AUDITCORE_COMPUTE_DISABLE_JIT).
HAS_NUMBA = _engine._NUMBA is not None
requires_numba = pytest.mark.skipif(
    not HAS_NUMBA, reason="numba nicht installiert (Extra [jit]) oder abgeschaltet"
)


def both_paths(call: Callable[[], T]) -> tuple[T, T]:
    """Result of ``call`` with the engine as configured and forced to Python."""
    compiled = call()
    with use_python():
        python = call()
    return compiled, python


def bits(array: object) -> bytes:
    """Bitwise representation (float -0.0 and 0.0 differ)."""
    data = np.ascontiguousarray(np.asarray(array))
    return data.dtype.str.encode() + data.tobytes()
