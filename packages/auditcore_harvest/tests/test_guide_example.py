"""The executable example of the adapter guide runs and passes the contract suite."""

from __future__ import annotations

import runpy
from pathlib import Path


def test_guide_example_runs(capsys: object) -> None:
    runpy.run_path(
        str(Path(__file__).parents[1] / "docs" / "examples" / "eigener_adapter.py"),
        run_name="__main__",
    )
