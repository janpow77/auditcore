"""Runtime dependencies must carry MIT-compatible licenses."""

from __future__ import annotations

import re
from importlib.metadata import PackageNotFoundError, distribution, requires

ALLOWED = re.compile(r"\b(MIT|BSD|Apache|ISC|PSF|Python Software Foundation)\b", re.IGNORECASE)
FORBIDDEN = re.compile(r"\b(A?GPL|LGPL|SSPL|BUSL|BSL|Commons Clause|proprietary)\b", re.IGNORECASE)


def _license_text(name: str) -> str:
    metadata = distribution(name).metadata
    parts = [metadata.get("License-Expression") or "", metadata.get("License") or ""]
    parts += [c for c in metadata.get_all("Classifier") or [] if c.startswith("License ::")]
    return " ".join(parts)


def _runtime_dependencies() -> list[str]:
    names = []
    for requirement in requires("auditcore_runner") or []:
        name = re.split(r"[\s\[<>=;!~]", requirement, maxsplit=1)[0]
        optional = "extra ==" in requirement and "github-app" not in requirement
        if not optional:
            names.append(name)
    return names


def test_runtime_dependencies_are_mit_compatible() -> None:
    checked = 0
    for name in _runtime_dependencies():
        try:
            text = _license_text(name)
        except PackageNotFoundError:
            continue
        assert ALLOWED.search(text), f"{name}: Lizenz unklar ({text!r})"
        assert not FORBIDDEN.search(text), f"{name}: nicht MIT-verträglich ({text!r})"
        checked += 1
    assert checked >= 1
