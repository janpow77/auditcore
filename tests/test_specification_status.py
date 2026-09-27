"""Status „spezifiziert“ only with a holding specification block (scripts/docs/specification.py)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "docs"))

import catalog  # noqa: E402
import specification  # noqa: E402

DOCUMENT = "\n\n".join(
    [*specification.SECTIONS, "I1 Summe bleibt gleich. Legacy: `mod.legacy_parse`."]
)
TESTS = "from hypothesis import given\n\ndef test_i1_sum() -> None:\n    '''I1'''\n"
BLOCK = {
    "document": "docs/spezifikation.md",
    "property_tests": ["tests/test_spezifikation.py"],
    "invariants": ["I1"],
    "legacy_variants": ["mod.legacy_parse"],
}


def _package(
    tmp_path: Path, block: object | None, document: str = DOCUMENT, tests: str = TESTS
) -> Path:
    (tmp_path / "docs").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "docs" / "spezifikation.md").write_text(document, "utf-8")
    (tmp_path / "tests" / "test_spezifikation.py").write_text(tests, "utf-8")
    data: dict[str, object] = {"classification": "EXTRACTION", "characterization": {"x": 1}}
    if block is not None:
        data["specification"] = block
    (tmp_path / "provenance.json").write_text(json.dumps(data), "utf-8")
    return tmp_path


def test_characterised_without_block_stays_characterised(tmp_path: Path) -> None:
    assert catalog.status(_package(tmp_path, None)) == "charakterisiert"


def test_holding_block_is_specified(tmp_path: Path) -> None:
    assert catalog.status(_package(tmp_path, BLOCK)) == "spezifiziert"


@pytest.mark.parametrize(
    ("change", "document", "tests", "message"),
    [
        ({"document": "docs/fehlt.md"}, DOCUMENT, TESTS, "fehlt"),
        ({}, DOCUMENT.replace("## Abgrenzung", ""), TESTS, "Abgrenzung"),
        ({"invariants": ["I2"]}, DOCUMENT, TESTS, "I2 fehlt im Dokument"),
        ({}, DOCUMENT, TESTS.replace("I1", "Ix").replace("i1", "ix"), "I1 ohne Eigenschaftstest"),
        ({}, DOCUMENT, TESTS.replace("hypothesis", "random"), "ohne Hypothesis"),
        ({"invariants": ["A1"]}, DOCUMENT, TESTS, "heißt nicht"),
        ({"invariants": []}, DOCUMENT, TESTS, "keine Invarianten"),
        ({"legacy_variants": ["mod.other"]}, DOCUMENT, TESTS, "mod.other"),
        ({"property_tests": "x"}, DOCUMENT, TESTS, "Liste"),
    ],
)
def test_block_that_does_not_hold_fails_the_catalog(
    tmp_path: Path, change: dict[str, object], document: str, tests: str, message: str
) -> None:
    package = _package(tmp_path, {**BLOCK, **change}, document, tests)
    with pytest.raises(specification.SpecificationError, match=message):
        catalog.status(package)


def test_invariant_ids_match_as_words() -> None:
    assert specification._words("siehe I1.", "I1")
    assert not specification._words("I10 und I11", "I1")


def test_new_packages_are_not_marked_specified(tmp_path: Path) -> None:
    package = _package(tmp_path, BLOCK)
    data = json.loads((package / "provenance.json").read_text("utf-8"))
    data["classification"] = "NEW_IMPLEMENTATION"
    (package / "provenance.json").write_text(json.dumps(data), "utf-8")
    assert catalog.status(package) == "neu, gegen charakterisierte Verträge"
