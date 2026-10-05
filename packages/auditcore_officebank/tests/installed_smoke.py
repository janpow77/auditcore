"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

import json
import tempfile
from importlib.metadata import distribution
from importlib.resources import files
from importlib.util import find_spec
from pathlib import Path

from auditcore_officebank import load_project, mask_secrets
from auditcore_officebank.cli import main
from auditcore_officebank.testing import FakeGuest


def main_smoke() -> None:
    package = distribution("auditcore_officebank")
    assert package.version == "0.1.0"
    assert [r for r in package.requires or [] if "extra ==" not in r] == []
    assert find_spec("auditcore") is None
    schema = files("auditcore_officebank").joinpath("data", "schemas", "projekt.schema.json")
    assert json.loads(schema.read_text(encoding="utf-8"))["$id"] == "auditcore-officebank/projekt/1"
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / ".officebank.toml").write_text(
            'schema = "auditcore-officebank/projekt/1"\n'
            '[projekt]\nkuerzel = "P-T"\nhost = "excel"\n',
            encoding="utf-8",
        )
        assert load_project(root).host == "excel"
    assert mask_secrets("Pwd=x1;") == "Pwd=****;"
    assert FakeGuest().exec_system("Get-Date", 5).exit_code == 0
    assert main(["status"]) == 0
    assert main(["vm", "status"]) == 3
    print("auditcore_officebank installed smoke: ok")


if __name__ == "__main__":
    main_smoke()
