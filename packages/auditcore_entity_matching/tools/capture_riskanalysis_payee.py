"""Capture the original riskanalysis payee normaliser and its RF09 name score.

Compiles only the pinned, unchanged definitions ``_LEGAL``, ``_NONWORD``,
``_WS`` and ``normalize_name`` (verified by Git blob) from
``backend/app/pipeline/payee_normalizer.py`` and executes them. The rapidfuzz
``token_set_ratio`` of normalised pairs and the unchanged
``red_flags._name_match`` (blob-verified, rapidfuzz branch) are recorded as
well, because the riskanalysis red-flag rule RF09 scores exactly these
values. Never imports ``auditcore_entity_matching``, never touches a database
or network.

    python tools/capture_riskanalysis_payee.py <riskanalysis checkout> \
        tests/fixtures/riskanalysis_payee_observed.json
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import platform
import re
import subprocess
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import rapidfuzz
from rapidfuzz import fuzz

REPOSITORY = "janpow77/riskanalysis"
COMMIT = "b5c523bf7eaa326153778d9751f176f03d4d56ed"
PATH = "backend/app/pipeline/payee_normalizer.py"
BLOB = "fceae5b0d3364c5b20cc638ce4453ac082085aa7"
SYMBOLS = ["_LEGAL", "_NONWORD", "_WS", "normalize_name"]
RED_FLAGS_PATH = "backend/app/pipeline/red_flags.py"
RED_FLAGS_BLOB = "b6196a7dbd3838bd4dd361c71e3cc44c904f4980"

#: Synthetic names only (no personal data): legal forms, umlauts, punctuation,
#: generic words, multi-token forms (``e k``, ``e v``) and non-text inputs.
NAMES: list[Any] = [
    "Müller GmbH",
    "MÜLLER GMBH",
    "Mueller GmbH",
    "Müller-Lüdenscheidt KG",
    "ÄRZTE e.V.",
    "Ärztekammer Nord e. V.",
    "Straße Bau AG",
    "STRASSE BAU AG",
    "Bau & Co. KG",
    "Bau und Co KG",
    "The Company Ltd.",
    "Stiftung e k Test",
    "Handel e.K.",
    "Handel e K",
    "Handel eK",
    "Beispiel gGmbH",
    "Beispiel GmbH & Co. KGaA",
    "Beispiel mbH",
    "Partner PartG mbB",
    "Verein für Sport e.V.",
    "Gesellschaft für Technik mbH",
    "Société Générale S.A.",
    "Çelik Yapı A.Ş.",
    "Øresund ApS",
    "Łódź Sp. z o.o.",
    "ﬁnanz ﬂow GmbH",
    "Ｆｕｌｌｗｉｄｔｈ GmbH",
    "Straße",
    "the und GmbH",
    "  Leer   Zeichen  GmbH  ",
    "GmbH",
    "AG",
    "ag bau",
    "Bauag",
    "Sage GmbH",
    "Seeger SE",
    "Ugur UG (haftungsbeschränkt)",
    "Kg-Handel",
    "Co-Working GmbH",
    "Evangelische Kirche e.V.",
    "Theater am Markt",
    "Undine Werft",
    "1&1 Telecom GmbH",
    "3M Deutschland GmbH",
    "A.B.C. Services",
    "Beispiel\tGmbH\nNord",
    "Ⅳ Consulting",
    "",
    "   ",
    None,
    float("nan"),
    12345,
    12.5,
    "nan",
    "None",
]

#: Pairs for the RF09 score (Begünstigter, Auftragnehmer).
PAIRS: list[tuple[Any, Any]] = [
    ("Beispiel GmbH", "Beispiel GmbH"),
    ("Alpha GmbH", "Lieferant Müller KG"),
    ("Selbst GmbH", "Selbst GmbH"),
    ("Müller GmbH", "Mueller GmbH"),
    ("Müller Bau GmbH", "Bau Müller KG"),
    ("Stadtwerke Nord GmbH", "Stadtwerke Nord Service GmbH"),
    ("Stadtwerke Nord", "Nordstadtwerke"),
    ("Technik Beispiel AG", "Beispiel Technik"),
    ("Kreis Beispiel", "Landkreis Beispiel"),
    ("ABC", "ABC GmbH"),
    ("Abcd", "Abcd"),
    ("Abcd", "Abce"),
    ("Holzbau Schmidt", "Holzbau Schmitt"),
    ("Holzbau Schmidt", "Metallbau Schmidt"),
    ("Universität Beispielstadt", "Universitaet Beispielstadt"),
    ("Forschung und Entwicklung GmbH", "Forschung Entwicklung"),
    ("Innovation Hub", "Innovations Hub GmbH"),
    ("Innovation Hub", "Hub Innovation"),
    ("", "Beispiel GmbH"),
    (None, "Beispiel GmbH"),
    ("Beispiel GmbH", float("nan")),
    ("GmbH", "GmbH"),
    ("Werk 1", "Werk 2"),
    ("Planungsbüro Nord", "Planungsbuero Nord"),
    ("Planungsbüro Nord", "Planungsbüro Süd"),
]


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def load(checkout: Path) -> dict[str, Any]:
    raw = (checkout / PATH).read_bytes()
    if git_blob(raw) != BLOB:
        raise SystemExit(f"{PATH} does not match the pinned blob")
    tree = ast.parse(raw.decode("utf-8"))

    def pinned(node: ast.stmt) -> bool:
        if isinstance(node, ast.FunctionDef):
            return node.name in SYMBOLS
        return isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id in SYMBOLS for t in node.targets
        )

    wanted = [node for node in tree.body if pinned(node)]
    if len(wanted) != len(SYMBOLS):
        raise SystemExit("missing definitions in payee_normalizer.py")
    module = ast.Module(body=wanted, type_ignores=[])
    namespace: dict[str, Any] = {"re": re, "unicodedata": unicodedata}
    exec(compile(module, PATH, "exec"), namespace)  # noqa: S102 - pinned source
    return namespace


def encode(value: Any) -> Any:
    if isinstance(value, float) and value != value:
        return {"$float": "nan"}
    return value


def load_name_match(checkout: Path, normalize_name: Any) -> Any:
    """Unchanged ``red_flags._name_match`` bound to the pinned normaliser and rapidfuzz."""
    raw = (checkout / RED_FLAGS_PATH).read_bytes()
    if git_blob(raw) != RED_FLAGS_BLOB:
        raise SystemExit(f"{RED_FLAGS_PATH} does not match the pinned blob")
    tree = ast.parse(raw.decode("utf-8"))
    wanted = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_name_match"]
    if len(wanted) != 1:
        raise SystemExit("_name_match missing in red_flags.py")
    namespace: dict[str, Any] = {
        "normalize_name": normalize_name,
        "_HAS_RF": True,
        "_rf_fuzz": fuzz,
        "SequenceMatcher": SequenceMatcher,
    }
    module = ast.Module(body=wanted, type_ignores=[])
    exec(compile(module, RED_FLAGS_PATH, "exec"), namespace)  # noqa: S102 - pinned source
    return namespace["_name_match"]


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
    if head != COMMIT:
        raise SystemExit(f"checkout is at {head}, expected {COMMIT}")
    ns = load(args.checkout)
    normalize_name = ns["normalize_name"]
    name_match = load_name_match(args.checkout, normalize_name)
    cases = [
        {"name": f"normalize-{i:02d}", "input": encode(v), "output": normalize_name(v)}
        for i, v in enumerate(NAMES)
    ]
    pairs = []
    for i, (a, b) in enumerate(PAIRS):
        na, nb = normalize_name(a), normalize_name(b)
        pairs.append(
            {
                "name": f"pair-{i:02d}",
                "left": encode(a),
                "right": encode(b),
                "left_normalized": na,
                "right_normalized": nb,
                "token_set_ratio": float(fuzz.token_set_ratio(na, nb)),
                "name_match": name_match(a, b),
            }
        )
    document = {
        "source": {
            "repository": REPOSITORY,
            "commit": COMMIT,
            "path": PATH,
            "git_blob": BLOB,
            "symbols": SYMBOLS,
        },
        "constants": {
            "legal_pattern": ns["_LEGAL"].pattern,
            "nonword_pattern": ns["_NONWORD"].pattern,
            "whitespace_pattern": ns["_WS"].pattern,
        },
        "environment": {
            "python": platform.python_version(),
            "rapidfuzz": rapidfuzz.__version__,
            "unicode": unicodedata.unidata_version,
        },
        "normalize": cases,
        "pairs": pairs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(cases)} normalisation and {len(pairs)} pair cases written to {args.output}")


if __name__ == "__main__":
    main()
