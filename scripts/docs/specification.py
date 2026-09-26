"""Check the functional specification of a package (status „spezifiziert“).

A characterised package counts as specified when its ``provenance.json``
carries a ``specification`` block and the files it names hold what the block
promises::

    "specification": {
      "document": "docs/spezifikation.md",
      "property_tests": ["tests/test_spezifikation.py"],
      "invariants": ["I1", "I2", ...],
      "legacy_variants": ["zvg.legacy_parse_de_number", ...]
    }

* the document exists and has every section of :data:`SECTIONS`;
* every invariant id appears as a word in the document and in at least one
  property-test file, and those files use Hypothesis;
* every documented legacy variant is named in the document.

A block that does not hold is an error (the catalog check fails), never a
silent fallback to „charakterisiert“. Template: ``docs/bibliotheken/spezifikation-vorlage.md``.

    python scripts/docs/specification.py packages/auditcore_legal_sources
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path

SECTIONS = (
    "## Zweck",
    "## Verträge",
    "## Invarianten",
    "## Fehlerfälle",
    "## Abgrenzung",
    "## Bewusste Abweichungen vom Altverhalten",
)
INVARIANT_ID = re.compile(r"^I\d+$")


class SpecificationError(ValueError):
    """The ``specification`` block of a package does not hold."""


def _words(text: str, token: str) -> bool:
    return re.search(rf"(?<![\w.]){re.escape(token)}(?![\w])", text) is not None


def _strings(block: Mapping[str, object], key: str, where: str) -> list[str]:
    value = block.get(key, [])
    if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
        raise SpecificationError(f"{where}: '{key}' muss eine Liste von Texten sein.")
    return list(value)


def _read(package_dir: Path, relative: object, where: str) -> str:
    if not isinstance(relative, str) or not relative:
        raise SpecificationError(f"{where}: Pfadangabe fehlt.")
    path = package_dir / relative
    if not path.is_file():
        raise SpecificationError(f"{where}: {relative} fehlt.")
    return path.read_text("utf-8")


def check(package_dir: Path, block: object) -> list[str]:
    """Problems of one ``specification`` block (empty list: it holds)."""
    where = f"{package_dir.name}/provenance.json specification"
    if not isinstance(block, Mapping):
        return [f"{where}: muss ein JSON-Objekt sein."]
    try:
        document = _read(package_dir, block.get("document"), where)
        tests = [
            _read(package_dir, path, where) for path in _strings(block, "property_tests", where)
        ]
        invariants = _strings(block, "invariants", where)
        legacy = _strings(block, "legacy_variants", where)
    except SpecificationError as exc:
        return [str(exc)]
    problems = [f"{where}: Abschnitt „{s}“ fehlt." for s in SECTIONS if s not in document]
    if not tests:
        problems.append(f"{where}: keine Eigenschaftstests angegeben.")
    elif not all("hypothesis" in text for text in tests):
        problems.append(f"{where}: Eigenschaftstests ohne Hypothesis.")
    if not invariants:
        problems.append(f"{where}: keine Invarianten angegeben.")
    for ident in invariants:
        if not INVARIANT_ID.match(ident):
            problems.append(f"{where}: Invariante '{ident}' heißt nicht I<Zahl>.")
        elif not _words(document, ident):
            problems.append(f"{where}: Invariante {ident} fehlt im Dokument.")
        elif not any(_words(text, ident) for text in tests):
            problems.append(f"{where}: Invariante {ident} ohne Eigenschaftstest.")
    problems += [
        f"{where}: Legacy-Variante {name} fehlt im Dokument."
        for name in legacy
        if name not in document
    ]
    return problems


def specified(package_dir: Path, data: Mapping[str, object]) -> bool:
    """Whether ``data`` (a parsed provenance.json) declares a holding specification.

    Raises :class:`SpecificationError` if a declared block does not hold.
    """
    if "specification" not in data:
        return False
    problems = check(package_dir, data["specification"])
    if problems:
        raise SpecificationError("\n".join(problems))
    return True


def main(argv: list[str] | None = None) -> int:
    failed = False
    for name in argv if argv is not None else sys.argv[1:]:
        package_dir = Path(name)
        data = json.loads((package_dir / "provenance.json").read_text("utf-8"))
        try:
            ok = specified(package_dir, data)
        except SpecificationError as exc:
            print(exc, file=sys.stderr)
            failed = True
            continue
        print(f"{package_dir.name}: {'spezifiziert' if ok else 'keine Spezifikation'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
