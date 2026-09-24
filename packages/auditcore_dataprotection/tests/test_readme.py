"""The Python quick start in README.md runs as documented."""

from __future__ import annotations

import re
from pathlib import Path

README = Path(__file__).resolve().parents[1] / "README.md"


def test_readme_quick_start_runs() -> None:
    text = README.read_text(encoding="utf-8")
    section = text.split("## Schnellstart in Python", 1)[1]
    code = re.search(r"```python\n(.*?)```", section, re.S)
    assert code is not None
    namespace: dict[str, object] = {}
    exec(compile(code.group(1), "README.md", "exec"), namespace)  # noqa: S102
    released = namespace["d"]
    assert released.release_open_points  # type: ignore[attr-defined]
    assert "Bei der Freigabe offen" in str(namespace["html"])
