"""The exact synthetic responses the capture tool fed to the original clients."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import capture_procurement_legacy as capture  # noqa: E402

_MNEMONIC = {
    "ND": "12-2020",
    "PD": "2020-01-02",
    "TI": {"deu": "Titel", "eng": "Title"},
    "OL": "Amt",
    "NC": "services",
    "PR": "open",
    "TV": 100,
    "TD": "7",
}
CLIENT_INPUTS: dict[tuple[str, str], tuple[int, Any]] = {
    ("ted", "results-mnemonic"): (200, {"results": [_MNEMONIC]}),
    ("ted", "notices-mnemonic"): (200, {"notices": [{**_MNEMONIC, "TI": "Plain"}]}),
    ("ted", "long-names"): (200, {"notices": [{"noticeNumber": "N", "title": "T" * 300}]}),
    ("ted", "empty"): (200, {"notices": []}),
    ("ted", "not-found"): (404, None),
    ("ted", "server-error"): (500, None),
    ("ted", "bad-json"): (200, ValueError("no json")),
    ("ted", "exception"): (0, ConnectionError("down")),
    ("had", "table"): (200, capture.HAD_TABLE),
    ("had", "divs"): (200, capture.HAD_DIVS),
    ("had", "none"): (200, capture.HAD_NONE),
    ("had", "forbidden"): (403, b""),
    ("had", "not-found"): (404, b""),
    ("had", "error"): (500, b""),
    ("had", "exception"): (0, ConnectionError("down")),
}
