"""Capture the PEP name normalisation of flowinvoice (Profile ``flowinvoice.pep``).

``PEPChecker._normalize_name`` (flowinvoice@fb2d185) is executed from the
pinned, blob-verified file. The module is loaded under a package stub because
the real package ``__init__`` imports the whole application (database, ORM);
``pep_checker`` itself only needs ``httpx`` and its sibling ``models``. No
network, no database.

    python tools/capture_flowinvoice.py <checkout> tests/fixtures/flowinvoice_observed.json
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
import types
import unicodedata
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from capture_transliteration import INPUTS  # noqa: E402

SOURCE = {
    "repository": "janpow77/flowinvoice",
    "commit": "fb2d18568d2eaf64574d131ceae51a936b9aac02",
    "path": "backend/app/services/fraud_detection/pep_checker.py",
    "git_blob": "58d1849a626faa00509718287f7a5b793b0d7da1",
    "symbols": ["PEPChecker._normalize_name"],
}
MODELS_BLOB = "e960f32633874444b9ddc0f323dd54f5b0242e59"


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkout", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    head = subprocess.run(
        ["git", "-C", str(args.checkout), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if head != SOURCE["commit"]:
        raise SystemExit("Checkout steht nicht auf dem gebundenen Commit.")
    base = args.checkout / "backend/app/services/fraud_detection"
    if git_blob((base / "pep_checker.py").read_bytes()) != SOURCE["git_blob"]:
        raise SystemExit("pep_checker.py weicht vom gebundenen Blob ab.")
    if git_blob((base / "models.py").read_bytes()) != MODELS_BLOB:
        raise SystemExit("models.py weicht vom gebundenen Blob ab.")
    for name, path in (
        ("app", None),
        ("app.services", None),
        ("app.services.fraud_detection", base),
    ):
        module = types.ModuleType(name)
        module.__path__ = [str(path)] if path else []  # type: ignore[attr-defined]
        sys.modules[name] = module
    for name in ("models", "pep_checker"):
        spec = importlib.util.spec_from_file_location(
            f"app.services.fraud_detection.{name}", base / f"{name}.py"
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    normalize = sys.modules["app.services.fraud_detection.pep_checker"].PEPChecker._normalize_name
    cases: list[dict[str, Any]] = []
    for i, value in enumerate([*INPUTS, "Ivan Petrov", "A B", "x\x1cy"]):
        try:
            output, exception = normalize(value), None
        except Exception as exc:  # noqa: BLE001 - characterization records every error
            output, exception = None, {"type": type(exc).__name__, "message": str(exc)}
        cases.append(
            {
                "name": f"flowinvoice-pep-{i}",
                "operation": "flowinvoice_pep_normalize",
                "inputs": {"text": value},
                "output": output,
                "exception": exception,
            }
        )
    document = {
        "status": "OBSERVED",
        "scope": "LOCAL_LEGACY_CHARACTERIZATION",
        "sources": [SOURCE],
        "environment": {
            "python": platform.python_version(),
            "unicode": unicodedata.unidata_version,
        },
        "cases": cases,
    }
    args.output.write_text(
        json.dumps(document, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"{len(cases)} Fälle → {args.output}")


if __name__ == "__main__":
    main()
