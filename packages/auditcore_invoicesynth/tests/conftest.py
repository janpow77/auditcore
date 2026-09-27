from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from auditcore_invoicesynth.fonts import FontSet, discover_fonts
from auditcore_invoicesynth.plan import SynthConfig

SMALL = {"train": 12, "validation": 2, "test_synthetic": 2, "test_layout_holdout": 4}


@pytest.fixture(scope="session")
def fonts() -> FontSet:
    found = discover_fonts()
    assert found.families, "Keine freie Katalogschrift (fonts-dejavu-core) installiert"
    return found


@pytest.fixture(scope="session")
def small_config() -> SynthConfig:
    return SynthConfig(seed=7, counts=dict(SMALL), dpi_choices=(72, 96))


@pytest.fixture(scope="session")
def small_dataset(
    tmp_path_factory: pytest.TempPathFactory, small_config: SynthConfig, fonts: FontSet
) -> tuple[Path, dict[str, Any]]:
    from auditcore_invoicesynth import build_dataset

    out = tmp_path_factory.mktemp("ds") / "a"
    return out, build_dataset(small_config, out, fonts)


TORCH_STACK = frozenset({"torch", "transformers", "tokenizers"})


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark tests that need the torch stack as ``gpu`` (select with ``-m gpu``).

    They are CPU smoke tests (``cpu_smoke``) and still run without CUDA; they skip
    themselves via ``importorskip`` when torch is not installed.
    """
    for item in items:
        function = getattr(item, "function", None)
        constants = set(getattr(getattr(function, "__code__", None), "co_consts", ()))
        if constants & TORCH_STACK:
            item.add_marker(pytest.mark.gpu)
