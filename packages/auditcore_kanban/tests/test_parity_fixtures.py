"""The committed parity fixtures equal a fresh generation (TS reads the same files)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from conftest import FIXTURES

TOOL = Path(__file__).resolve().parents[1] / "tools" / "build_parity_fixtures.py"


def _builder():  # type: ignore[no-untyped-def]
    if not TOOL.is_file():
        pytest.skip("tools/ not shipped with this checkout")
    spec = importlib.util.spec_from_file_location("build_parity_fixtures", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("name", ["rank", "transitions", "wip", "filter", "deadline",
                                  "permissions", "validation", "commands", "group"])
def test_fixture_is_current(name: str) -> None:
    builder = _builder()
    stored = (FIXTURES / "parity" / f"{name}.json").read_text(encoding="utf-8")
    assert builder.render(name) == stored


def test_fixture_format() -> None:
    for path in (FIXTURES / "parity").glob("*.json"):
        cases = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(cases, list) and cases
        assert all(set(c) == {"name", "input", "expected"} for c in cases), path.name
        assert len({c["name"] for c in cases}) == len(cases), path.name
