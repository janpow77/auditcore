"""Decide where the job image takes its auditcore dependencies from.

``deps_source.py WHEEL REQUIREMENTS`` prints ``release`` when every auditcore
requirement of the wheel is pinned with the same version in the hash-bound
release requirements, otherwise ``repo``. ``--names REQUIREMENTS`` prints the
auditcore distributions listed in the requirements file.
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

_PINNED = re.compile(r"^(auditcore_[a-z_]+) @ \S+/\1-([0-9][0-9.]*)-py3-none-any\.whl", re.M)
_REQUIRES = re.compile(r"^Requires-Dist: (auditcore[-_][a-z_-]+)==([0-9][0-9.]*)\s*$", re.M)


def pinned(requirements: Path) -> dict[str, str]:
    """Distribution → version of the release wheels in the requirements file."""
    return dict(_PINNED.findall(requirements.read_text(encoding="utf-8")))


def required(wheel: Path) -> dict[str, str]:
    """Unconditional auditcore requirements declared in the wheel metadata."""
    with zipfile.ZipFile(wheel) as archive:
        name = next(n for n in archive.namelist() if n.endswith(".dist-info/METADATA"))
        metadata = archive.read(name).decode("utf-8")
    return {n.replace("-", "_"): v for n, v in _REQUIRES.findall(metadata)}


def main(argv: list[str]) -> int:
    if argv[:1] == ["--names"]:
        print("\n".join(sorted(pinned(Path(argv[1])))))
        return 0
    have = pinned(Path(argv[1]))
    need = required(Path(argv[0]))
    print("release" if all(have.get(n) == v for n, v in need.items()) else "repo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
