"""Institution names stay out of the packages (scripts/check_institution_names.py)."""

import importlib.util
import re
import sys
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "check_institution_names",
    Path(__file__).resolve().parents[1] / "scripts/check_institution_names.py",
)
assert SPEC is not None and SPEC.loader is not None
script = sys.modules[SPEC.name] = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(script)

TERMS = [script.Term("Musterbank", "Zwischengeschaltete Stelle"), script.Term("MMF", None)]


def test_repository_has_no_names_outside_justified_exceptions() -> None:
    findings, stale = script.check()
    assert findings == []
    assert stale == []


def test_denylist_and_exceptions_are_well_formed() -> None:
    assert script.load_denylist()
    assert all(e.reason for e in script.load_exceptions())


def test_names_match_as_words_including_identifiers_and_regex_boundaries() -> None:
    pattern = script.name_pattern(TERMS)
    for text in ("die MUSTERBANK prüft", "rbvk_musterbank_scorer", r"\bMusterbank\b", "(MMF)"):
        assert pattern.search(text), text
    for text in ("Musterbanken", "XMusterbank", "MMFeld"):
        assert not pattern.search(text), text


def test_neutralize_replaces_only_terms_with_replacement() -> None:
    assert script.neutralize("Musterbank und MMF", TERMS) == "Zwischengeschaltete Stelle und MMF"


def test_exceptions_cover_only_the_allowed_expression() -> None:
    pattern = script.name_pattern(TERMS)
    allowed = script.Allowance("pkg/*", re.compile(r"musterbank_scorer\.py"), "Pfad")
    text = "path = 'musterbank_scorer.py'\nlabel = 'Musterbank'\n"
    findings, used = script.scan_text("pkg/a.py", text, pattern, [allowed])
    assert [f.line for f in findings] == [2] and used == {0}
    findings, used = script.scan_text("other/a.py", text, pattern, [allowed])
    assert len(findings) == 2 and used == set()
