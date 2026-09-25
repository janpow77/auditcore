"""Run the quick-start code blocks of a README (doctest-like runner).

Every ```` ```python ```` block of the section „Schnellstart“ is executed in
order in one shared namespace; ```` ```pycon ```` blocks (``>>>`` prompts) are
checked with :mod:`doctest` against that namespace. Blocks whose info string
contains ``no-run`` are skipped (for example shell output or optional extras).

    PYTHONPATH=packages/<paket>/src \\
        python scripts/docs/readme_snippets.py packages/<paket>/README.md
"""

from __future__ import annotations

import doctest
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^```([^\n]*)\n(.*?)^```\s*$", re.S | re.M)


def section(text: str, title: str) -> str:
    """Body of the level-2 section ``title`` (empty when missing)."""
    match = re.search(rf"^## {re.escape(title)}[ \t]*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return match.group(1) if match else ""


def code_blocks(body: str) -> list[tuple[str, str]]:
    """``(info, code)`` of every fenced block in ``body``."""
    return [(m.group(1).strip(), m.group(2)) for m in FENCE.finditer(body)]


def runnable_blocks(text: str) -> list[tuple[str, str]]:
    blocks = []
    for info, code in code_blocks(section(text, "Schnellstart")):
        words = info.split()
        language = words[0] if words else ""
        if language in {"python", "pycon"} and "no-run" not in words:
            blocks.append((language, code))
    return blocks


def run(readme: Path) -> int:
    """Execute the quick start; return the number of failed doctest examples."""
    namespace: dict[str, object] = {"__name__": "__readme__"}
    failures = 0
    for index, (language, code) in enumerate(runnable_blocks(readme.read_text("utf-8")), 1):
        name = f"{readme}#schnellstart-{index}"
        if language == "python":
            exec(compile(code, name, "exec"), namespace)  # noqa: S102 - eigener README-Code
            continue
        test = doctest.DocTestParser().get_doctest(code, dict(namespace), name, str(readme), 0)
        runner = doctest.DocTestRunner(
            optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE
        )
        failures += runner.run(test, clear_globs=False).failed
        namespace.update(test.globs)
    return failures


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("Aufruf: readme_snippets.py <README.md>", file=sys.stderr)
        return 2
    return 1 if run(Path(argv[0])) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
