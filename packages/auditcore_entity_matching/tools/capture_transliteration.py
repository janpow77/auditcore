"""Capture the transliterating sanctions normalisation of 23.09.2026 (Profile 2026.09.2).

Both source applications changed their sanctions comparison form after the
user decision of 23.09.2026 („mueller wenn es kein umlaut gibt“):

* audit_designer@1254591 (PR #380): ``falte_diakritika`` normalises to NFC
  and transliterates ä/ö/ü → ae/oe/ue before the unchanged fold map and NFKD.
* flowworkshop@3d1cb40 (PR #49): ``normalize_name`` translates ä/ö/ü/ß/ẞ and
  then calls ``auditcore_entity_matching.legacy.flowworkshop_normalize_name``
  of the *installed* library 0.1.0.

This tool compiles only the pinned, blob-verified definitions and executes
them. The flowworkshop original imports the library itself, so the tool must
run in an environment where exactly ``auditcore_entity_matching==0.1.0`` is
installed (checked below); the new library version is never imported. No
database, no network.

    python tools/capture_transliteration.py <audit_designer checkout> \
        <flowworkshop checkout> tests/fixtures/transliteration_observed.json
"""

from __future__ import annotations

import argparse
import copy
import json
import platform
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any

import rapidfuzz

sys.path.insert(0, str(Path(__file__).parent))
from capture_legacy import NAMES, SCORES, load  # noqa: E402

DESIGNER = {
    "repository": "janpow77/audit_designer",
    "commit": "1254591156d3bdf6ccdf4050dec7713a61ad4a20",
    "path": "backend/app/core/shared/research/register/sanctions.py",
    "git_blob": "5c064ddecb473b3f1a4341a0dc6513268d106295",
    "symbols": [
        "RECHTSFORMZUSAETZE",
        "_FALTUNG",
        "_NICHT_WORT",
        "falte_diakritika",
        "normalisiere_name",
        "klassifiziere",
        "STANDARD_MINDESTWERT",
    ],
}
WORKSHOP = {
    "repository": "janpow77/flowworkshop",
    "commit": "3d1cb40221645935c323392d70d84102d05ac7bb",
    "path": "auditworkshop/backend/services/sanctions_service.py",
    "git_blob": "5b9de79484373428f45ddeb879a497b671a29e1c",
    "symbols": ["UMLAUT_UMSCHRIFT", "normalize_name", "_classify"],
}

#: Additional inputs for the new rules: decomposed umlauts, capital sharp s,
#: umlauts next to the unchanged special letters and mixed scripts.
EXTRA_NAMES = [
    "Müller GmbH",
    "MÜLLER",
    "Mueller GmbH",
    "Müller-Lüdenscheidt Söhne",
    "ÄÖÜ äöü ß ẞ",
    "Grüße aus Köln",
    "Göteborg Bröd AB",
    "Jørgen Ødegård",
    "Łukasz Wałęsa",
    "Björk Guðmundsdóttir",
    "Ærø Œnologie",
    "Zürich Versicherung AG",
    "Österreichische Post AG",
    "Übersee-Handel GmbH & Co. KG",
    "ÂÊÎÔÛ âêîôû",
    "Ärger ÄG",
    "öko",
    "Straße",
    "STRASSE",
]
INPUTS = [*NAMES, *[n for n in EXTRA_NAMES if n not in NAMES]]


def head(checkout: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("designer", type=Path)
    parser.add_argument("workshop", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    import auditcore_entity_matching
    from auditcore_entity_matching import legacy as library_010

    if auditcore_entity_matching.__version__ != "0.1.0":
        raise SystemExit("Der flowworkshop-Stand ruft die Bibliothek 0.1.0 auf; sie ist nötig.")
    for source, checkout in ((DESIGNER, args.designer), (WORKSHOP, args.workshop)):
        if head(checkout) != source["commit"]:
            raise SystemExit(f"{checkout}: nicht auf dem gebundenen Commit")
    ds = load(args.designer / DESIGNER["path"], DESIGNER["git_blob"], DESIGNER["symbols"])
    fw = load(args.workshop / WORKSHOP["path"], WORKSHOP["git_blob"], WORKSHOP["symbols"])
    fw["_bibliothek"] = library_010  # the module-level import of the original

    cases: list[dict[str, Any]] = []

    def observe(name: str, operation: str, inputs: Any, call: Any) -> None:
        before = copy.deepcopy(inputs)
        try:
            output, exception = call(), None
        except Exception as exc:  # noqa: BLE001 - characterization records every error
            output, exception = None, {"type": type(exc).__name__, "message": str(exc)}
        assert inputs == before
        cases.append(
            {
                "name": name,
                "operation": operation,
                "inputs": inputs,
                "output": output,
                "exception": exception,
            }
        )

    for i, value in enumerate(INPUTS):
        observe(
            f"designer-v2-{i}",
            "designer_normalize_v2",
            {"text": value},
            lambda v=value: ds["normalisiere_name"](v),
        )
        observe(
            f"workshop-v2-{i}",
            "workshop_normalize_v2",
            {"text": value},
            lambda v=value: fw["normalize_name"](v),
        )
    pairs = [("mueller", "mueller"), ("mueller schmidt", "schmidt mueller"), ("muller", "mueller")]
    for score in SCORES:
        for q, m in [(None, None), *pairs]:
            inputs = {"score": score, "q_norm": q, "matched_norm": m}
            observe(
                f"designer-v2-classify-{score}-{q}",
                "designer_classify_v2",
                inputs,
                lambda s=score, a=q, b=m: ds["klassifiziere"](s, a, b),
            )
            observe(
                f"workshop-v2-classify-{score}-{q}",
                "workshop_classify_v2",
                inputs,
                lambda s=score, a=q, b=m: fw["_classify"](s, a, b),
            )

    document = {
        "status": "OBSERVED",
        "scope": "LOCAL_LEGACY_CHARACTERIZATION",
        "decision": "Nutzerentscheidung 23.09.2026: „mueller wenn es kein umlaut gibt“",
        "sources": [
            {k: DESIGNER[k] for k in ("repository", "commit", "path", "git_blob", "symbols")},
            {k: WORKSHOP[k] for k in ("repository", "commit", "path", "git_blob", "symbols")},
        ],
        "environment": {
            "python": platform.python_version(),
            "rapidfuzz": rapidfuzz.__version__,
            "unicode": unicodedata.unidata_version,
            "auditcore_entity_matching_called_by_workshop": "0.1.0",
        },
        "constants": {
            "audit_designer.sanctions.fold_map": dict(ds["_FALTUNG"]),
            "audit_designer.sanctions.legal_suffixes": sorted(ds["RECHTSFORMZUSAETZE"]),
            "audit_designer.sanctions.minimum_score": ds["STANDARD_MINDESTWERT"],
            "flowworkshop.sanctions.umlaut_translation": {
                chr(k): v for k, v in sorted(fw["UMLAUT_UMSCHRIFT"].items())
            },
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
