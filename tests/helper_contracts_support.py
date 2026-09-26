"""Shared fixtures for the ``auditcore-helpers`` tests."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from auditcore.tools.helpers.model import HelperToolError
from auditcore.tools.helpers.nodetools import ensure_toolchain

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "helpers"
CASES = ROOT / "contracts" / "common-cases"
REQUIRE_NODE = "AUDITCORE_HELPERS_REQUIRE_NODE"


def node_or_skip() -> Path:
    """Install the Node toolchain once; skip locally without Node, fail in CI."""
    try:
        return ensure_toolchain()
    except HelperToolError as error:
        if os.environ.get(REQUIRE_NODE):
            raise
        pytest.skip(f"Node-Werkzeugkette nicht verfügbar: {error}")


def copy_fixture(name: str, target: Path) -> Path:
    """Copy a fixture app into ``target`` (tests may write baselines there)."""
    destination = target / name
    shutil.copytree(FIXTURES / name, destination)
    return destination
