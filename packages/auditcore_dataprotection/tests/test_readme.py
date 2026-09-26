"""The Python quick start in README.md runs as documented."""

from __future__ import annotations

import re
from pathlib import Path

README = Path(__file__).resolve().parents[1] / "README.md"


def test_readme_quick_start_runs() -> None:
    text = README.read_text(encoding="utf-8")
    section = text.split("## Schnellstart\n", 1)[1]
    blocks = re.findall(r"```python\n(.*?)```", section.split("\n## ", 1)[0], re.S)
    assert len(blocks) >= 2
    namespace: dict[str, object] = {}
    for block in blocks:
        exec(compile(block, "README.md", "exec"), namespace)  # noqa: S102
    released = namespace["d"]
    assert released.release_open_points  # type: ignore[attr-defined]
    assert "Bei der Freigabe offen" in str(namespace["html"])
    assert "Verzeichnis von Verarbeitungstätigkeiten" in str(namespace["ansicht"])
    assert "freigegeben am" in str(namespace["ansicht"])
