"""The Node toolchain is installed once even when several processes start at the same time."""

import os
import subprocess
import sys
from pathlib import Path

FAKE_NPM = """#!/bin/sh
# Slow fake "npm ci": counts calls and fails like npm when another run is busy.
echo x >> "$NPM_CALLS"
[ -d node_modules ] && { echo "ENOTEMPTY" >&2; exit 1; }
mkdir node_modules
sleep 1
for m in typescript tsx; do mkdir -p node_modules/$m; echo '{}' > node_modules/$m/package.json; done
"""

CALL = "from auditcore.tools.helpers.nodetools import ensure_toolchain; print(ensure_toolchain())"


def test_parallel_processes_install_once(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    npm = bin_dir / "npm"
    npm.write_text(FAKE_NPM)
    npm.chmod(0o755)
    calls = tmp_path / "calls"
    env = {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "XDG_CACHE_HOME": str(tmp_path / "cache"),
        "NPM_CALLS": str(calls),
    }
    env.pop("AUDITCORE_HELPERS_TOOLCHAIN", None)
    processes = [
        subprocess.Popen(  # noqa: S603
            [sys.executable, "-c", CALL], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        for _ in range(4)
    ]
    results = [process.communicate(timeout=60) for process in processes]
    assert [p.returncode for p in processes] == [0, 0, 0, 0], [r[1] for r in results]
    assert calls.read_text().count("x") == 1
