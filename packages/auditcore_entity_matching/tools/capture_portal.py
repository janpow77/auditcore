"""Capture the audit-portal comparison forms (Profiles ``audit_portal.name[_folded]``).

``audit_prep.normalization.normalize_name`` and ``normalize_name_folded``
(audit-portal@ac1ccc7) are executed from the pinned, blob-verified package
``audit_prep`` (standard library only). No network, no database.

    python tools/capture_portal.py <checkout> tests/fixtures/portal_observed.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from capture_transliteration import INPUTS  # noqa: E402

SOURCE = {
    "repository": "janpow77/audit-portal",
    "commit": "ac1ccc779db69492db0c2c154b6ec84fdd1794b1",
    "path": "backend/audit_prep/normalization.py",
    "git_blob": "c9f9c3dbb211cd6c215464293bccc5efebf0fc7d",
    "symbols": ["LEGAL_SUFFIXES", "_UMLAUT_FOLD", "normalize_name", "normalize_name_folded"],
}


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
    path = args.checkout / SOURCE["path"]
    if git_blob(path.read_bytes()) != SOURCE["git_blob"]:
        raise SystemExit("normalization.py weicht vom gebundenen Blob ab.")
    sys.path.insert(0, str(args.checkout / "backend"))
    from audit_prep import normalization as portal

    cases: list[dict[str, Any]] = []
    for i, value in enumerate(INPUTS):
        for operation, function in (
            ("portal_name", portal.normalize_name),
            ("portal_name_folded", portal.normalize_name_folded),
        ):
            try:
                output, exception = function(value), None
            except Exception as exc:  # noqa: BLE001 - characterization records every error
                output, exception = None, {"type": type(exc).__name__, "message": str(exc)}
            cases.append(
                {
                    "name": f"{operation}-{i}",
                    "operation": operation,
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
        "constants": {
            "legal_suffixes": sorted(portal.LEGAL_SUFFIXES),
            "umlaut_fold": {chr(k): v for k, v in sorted(portal._UMLAUT_FOLD.items())},
        },
        "cases": cases,
    }
    args.output.write_text(
        json.dumps(document, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"{len(cases)} Fälle → {args.output}")


if __name__ == "__main__":
    main()
