"""Deterministische Zuordnung und Einstufung der Unterschiede.

Algorithmen unverändert aus ``matching.py`` des Originals; das
Ähnlichkeitsmaß wird ausdrücklich übergeben (siehe :mod:`scoring`).
"""

from __future__ import annotations

import difflib
from collections.abc import Iterable

from auditcore_documents.model import CompareItem, CompareRow
from auditcore_documents.normalize import (
    normalise_for_match,
    normalise_semantic,
    normalise_verbatim,
    word_diff,
)
from auditcore_documents.scoring import Scorer

Pairs = list[tuple[CompareItem, CompareItem]]
Assignment = tuple[Pairs, list[CompareItem], list[CompareItem]]

#: Reihenfolge der Ergebniszeilen; „moved“ fehlt im Original und sortiert
#: deshalb mit 9 ans Ende (charakterisiert, beibehalten).
ROW_ORDER = {"changed": 0, "removed": 1, "added": 2, "unchanged": 3}


def similarity(left: CompareItem, right: CompareItem, scorer: Scorer) -> int:
    return scorer(normalise_for_match(left.text), normalise_for_match(right.text))


def _take_exact(
    old_items: Iterable[CompareItem],
    new_items: list[CompareItem],
) -> tuple[Pairs, list[CompareItem], set[str]]:
    matches: Pairs = []
    unmatched: list[CompareItem] = []
    used_new: set[str] = set()
    for old in old_items:
        candidate = next(
            (
                new
                for new in new_items
                if new.source_id not in used_new
                and normalise_for_match(new.text) == normalise_for_match(old.text)
            ),
            None,
        )
        if candidate is None:
            unmatched.append(old)
            continue
        used_new.add(candidate.source_id)
        matches.append((old, candidate))
    return matches, unmatched, used_new


def checklist_matches(
    old_items: list[CompareItem],
    new_items: list[CompareItem],
    threshold: int,
    scorer: Scorer,
) -> Assignment:
    """Stabile Kennung, dann wortgleich, dann bestes Ähnlichkeitsmaß ≥ Schwelle."""
    matches: Pairs = []
    used_old: set[str] = set()
    used_new: set[str] = set()

    new_by_stable = {item.stable_id: item for item in new_items if item.stable_id}
    for old in old_items:
        if not old.stable_id:
            continue
        candidate = new_by_stable.get(old.stable_id)
        if candidate is None or candidate.source_id in used_new:
            continue
        matches.append((old, candidate))
        used_old.add(old.source_id)
        used_new.add(candidate.source_id)

    remaining_old = [item for item in old_items if item.source_id not in used_old]
    remaining_new = [item for item in new_items if item.source_id not in used_new]
    exact, remaining_old, exact_used = _take_exact(remaining_old, remaining_new)
    matches.extend(exact)
    used_new.update(exact_used)

    for old in remaining_old:
        candidates = [item for item in new_items if item.source_id not in used_new]
        scored = [(similarity(old, item, scorer), item) for item in candidates]
        # max() liefert bei Gleichstand das erste Element – wie im Original.
        best = max(scored, key=lambda pair: pair[0], default=None)
        if best is None or best[0] < threshold:
            continue
        matches.append((old, best[1]))
        used_new.add(best[1].source_id)

    matches.sort(key=lambda pair: pair[0].order)
    matched_old = {old.source_id for old, _new in matches}
    removed = [item for item in old_items if item.source_id not in matched_old]
    added = [item for item in new_items if item.source_id not in used_new]
    return matches, removed, added


def _ordered_fuzzy_block(
    old_items: list[CompareItem],
    new_items: list[CompareItem],
    threshold: int,
    scorer: Scorer,
) -> Assignment:
    """Monotone Zuordnung mit maximaler Punktsumme innerhalb eines Blocks."""
    old_count, new_count = len(old_items), len(new_items)
    scores = [[similarity(old, new, scorer) for new in new_items] for old in old_items]
    dp = [[0 for _ in range(new_count + 1)] for _ in range(old_count + 1)]
    choice = [["" for _ in range(new_count + 1)] for _ in range(old_count + 1)]
    for i in range(1, old_count + 1):
        for j in range(1, new_count + 1):
            best, action = dp[i - 1][j], "old"
            if dp[i][j - 1] > best:
                best, action = dp[i][j - 1], "new"
            score = scores[i - 1][j - 1]
            if score >= threshold and dp[i - 1][j - 1] + score > best:
                best, action = dp[i - 1][j - 1] + score, "match"
            dp[i][j], choice[i][j] = best, action

    pairs: Pairs = []
    matched_old: set[str] = set()
    matched_new: set[str] = set()
    i, j = old_count, new_count
    while i > 0 and j > 0:
        action = choice[i][j]
        if action == "match":
            old, new = old_items[i - 1], new_items[j - 1]
            pairs.append((old, new))
            matched_old.add(old.source_id)
            matched_new.add(new.source_id)
            i -= 1
            j -= 1
        elif action == "old":
            i -= 1
        else:
            j -= 1
    pairs.reverse()
    return (
        pairs,
        [item for item in old_items if item.source_id not in matched_old],
        [item for item in new_items if item.source_id not in matched_new],
    )


def text_matches(
    old_items: list[CompareItem],
    new_items: list[CompareItem],
    threshold: int,
    scorer: Scorer,
) -> Assignment:
    """Reihenfolgetreue Zuordnung: SequenceMatcher, Ersetzungsblöcke unscharf."""
    old_keys = [normalise_for_match(item.text) for item in old_items]
    new_keys = [normalise_for_match(item.text) for item in new_items]
    matcher = difflib.SequenceMatcher(None, old_keys, new_keys, autojunk=False)
    pairs: Pairs = []
    removed: list[CompareItem] = []
    added: list[CompareItem] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            pairs.extend(zip(old_items[i1:i2], new_items[j1:j2], strict=True))
        elif tag == "replace":
            block_pairs, block_removed, block_added = _ordered_fuzzy_block(
                old_items[i1:i2],
                new_items[j1:j2],
                max(70, threshold - 10),
                scorer,
            )
            pairs.extend(block_pairs)
            removed.extend(block_removed)
            added.extend(block_added)
        elif tag == "delete":
            removed.extend(old_items[i1:i2])
        elif tag == "insert":
            added.extend(new_items[j1:j2])
    return pairs, removed, added


def detect_moves(removed: list[CompareItem], added: list[CompareItem]) -> Assignment:
    """Wortgleich entfallene und neue Stellen sind eine Umstellung.

    Zuordnung in Reihenfolge des Auftretens; leerer Text belegt keine
    Verschiebung. Liefert (verschoben, restliche entfallene, restliche neue).
    """
    open_items: dict[str, list[CompareItem]] = {}
    for item in added:
        open_items.setdefault(normalise_for_match(item.text), []).append(item)

    moved: Pairs = []
    rest_removed: list[CompareItem] = []
    for item in removed:
        key = normalise_for_match(item.text)
        candidates = open_items.get(key)
        if not key or not candidates:
            rest_removed.append(item)
            continue
        moved.append((item, candidates.pop(0)))

    paired = {new.source_id for _, new in moved}
    rest_added = [item for item in added if item.source_id not in paired]
    return moved, rest_removed, rest_added


def _field_changed(old: str, new: str, include_editorial: bool) -> bool:
    normaliser = normalise_verbatim if include_editorial else normalise_semantic
    return normaliser(old) != normaliser(new)


def _pair_row(
    old: CompareItem,
    new: CompareItem,
    *,
    include_answers: bool,
    include_notes: bool,
    include_editorial: bool,
) -> CompareRow:
    changes = {
        "text": _field_changed(old.text, new.text, include_editorial),
        "answer": include_answers and old.answer != new.answer,
        "comment": include_answers and old.comment != new.comment,
        "note": include_notes and old.note != new.note,
    }
    diff = {
        "text": word_diff(old.text, new.text) if changes["text"] else [],
        "answer": word_diff(old.answer, new.answer) if changes["answer"] else [],
        "comment": word_diff(old.comment, new.comment) if changes["comment"] else [],
        "note": word_diff(old.note, new.note) if changes["note"] else [],
    }
    status = "changed" if any(changes.values()) else "unchanged"
    return CompareRow(
        row_id=f"match-{old.source_id}-{new.source_id}",
        status=status,
        location=new.location or old.location or new.section or old.section,
        old_text=old.text,
        new_text=new.text,
        old_answer=old.answer,
        new_answer=new.answer,
        old_comment=old.comment,
        new_comment=new.comment,
        old_note=old.note,
        new_note=new.note,
        selected=status != "unchanged",
        diff=diff,
    )


def _moved_row(old_item: CompareItem, new_item: CompareItem) -> CompareRow:
    source = old_item.location or old_item.section
    target = new_item.location or new_item.section
    return CompareRow(
        row_id=f"moved-{old_item.source_id}-{new_item.source_id}",
        status="moved",
        location=(
            f"{source} → {target}" if source and target and source != target else (target or source)
        ),
        old_text=old_item.text,
        new_text=new_item.text,
        old_answer=old_item.answer,
        new_answer=new_item.answer,
        old_comment=old_item.comment,
        new_comment=new_item.comment,
        old_note=old_item.note,
        new_note=new_item.note,
    )


def _removed_row(item: CompareItem) -> CompareRow:
    return CompareRow(
        row_id=f"removed-{item.source_id}",
        status="removed",
        location=item.location or item.section,
        old_text=item.text,
        old_answer=item.answer,
        old_comment=item.comment,
        old_note=item.note,
    )


def _added_row(item: CompareItem) -> CompareRow:
    return CompareRow(
        row_id=f"added-{item.source_id}",
        status="added",
        location=item.location or item.section,
        new_text=item.text,
        new_answer=item.answer,
        new_comment=item.comment,
        new_note=item.note,
    )


def build_rows(
    mode: str,
    pairs: Pairs,
    removed: list[CompareItem],
    added: list[CompareItem],
    *,
    include_answers: bool,
    include_notes: bool,
    include_editorial: bool,
    moved: Pairs | None = None,
) -> list[CompareRow]:
    """Ergebniszeilen; ``mode`` wird wie im Original nicht ausgewertet."""
    del mode
    rows = [
        _pair_row(
            old,
            new,
            include_answers=include_answers,
            include_notes=include_notes,
            include_editorial=include_editorial,
        )
        for old, new in pairs
    ]
    rows.extend(_moved_row(old_item, new_item) for old_item, new_item in moved or [])
    rows.extend(_removed_row(item) for item in removed)
    rows.extend(_added_row(item) for item in added)
    rows.sort(key=lambda row: (ROW_ORDER.get(row.status, 9), row.row_id))
    return rows
