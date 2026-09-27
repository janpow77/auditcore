"""Invarianten aus docs/spezifikation.md als Eigenschaftstests (Hypothesis).

Synthetische Vergleichseinheiten; keine Dateien, kein Netz.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from auditcore_documents import (
    LEGACY_DIFFLIB,
    RECOMMENDED,
    CompareItem,
    ComparisonResult,
    LawParagraph,
    apply_commands,
    base_paragraphs,
    compare_items,
    difflib_ratio,
    normalise_for_match,
    normalise_semantic,
    normalise_verbatim,
    rapidfuzz_token_set,
    word_diff,
)
from auditcore_documents.pipeline.hashing import HashingService

EXAMPLES = settings(max_examples=120, deadline=None)
WORDS = st.sampled_from(
    ["Antrag", "Prüfung", "Belege", "sind", "vorzulegen", "Frist", "§", "3", "Absatz", "Kosten",
     "förderfähig", "nicht", "und", "der", "die", "1.", "a)", "-", "Nachweis", "Zahlung"]
)  # fmt: skip
TEXTS = st.lists(WORDS, min_size=0, max_size=12).map(" ".join)
ANY_TEXT = st.text(max_size=60)
PROFILES = st.sampled_from([RECOMMENDED, LEGACY_DIFFLIB])
MODES = st.sampled_from(["text", "checklist"])


@st.composite
def items(draw: st.DrawFn, prefix: str = "a") -> list[CompareItem]:
    texts = draw(st.lists(TEXTS, max_size=10))
    return [
        CompareItem(
            source_id=f"{prefix}{index}",
            section=draw(st.sampled_from(["", "§ 1", "§ 2", "Kapitel 3"])),
            text=text,
            answer=draw(st.sampled_from(["", "ja", "nein"])),
            location=f"Stelle {index}",
            order=index,
        )
        for index, text in enumerate(texts)
    ]


def _renamed(values: list[CompareItem], prefix: str) -> list[CompareItem]:
    return [replace(item, source_id=f"{prefix}{index}") for index, item in enumerate(values)]


LETTER_FIRST = st.tuples(st.sampled_from(["Antrag", "Prüfung", "Kosten", "Nachweis"]), TEXTS).map(
    " ".join
)


@EXAMPLES
@given(ANY_TEXT, LETTER_FIRST)
def test_i1_normalisation_is_idempotent(text: str, sentence: str) -> None:
    """I1: Normalisierungen sind idempotent (for_match/semantic: Text beginnt mit Wort)."""
    assert normalise_verbatim(normalise_verbatim(text)) == normalise_verbatim(text)
    for normalise in (normalise_for_match, normalise_semantic):
        assert normalise(normalise(sentence)) == normalise(sentence)


@pytest.mark.xfail(
    strict=True,
    reason="Befund B1 (docs/spezifikation.md): je Durchgang wird nur eine führende "
    "Nummerierung entfernt; „1. 2. Text“ und „:0“ ändern sich beim zweiten Durchgang erneut.",
)
@settings(max_examples=200, deadline=None)
@given(ANY_TEXT)
def test_i1_befund_b1_leading_numbering_is_removed_once(text: str) -> None:
    """I1 (Befund B1): für beliebige Texte nicht idempotent."""
    for normalise in (normalise_for_match, normalise_semantic):
        assert normalise(normalise(text)) == normalise(text)


@EXAMPLES
@given(st.lists(st.text(st.characters(blacklist_categories=("Zs", "Cc")), min_size=1), max_size=8),
       st.lists(st.sampled_from([" ", "  ", "\t", "\n"]), min_size=8, max_size=8))  # fmt: skip
def test_i2_verbatim_ignores_whitespace_layout(words: list[str], gaps: list[str]) -> None:
    """I2: ``normalise_verbatim`` hängt nicht von Art und Menge des Leerraums ab."""
    spaced = "".join(word + gap for word, gap in zip(words, gaps, strict=False))
    assert normalise_verbatim(spaced) == normalise_verbatim(" ".join(words))


@EXAMPLES
@given(TEXTS, TEXTS)
def test_i3_word_diff_reconstructs_both_versions(old: str, new: str) -> None:
    """I3: Wortdifferenz leer bei Gleichheit, sonst beide Fassungen rekonstruierbar."""
    if old == new:
        assert word_diff(old, new) == []
        return
    lines = word_diff(old, new)
    assert [line[2:] for line in lines if line[:2] in ("- ", "  ")] == old.split()
    assert [line[2:] for line in lines if line[:2] in ("+ ", "  ")] == new.split()


@EXAMPLES
@given(items(), MODES, PROFILES)
def test_i4_comparison_with_itself_finds_no_change(
    values: list[CompareItem], mode: str, profile: object
) -> None:
    """I4: Vergleich einer Fassung mit sich selbst: alle Einheiten zugeordnet, keine Änderung."""
    rows, counts = compare_items(values, _renamed(values, "b"), mode=mode, profile=profile)  # type: ignore[arg-type]
    assert counts["matched_count"] == len(values)
    assert counts["changed_count"] == counts["removed_count"] == counts["added_count"] == 0
    assert counts["moved_count"] == 0
    assert all(row.status == "unchanged" and not row.selected for row in rows)


@EXAMPLES
@given(items("a"), items("b"), MODES, PROFILES)
def test_i5_every_unit_is_accounted_for_once(
    old: list[CompareItem], new: list[CompareItem], mode: str, profile: object
) -> None:
    """I5: jede Einheit wird genau einmal verbucht (Zählwerte gehen auf)."""
    rows, counts = compare_items(old, new, mode=mode, profile=profile)  # type: ignore[arg-type]
    assert (
        counts["old_count"]
        == counts["matched_count"] + counts["removed_count"] + counts["moved_count"]
    )
    assert (
        counts["new_count"]
        == counts["matched_count"] + counts["added_count"] + counts["moved_count"]
    )
    unchanged = sum(row.status == "unchanged" for row in rows)
    assert unchanged + counts["changed_count"] == counts["matched_count"]
    assert (
        len(rows)
        == counts["matched_count"]
        + counts["removed_count"]
        + counts["added_count"]
        + counts["moved_count"]
    )


@EXAMPLES
@given(items("a"), items("b"), MODES)
def test_i6_result_survives_dict_round_trip(
    old: list[CompareItem], new: list[CompareItem], mode: str
) -> None:
    """I6: ``ComparisonResult.from_dict(r.to_dict()) == r``."""
    rows, counts = compare_items(old, new, mode=mode, profile=LEGACY_DIFFLIB)
    result = ComparisonResult(
        version="1", mode=mode, old_filename="alt.docx", new_filename="neu.docx",
        old_sha256="0" * 64, new_sha256="1" * 64, rows=rows, created_at="2026-09-26T00:00:00",
        **{k: v for k, v in counts.items()},
    )  # fmt: skip
    assert ComparisonResult.from_dict(result.to_dict()) == result


@EXAMPLES
@given(TEXTS, TEXTS)
def test_i7_similarity_is_bounded_and_full_for_identity(left: str, right: str) -> None:
    """I7: Ähnlichkeit in 0…100, Identität 100, token_set symmetrisch."""
    token_set = rapidfuzz_token_set()
    for scorer in (difflib_ratio, token_set):
        assert 0 <= scorer(left, right) <= 100
    assert difflib_ratio(left, left) == 100
    assert token_set(left, right) == token_set(right, left)
    if left.strip():
        assert token_set(left, left) == 100


@EXAMPLES
@given(
    st.lists(st.tuples(st.sampled_from(["§ 1", "§ 2", "§ 10a"]), TEXTS), min_size=1, max_size=12)
)
def test_i8_base_paragraphs_count_per_section(entries: list[tuple[str, str]]) -> None:
    """I8: Absätze werden je Paragraf ab 1 lückenlos gezählt, Text bleibt unverändert."""
    values = [CompareItem(f"s{i}", section=s, text=t) for i, (s, t) in enumerate(entries)]
    paragraphs = base_paragraphs(values)
    seen: dict[str, int] = {}
    for paragraph, (section, text) in zip(paragraphs, entries, strict=True):
        seen[section] = seen.get(section, 0) + 1
        assert (paragraph.section, paragraph.paragraph, paragraph.text) == (
            section,
            seen[section],
            text,
        )


@EXAMPLES
@given(
    st.lists(TEXTS, min_size=1, max_size=5),
    st.lists(st.sampled_from(["Hinweis", "Siehe oben", "Anlage"]), max_size=4),
    st.booleans(),
)
def test_i9_lines_without_command_are_skipped(
    texts: list[str], commands: list[str], renumber: bool
) -> None:
    """I9: Zeilen ohne Änderungsbefehl werden übergangen; der Stammtext bleibt unverändert."""
    paragraphs = [LawParagraph("§ 1", index, text) for index, text in enumerate(texts, start=1)]
    before = [replace(p) for p in paragraphs]
    result, open_commands, recognised = apply_commands(
        paragraphs, commands, renumber_after_insert=renumber
    )
    assert recognised == 0 and open_commands == []
    assert result == before


@EXAMPLES
@given(
    st.lists(st.text(alphabet="0123456789abcdef", min_size=64, max_size=64), max_size=6),
    st.text(max_size=8),
)
def test_i10_linked_chain_is_prefix_stable_and_order_sensitive(
    stages: list[str], seed: str
) -> None:
    """I10: die verkettete Hash-Kette ist präfixstabil, deterministisch und reihenfolgeabhängig."""
    chain = HashingService.linked_chain(stages, seed)
    assert len(chain) == len(stages)
    assert HashingService.linked_chain(stages[:-1], seed) == chain[:-1]
    assert HashingService.linked_chain(stages, seed) == chain
    if stages != stages[::-1]:
        assert HashingService.linked_chain(stages[::-1], seed)[-1] != chain[-1]
    assert HashingService.verify_chain(stages, HashingService.compute_chain_hash(stages)) == bool(
        stages
    )
