"""Deterministic numeric kernels for audit data with optional Numba compilation.

``accelerate`` compiles a kernel with Numba when the ``[jit]`` extra is
installed and falls back to the identical Python function otherwise (logged
once, queryable via ``engine_info``). Money is handled in integer cents,
statistics in float64 with sequential compensated sums; both engines produce
bit-identical results.
"""

from __future__ import annotations

from ._buffers import MaskedBuffer, from_cents, to_buffer, to_cents, to_cents_buffer, to_days
from ._engine import (
    DISABLE_ENV,
    EngineInfo,
    Kernel,
    accelerate,
    engine_info,
    engine_report,
    jitable,
    prange,
    use_python,
)

__version__ = "0.1.0"

__all__ = [
    "DISABLE_ENV",
    "EngineInfo",
    "Kernel",
    "MaskedBuffer",
    "accelerate",
    "engine_info",
    "engine_report",
    "from_cents",
    "jitable",
    "prange",
    "to_buffer",
    "to_cents",
    "to_cents_buffer",
    "to_days",
    "use_python",
]
