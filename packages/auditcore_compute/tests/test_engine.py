"""Engine selection, fallback reasons, warnings and the fastmath ban."""

from __future__ import annotations

import importlib
import logging
from collections.abc import Callable
from types import ModuleType

import numpy as np
import pytest
from conftest import requires_numba

from auditcore_compute import (
    DISABLE_ENV,
    EngineInfo,
    Kernel,
    accelerate,
    engine_info,
    engine_report,
    jitable,
    use_python,
)
from auditcore_compute import _engine as engine
from auditcore_compute.finance import share_cents
from auditcore_compute.stats import deterministic_sum


@pytest.fixture(autouse=True)
def engine_path() -> str:
    """Engine tests choose their path themselves (overrides the conftest fixture)."""
    return "engine"


def _double(values: np.ndarray, out: np.ndarray) -> None:
    for i in range(values.shape[0]):
        out[i] = 2 * values[i]


def _fresh(func: Callable[..., object] = _double, **options: bool) -> Kernel[..., object]:
    return accelerate(func, **options)


def _run(kernel: Kernel[..., object]) -> list[int]:
    out = np.zeros(3, dtype=np.int64)
    kernel(np.arange(3, dtype=np.int64), out)
    return [int(v) for v in out]


def test_fastmath_is_rejected_with_reason() -> None:
    for flag in (True, {"contract"}, "fast"):
        with pytest.raises(ValueError, match="bitgleich"):
            accelerate(_double, fastmath=flag)
    with pytest.raises(ValueError, match="fastmath"):
        accelerate(fastmath=True)


def test_decorator_forms_and_metadata() -> None:
    @accelerate(parallel=False, cache=False)
    def triple(value: int) -> int:
        """Triple."""
        return 3 * value

    assert isinstance(triple, Kernel)
    assert triple(2) == 6 and triple.__name__ == "triple" and triple.__doc__ == "Triple."
    assert triple.py_func(4) == 12
    with use_python():
        assert triple(5) == 15
    with pytest.raises(TypeError, match="accelerate"):
        engine_info(len)


def test_environment_forces_python(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv(DISABLE_ENV, "1")
    monkeypatch.setattr(engine, "_WARNED", set())
    kernel = _fresh()
    with caplog.at_level(logging.WARNING, logger="auditcore_compute"):
        assert _run(kernel) == [0, 2, 4]
        assert _run(_fresh()) == [0, 2, 4]
    info = engine_info(kernel)
    assert info.mode == "python" and DISABLE_ENV in info.reason
    assert not info.compiled and not info.parallel and not info.cache
    assert len([r for r in caplog.records if DISABLE_ENV in r.getMessage()]) == 1


def test_missing_numba_falls_back(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.delenv(DISABLE_ENV, raising=False)
    monkeypatch.setattr(engine, "_NUMBA", None)
    monkeypatch.setattr(engine, "_NUMBA_REASON", "numba ist nicht installiert (Extra [jit])")
    monkeypatch.setattr(engine, "_WARNED", set())
    kernel = _fresh(parallel=True)
    with caplog.at_level(logging.WARNING, logger="auditcore_compute"):
        assert _run(kernel) == [0, 2, 4]
    info = kernel.info()
    assert info.mode == "python" and "nicht installiert" in info.reason
    assert info.numba_version is None
    assert "reines Python" in caplog.text
    helper = jitable(_double)
    assert helper is _double


def _raise(error: BaseException) -> Callable[[str], ModuleType]:
    def fake(name: str) -> ModuleType:
        raise error

    return fake


def test_load_numba_reasons(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(DISABLE_ENV, raising=False)
    monkeypatch.setattr(importlib, "import_module", _raise(ImportError("x")))
    assert engine.load_numba() == (None, "numba ist nicht installiert (Extra [jit])")
    monkeypatch.setattr(importlib, "import_module", _raise(AttributeError("broken")))
    assert engine.load_numba() == (None, "numba nicht ladbar: AttributeError")
    monkeypatch.setattr(importlib, "import_module", lambda name: ModuleType(name))
    module, reason = engine.load_numba()
    assert module is not None and reason == "numba verfügbar"
    monkeypatch.setenv(DISABLE_ENV, "yes")
    assert engine.jit_disabled()
    assert engine.load_numba()[0] is None


def _fake_numba() -> ModuleType:
    module = ModuleType("numba")
    module.__dict__["__version__"] = "0.0-fake"

    def njit(**options: object) -> Callable[[Callable[..., object]], Callable[..., object]]:
        assert options == {"cache": False, "parallel": False, "fastmath": False}
        return lambda func: func

    module.__dict__["njit"] = njit
    return module


def _no_locator(numba: ModuleType, dispatcher: object, func: Callable[..., object]) -> None:
    raise RuntimeError("cannot cache function: no locator available")


def test_unwritable_cache_compiles_without_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(DISABLE_ENV, raising=False)
    monkeypatch.setattr(engine, "_NUMBA", _fake_numba())
    monkeypatch.setattr(engine, "attach_cache", _no_locator)
    kernel = _fresh()
    assert _run(kernel) == [0, 2, 4]
    info = kernel.info()
    assert info.mode == "jit" and not info.cache and "ohne Cache" in info.reason
    assert info.compiled and info.numba_version == "0.0-fake"
    monkeypatch.setattr(engine, "attach_cache", lambda numba, dispatcher, func: None)
    cached = _fresh()
    assert _run(cached) == [0, 2, 4] and cached.info().cache
    uncached = _fresh(cache=False)
    assert _run(uncached) == [0, 2, 4] and not uncached.info().cache


@requires_numba
def test_cache_key_contains_source_fingerprint() -> None:
    numba = importlib.import_module("numba")
    dispatcher = numba.njit(cache=False)(_divide)
    engine.attach_cache(numba, dispatcher, _divide)
    cache = dispatcher._cache
    assert type(cache).__name__ == "FingerprintFunctionCache"
    assert len(engine.SOURCE_FINGERPRINT) == 64
    key = cache._index_key((), dispatcher.targetctx.codegen())
    assert key[1] == engine.SOURCE_FINGERPRINT


def test_engine_info_as_dict() -> None:
    info = EngineInfo("k", "python", "grund", None, False, False, False)
    assert info.as_dict() == {
        "name": "k",
        "mode": "python",
        "reason": "grund",
        "numba_version": None,
        "parallel": False,
        "cache": False,
        "compiled": False,
    }


def test_engine_report_lists_package_kernels() -> None:
    names = {info.name for info in engine_report()}
    assert {"share_kernel", "interest_kernel", "moments_kernel", "duplicate_scan_kernel"} <= names


class _Plain:
    """An ordinary Python class: Numba cannot type its instances."""

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Plain)

    __hash__ = object.__hash__


def _unsupported(values: np.ndarray) -> object:
    return _Plain()


def _divide(values: np.ndarray) -> int:
    return int(values[0] // values[1])


@requires_numba
def test_compile_failure_falls_back_once(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(DISABLE_ENV, raising=False)
    kernel = accelerate(_unsupported, cache=False)
    with caplog.at_level(logging.WARNING, logger="auditcore_compute"):
        assert kernel(np.zeros(1)) == _Plain()
        assert kernel(np.zeros(1)) == _Plain()
    info = engine_info(kernel)
    assert info.mode == "python" and info.reason.startswith("Kompilierung fehlgeschlagen")
    assert len([r for r in caplog.records if "_unsupported" in r.getMessage()]) == 1


@requires_numba
def test_runtime_errors_are_not_masked() -> None:
    kernel = accelerate(_divide, cache=False)
    with pytest.raises(ZeroDivisionError):
        kernel(np.array([1, 0], dtype=np.int64))
    assert engine_info(kernel).mode == "jit"


@requires_numba
def test_package_kernels_run_compiled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(DISABLE_ENV, raising=False)
    share_cents([1, 2, 3], "0.5")
    deterministic_sum([1.0, 2.0])
    report = {info.name: info for info in engine_report()}
    for name in ("share_kernel", "sum_kernel"):
        assert report[name].mode == "jit" and report[name].compiled, report[name]
    assert not report["share_kernel"].parallel and not report["sum_kernel"].parallel
