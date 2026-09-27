"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

import json
import tempfile
from importlib.metadata import distribution
from importlib.resources import files
from importlib.util import find_spec
from pathlib import Path

from auditcore_runner import decide, validate
from auditcore_runner.cli import build_parser
from auditcore_runner.hardware import Gpu, HostFacts
from auditcore_runner.profile_io import from_json
from auditcore_runner.regeln import Signals
from auditcore_runner.werkzeuge import Finding, Registry, deduplicate, to_sarif


def main() -> None:
    package = distribution("auditcore_runner")
    assert package.version == "0.1.0"
    assert [r for r in package.requires or [] if "extra ==" not in r] == []
    assert find_spec("auditcore") is None
    data = files("auditcore_runner").joinpath("data")
    for name in (
        "Dockerfile",
        "supervisor.sh",
        "schemas/profil.schema.json",
        "schemas/runner-pool.schema.json",
        "beispiele/workstation-2gpu.json",
        "beispiele/server-cpu.json",
        "web/index.html",
        "web/tokens.css",
        "workflows/runner-wahl.yml",
        "templates/scaleset.service",
        "templates/auditcore-ci-egress.timer",
    ):
        assert data.joinpath(name).is_file(), name
    profile = from_json(json.loads(data.joinpath("beispiele", "workstation-2gpu.json").read_text(encoding="utf-8")))
    cards = tuple(Gpu(g.index, g.uuid, g.name, g.vram_mb) for g in profile.gpus)
    assert validate(profile, HostFacts("workstation", 32, 64 * 1024, 0, 0, cards)) == []
    signals = Signals(cpu_count=32, load_1m=1.0, memory_available_mb=40_000, swap_used_mb=0, idle_seconds=3600)
    assert decide(profile, signals).targets == {"cpu-gross": 3, "gpu-16gb": 2}
    assert "ruff" in Registry().names()
    finding = Finding("ruff", "F401", "a.py", 1, "unused")
    assert to_sarif(deduplicate([finding, finding]))["version"] == "2.1.0"
    assert build_parser().parse_args(["profil", "schema"]).aktion == "schema"
    with tempfile.TemporaryDirectory() as directory:
        assert Path(directory).is_dir()
    print("auditcore_runner installed smoke: ok")


if __name__ == "__main__":
    main()
