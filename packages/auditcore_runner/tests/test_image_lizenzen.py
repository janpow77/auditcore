"""Licenses of the programs in the runner image: permissive, or copyleft with text and source reference."""

from __future__ import annotations

import json
import re
from pathlib import Path

PACKAGE = Path(__file__).parents[1]
DATA = PACKAGE / "src" / "auditcore_runner" / "data"
PERMISSIVE = {
    "MIT",
    "ISC",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "0BSD",
    "MIT-0",
    "BlueOak-1.0.0",
    "CC0-1.0",
    "Python-2.0",
    "(BSD-2-Clause OR MIT OR Apache-2.0)",
    "Apache-2.0 OR MIT",
}
# Separate programs under weak or strong copyleft: only with license text in LICENSES/.
COPYLEFT = {"opengrep": "LGPL-2.1", "codespell": "GPL-2.0", "axe-core": "MPL-2.0", "lightningcss": "MPL-2.0"}
REVIEWED = {"parse-cache-control": "BSD-3-Clause", "svg-tags": "MIT"}
FORBIDDEN = re.compile(r"\bAGPL|SSPL|BUSL|Commons Clause", re.IGNORECASE)


def _copyleft_key(name: str) -> str | None:
    base = name.rsplit("/", 1)[-1]
    return next((k for k in COPYLEFT if base == k or base.startswith(f"{k}-") or name == f"@{k}/playwright"), None)


def test_node_lockfile_licenses() -> None:
    lock = json.loads((DATA / "werkzeuge" / "package-lock.json").read_text(encoding="utf-8"))
    problems = []
    for path, entry in lock["packages"].items():
        if not path:
            continue
        name = path.rsplit("node_modules/", 1)[-1]
        license_ = entry.get("license") or REVIEWED.get(name, "UNBEKANNT")
        key = _copyleft_key(name)
        if license_ in PERMISSIVE or (key and license_ == COPYLEFT[key]):
            continue
        problems.append(f"{name}: {license_}")
    assert not problems


def test_binaries_and_copyleft_texts() -> None:
    pins = json.loads((DATA / "werkzeuge" / "binaer.json").read_text(encoding="utf-8"))["werkzeuge"]
    for entry in pins:
        license_ = entry["lizenz"]
        assert not FORBIDDEN.search(license_), entry["name"]
        assert license_ in PERMISSIVE or COPYLEFT.get(entry["name"]) == license_, entry["name"]
    sources = (DATA / "LICENSES" / "QUELLEN.md").read_text(encoding="utf-8")
    for name, license_ in COPYLEFT.items():
        text = DATA / "LICENSES" / f"{name}-{license_}.txt"
        assert text.is_file() and text.stat().st_size > 10_000, name
        assert text.name in sources and "tree/v" in sources


def test_third_party_lists_every_pinned_tool() -> None:
    notice = (PACKAGE / "THIRD_PARTY.md").read_text(encoding="utf-8")
    pins = json.loads((DATA / "werkzeuge" / "binaer.json").read_text(encoding="utf-8"))["werkzeuge"]
    names = [e["name"] for e in pins if e["name"] != "node"]
    for file in ("requirements.txt", "requirements-libcst.txt"):
        lines = (DATA / "werkzeuge" / file).read_text(encoding="utf-8").splitlines()
        names += [line.split("==")[0] for line in lines if "==" in line]
    names += list(json.loads((DATA / "werkzeuge" / "package.json").read_text(encoding="utf-8"))["dependencies"])
    missing = [n for n in names if n.lower() not in notice.lower()]
    assert not missing
    assert "GHSA-69fq-xp46-6x23" in notice and "Semgrep-Regeln" in notice
