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
