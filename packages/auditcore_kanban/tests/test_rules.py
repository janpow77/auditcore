from __future__ import annotations

from dataclasses import replace

from conftest import make_card

from auditcore_kanban import Board, TransitionPolicy, check_capacity, check_move, wip_states
from auditcore_kanban.rules import movable_targets


def _move(board: Board, card_id: str, target: str) -> tuple[bool, str]:
    card = board.card(card_id)
    assert card is not None
    decision = check_move(board, card, target)
    return decision.allowed, decision.code


def test_free_policy_allows_everything_but_unknown_columns(board: Board) -> None:
    assert _move(board, "a", "erledigt") == (True, "OK")
    assert _move(board, "a", "nope") == (False, "UNKNOWN_COLUMN")


def test_restricted_policy(board: Board) -> None:
    policy = TransitionPolicy(allowed=frozenset({("offen", "in_arbeit")}))
    restricted = replace(board, transitions=policy)
    assert _move(restricted, "a", "in_arbeit")[0]
    assert _move(restricted, "a", "erledigt") == (False, "TRANSITION_NOT_ALLOWED")
    assert _move(restricted, "a", "offen") == (True, "OK")
    assert policy.mode == "restricted" and TransitionPolicy().mode == "free"


def test_locked_column_keeps_cards_but_allows_reorder(board: Board) -> None:
    locked = replace(board, transitions=TransitionPolicy(locked_columns=frozenset({"in_arbeit"})))
    assert _move(locked, "c", "offen") == (False, "COLUMN_LOCKED")
    assert _move(locked, "c", "in_arbeit") == (True, "OK")


def test_fixed_order_column(board: Board) -> None:
    fixed = replace(board, transitions=TransitionPolicy(fixed_order_columns=frozenset({"offen"})))
    assert _move(fixed, "a", "offen") == (False, "ORDER_FIXED")
    assert _move(fixed, "a", "in_arbeit")[0]


def test_wip_block_and_warn(board: Board) -> None:
    full = replace(board, cards=board.cards + (make_card("e", "in_arbeit", "k"),))
    assert _move(full, "a", "in_arbeit") == (False, "WIP_LIMIT_REACHED")
    assert _move(full, "c", "in_arbeit") == (True, "OK")
    warn = replace(full, wip_mode="warn")
    card = warn.card("a")
    assert card is not None
    decision = check_move(warn, card, "in_arbeit")
    assert decision.allowed and decision.warnings == ("WIP_LIMIT_REACHED",)
    assert check_capacity(full, "in_arbeit", exclude_card_id="c").allowed
    states = {s.column_id: s for s in wip_states(full)}
    assert states["in_arbeit"].full and not states["in_arbeit"].over
    assert not states["offen"].full


def test_movable_targets(board: Board) -> None:
    card = board.card("a")
    assert card is not None
    assert movable_targets(board, card) == ("in_arbeit", "erledigt")
