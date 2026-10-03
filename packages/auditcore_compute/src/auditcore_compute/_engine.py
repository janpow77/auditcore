"""Optional Numba compilation with observable NumPy or Python execution.

``accelerate`` wraps a kernel. On its first call the kernel is compiled with
Numba (``njit``, ``fastmath`` off) when Numba is installed and not disabled;
otherwise, or when compilation fails, a supplied NumPy fallback or the
original Python function runs. Each fallback is logged once and queryable through
``engine_info`` so that consumers can record the path in their provenance.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib
import logging
import os
import threading
from collections.abc import Callable, Iterator
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Generic, Literal, ParamSpec, TypeVar, cast, overload

P = ParamSpec("P")
R = TypeVar("R")
F = TypeVar("F", bound=Callable[..., object])

DISABLE_ENV = "AUDITCORE_COMPUTE_DISABLE_JIT"
LOGGER = logging.getLogger("auditcore_compute")
Mode = Literal["jit", "python", "numpy"]

_FORCE_PYTHON: ContextVar[bool] = ContextVar("auditcore_compute_force_python", default=False)
_REGISTRY: list[Kernel[..., object]] = []
_WARNED: set[str] = set()
_WARNED_LOCK = threading.Lock()


@dataclass(frozen=True)
class EngineInfo:
    """Execution path of one kernel, for logs and provenance records."""

    name: str
    mode: Mode
    reason: str
    numba_version: str | None
    parallel: bool
    cache: bool
    compiled: bool

    def as_dict(self) -> dict[str, object]:
        """Plain dictionary for JSON provenance."""
        return {
            "name": self.name,
            "mode": self.mode,
            "reason": self.reason,
            "numba_version": self.numba_version,
            "parallel": self.parallel,
            "cache": self.cache,
            "compiled": self.compiled,
        }


def jit_disabled() -> bool:
    """True when the environment disables JIT (NumPy or Python remains available)."""
    return os.environ.get(DISABLE_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def load_numba() -> tuple[ModuleType | None, str]:
    """Import Numba if possible; return the module (or None) and the reason."""
    if jit_disabled():
        return None, f"durch {DISABLE_ENV} abgeschaltet"
    try:
        module = importlib.import_module("numba")
    except ImportError:
        return None, "numba ist nicht installiert (Extra [jit])"
    except Exception as error:  # a broken install must not stop the library
        return None, f"numba nicht ladbar: {type(error).__name__}"
    return module, "numba verfügbar"


_NUMBA, _NUMBA_REASON = load_numba()
#: Hash of all package modules; part of every on-disk cache key.
SOURCE_FINGERPRINT = hashlib.sha256(
    b"".join(path.read_bytes() for path in sorted(Path(__file__).parent.glob("*.py")))
).hexdigest()
#: ``numba.prange`` for element-wise loops; plain ``range`` without Numba.
prange: Callable[..., range] = cast(Callable[..., range], _NUMBA.prange) if _NUMBA else range


def jitable(func: F) -> F:
    """Mark a helper callable from kernels; it stays a plain Python function."""
    if _NUMBA is not None:
        extending = importlib.import_module("numba.extending")
        return cast(F, extending.register_jitable(func))
    return func


@contextlib.contextmanager
def use_python() -> Iterator[None]:
    """Run every kernel as plain Python inside the block (e.g. for a cross-check)."""
    token = _FORCE_PYTHON.set(True)
    try:
        yield
    finally:
        _FORCE_PYTHON.reset(token)


class Kernel(Generic[P, R]):
    """A function compiled on first use, with the original kept as ``py_func``."""

    def __init__(
        self,
        func: Callable[P, R],
        *,
        parallel: bool,
        cache: bool,
        fallback: Callable[P, R] | None = None,
        min_parallel_size: int = 0,
        min_jit_size: int = 0,
    ) -> None:
        self.py_func = func
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__
        self.parallel = parallel
        self.cache_requested = cache
        self._lock = threading.Lock()
        self._compiled: Callable[P, R] | None = None
        self._resolved = False
        self._mode: Mode = "python"
        self._reason = "noch nicht aufgerufen"
        self._cache = False
        self._ran_jit = False
        self._fallback = fallback
        self._min_parallel_size = min_parallel_size
        self._min_jit_size = min_jit_size
        self._last_numpy = False
        self._serial = (
            Kernel(func, parallel=False, cache=cache, fallback=fallback)
            if parallel and min_parallel_size
            else None
        )
        self._last_serial = False

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        if _FORCE_PYTHON.get():
            return self.py_func(*args, **kwargs)
        size = getattr(args[0], "size", None) if args else None
        numpy = size is not None and size < self._min_jit_size and self._fallback is not None
        self._last_numpy = numpy
        if numpy and self._fallback is not None:
            return self._fallback(*args, **kwargs)
        serial = bool(
            self._serial is not None and size is not None and size < self._min_parallel_size
        )
        self._last_serial = serial
        if serial and self._serial is not None:
            return self._serial(*args, **kwargs)
        compiled = self._dispatcher()
        if compiled is None:
            return (self._fallback or self.py_func)(*args, **kwargs)
        try:
            result = compiled(*args, **kwargs)
        except Exception as error:
            if not _is_numba_error(error):
                raise
            self._fall_back(f"Kompilierung fehlgeschlagen: {type(error).__name__}", per_kernel=True)
            return (self._fallback or self.py_func)(*args, **kwargs)
        self._ran_jit = True
        return result

    def _dispatcher(self) -> Callable[P, R] | None:
        with self._lock:
            if not self._resolved:
                self._resolve()
            return self._compiled

    def _resolve(self) -> None:
        self._resolved = True
        numba, reason = (_NUMBA, _NUMBA_REASON) if not jit_disabled() else load_numba()
        if numba is None:
            self._fall_back(reason)
            return
        options = {"cache": False, "parallel": self.parallel, "fastmath": False}
        dispatcher = numba.njit(**options)(self.py_func)
        self._compiled = cast(Callable[P, R], dispatcher)
        self._mode = "jit"
        self._reason = "numba njit"
        if not self.cache_requested:
            return
        try:
            attach_cache(numba, dispatcher, self.py_func)
            self._cache = True
        except (RuntimeError, ImportError, AttributeError, OSError):
            # Numba refuses a cache without a writable directory (read-only
            # container image); compile without the on-disk cache instead.
            self._reason = "numba njit ohne Cache (Cache-Verzeichnis nicht beschreibbar)"

    def _fall_back(self, reason: str, *, per_kernel: bool = False) -> None:
        self._compiled = None
        self._mode = "numpy" if self._fallback is not None else "python"
        self._reason = reason
        key = f"{self.__name__}: {reason}" if per_kernel else reason
        _warn_once(f"{self._mode}: {key}", self.__name__, self._mode)

    def info(self) -> EngineInfo:
        """Current execution path (resolves the engine, does not compile)."""
        if self._last_numpy:
            return EngineInfo(
                self.__name__,
                "numpy",
                f"NumPy für weniger als {self._min_jit_size} Werte",
                str(_NUMBA.__version__) if _NUMBA is not None else None,
                False,
                False,
                False,
            )
        if self._last_serial and self._serial is not None:
            return self._serial.info()
        self._dispatcher()
        return EngineInfo(
            name=self.__name__,
            mode=self._mode,
            reason=self._reason,
            numba_version=str(_NUMBA.__version__) if _NUMBA is not None else None,
            parallel=self.parallel and self._mode == "jit",
            cache=self._cache and self._mode == "jit",
            compiled=self._ran_jit,
        )


def attach_cache(numba: ModuleType, dispatcher: object, func: Callable[..., object]) -> None:
    """Give a dispatcher Numba's on-disk cache, keyed additionally by SOURCE_FINGERPRINT.

    Numba only checks the file of the kernel itself; a changed ``@jitable``
    helper in another module would otherwise reuse stale machine code.
    """
    caching = importlib.import_module(f"{numba.__name__}.core.caching")
    base = caching.FunctionCache

    options = str(getattr(dispatcher, "targetoptions", {}))

    def index_key(cache: object, signature: object, codegen: object) -> tuple[object, str, str]:
        """Numba's key (signature, target, bytecode) plus the package fingerprint."""
        return base._index_key(cache, signature, codegen), SOURCE_FINGERPRINT, options

    fingerprinted = type("FingerprintFunctionCache", (base,), {"_index_key": index_key})
    setattr(dispatcher, "_cache", fingerprinted(func))  # noqa: B010 - Numba's private slot


def _warn_once(key: str, name: str, mode: Mode) -> None:
    """Log each fallback cause once per process (never silently)."""
    with _WARNED_LOCK:
        if key in _WARNED:
            return
        _WARNED.add(key)
    path = "NumPy" if mode == "numpy" else "reines Python"
    LOGGER.warning("auditcore_compute: %s statt JIT ab Kernel %s (%s).", path, name, key)


def _is_numba_error(error: Exception) -> bool:
    """Compilation errors of Numba (typing, lowering, unsupported features)."""
    return any(cls.__name__ == "NumbaError" for cls in type(error).__mro__)


@overload
def accelerate(
    func: Callable[P, R],
    *,
    parallel: bool = ...,
    cache: bool = ...,
    fastmath: object = ...,
    fallback: Callable[P, R] | None = ...,
    min_parallel_size: int = ...,
    min_jit_size: int = ...,
) -> Kernel[P, R]:
    """Compile a kernel with Numba when available, else run it as Python."""


@overload
def accelerate(
    func: None = None,
    *,
    parallel: bool = ...,
    cache: bool = ...,
    fastmath: object = ...,
    fallback: None = ...,
    min_parallel_size: int = ...,
    min_jit_size: int = ...,
) -> Callable[[Callable[P, R]], Kernel[P, R]]:
    """Decorator factory form: ``@accelerate(parallel=True)``."""


@overload
def accelerate(
    func: None = None,
    *,
    parallel: bool = ...,
    cache: bool = ...,
    fastmath: object = ...,
    fallback: Callable[P, R],
    min_parallel_size: int = ...,
    min_jit_size: int = ...,
) -> Callable[[Callable[P, R]], Kernel[P, R]]:
    """Decorator factory with a NumPy fallback of the same signature."""


def accelerate(
    func: Callable[P, R] | None = None,
    *,
    parallel: bool = False,
    cache: bool = True,
    fastmath: object = False,
    fallback: Callable[P, R] | None = None,
    min_parallel_size: int = 0,
    min_jit_size: int = 0,
) -> Kernel[P, R] | Callable[[Callable[P, R]], Kernel[P, R]]:
    """Compile a kernel with Numba, with observable NumPy or Python alternatives.

    ``fastmath`` is rejected: it allows reassociation and FMA contraction, so
    results would no longer be bit-identical between runs, machines and the
    Python path. ``parallel`` is meant for element-wise loops over ``prange``
    only; reductions (sums, means) must stay sequential.
    ``fallback`` must have the same signature and semantics as the kernel.
    Size thresholds inspect the first positional array argument: below
    ``min_jit_size`` use NumPy; below ``min_parallel_size`` use serial JIT.
    """
    if fastmath:
        raise ValueError(
            "fastmath ist in auditcore_compute verboten: Prüfergebnisse müssen bitgleich "
            "reproduzierbar sein (keine Umordnung von Gleitkomma-Operationen)."
        )
    for name, value in (("min_parallel_size", min_parallel_size), ("min_jit_size", min_jit_size)):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} muss eine ganze Zahl sein.")
        if value < 0:
            raise ValueError(f"{name} darf nicht negativ sein.")
    if min_jit_size and fallback is None:
        raise ValueError("min_jit_size benötigt einen NumPy-Rückfallpfad.")

    def wrap(target: Callable[P, R]) -> Kernel[P, R]:
        """Register the kernel so that ``engine_report`` lists it."""
        kernel = Kernel(
            target,
            parallel=parallel,
            cache=cache,
            fallback=fallback,
            min_parallel_size=min_parallel_size,
            min_jit_size=min_jit_size,
        )
        _REGISTRY.append(cast("Kernel[..., object]", kernel))
        return kernel

    return wrap(func) if func is not None else wrap


def engine_info(func: object) -> EngineInfo:
    """Execution path (``"jit"``, ``"numpy"`` or ``"python"``) of an accelerated kernel."""
    if not isinstance(func, Kernel):
        raise TypeError("engine_info erwartet eine mit @accelerate dekorierte Funktion.")
    return func.info()


def engine_report() -> tuple[EngineInfo, ...]:
    """Execution paths of all kernels defined so far (for provenance records)."""
    return tuple(kernel.info() for kernel in _REGISTRY)
