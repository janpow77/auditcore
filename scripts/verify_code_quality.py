"""Run the binding code-quality ratchet from a source checkout.

Equivalent to ``auditcore-codegate check`` but usable without installing the
platform: the repository ``src`` directory is put first on ``sys.path``.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from auditcore.tools.quality.codegate_cli import main  # noqa: E402

if __name__ == "__main__":
    arguments = sys.argv[1:]
    if not arguments or arguments[0].startswith("-"):
        arguments = ["check", "--root", str(ROOT), *arguments]
    raise SystemExit(main(arguments))
