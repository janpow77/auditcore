"""Application service: load, check version, run a pure command, save, log events."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from . import board_commands as bc
from . import commands as cc
from .commands import CommandResult, Context
from .errors import KanbanError
from .events import BoardEvent, Change, Clock, EventLog, InMemoryEventLog, utc_now
from .filtering import CardFilter, filter_cards
from .model import Board, Card, Column, TransitionPolicy
from .permissions import Action, authorize, check_share, role_of
from .storage import BoardStore, check_board_id
from .templates import template
from .validation import DEFAULT_LIMITS, Limits

Command = Callable[[Board, Context], CommandResult]


@dataclass(frozen=True)
class Outcome:
    """Result of a service call: the saved board, the command result and its events."""

    board: Board
    result: CommandResult
    events: tuple[BoardEvent, ...]


class BoardService:
    """Framework-free use cases on top of a :class:`BoardStore`.

    ``inherited_grants`` returns container grants for a board (e.g. notebook
    shares); ``user_exists`` lets sharing reject unknown users (404).
    """

    def __init__(
        self,
        store: BoardStore,
        events: EventLog | None = None,
        clock: Clock = utc_now,
        new_id: Callable[[], str] | None = None,
        limits: Limits = DEFAULT_LIMITS,
        inherited_grants: Callable[[Board], Mapping[str, str]] | None = None,
        user_exists: Callable[[str], bool] | None = None,
    ) -> None:
        self.store = store
        self.events = events if events is not None else InMemoryEventLog()
        self.clock = clock
        self.new_id = new_id or (lambda: uuid.uuid4().hex)
        self.limits = limits
        self.inherited_grants = inherited_grants
        self.user_exists = user_exists

    # -- helpers ------------------------------------------------------------

    def _inherited(self, board: Board) -> Mapping[str, str] | None:
        return None if self.inherited_grants is None else self.inherited_grants(board)

    def context(self, actor: str, board: Board | None = None) -> Context:
        inherited = None if board is None else self._inherited(board)
        return Context(actor, self.clock(), inherited, self.limits, self.new_id)

    def _load(self, board_id: str) -> Board:
        board = self.store.get(check_board_id(board_id))
        if board is None:
            raise KanbanError("NOT_VISIBLE", "Board nicht gefunden")
        return board

    def run(
        self, board_id: str, actor: str, command: Command, expected_version: int | None = None
    ) -> Outcome:
        """Visibility first, then the optimistic version check, then the command."""
        board = self._load(board_id)
        ctx = self.context(actor, board)
        authorize(board, actor, Action.READ, ctx.inherited).raise_if_denied()
        if expected_version is not None and expected_version != board.version:
            raise KanbanError("VERSION_CONFLICT", "Das Board wurde inzwischen geändert")
        result = command(board, ctx)
        self.store.save(result.board, board.version)
        events = self.events.record(board.id, result.board.version, actor, ctx.now, result.changes)
        return Outcome(result.board, result, events)

    # -- queries ------------------------------------------------------------

    def get_board(self, board_id: str, actor: str) -> tuple[Board, str]:
        """Board and the actor's role (NOT_VISIBLE if they have none)."""
        board = self._load(board_id)
        inherited = self._inherited(board)
        authorize(board, actor, Action.READ, inherited).raise_if_denied()
        return board, role_of(board, actor, inherited) or "read"

    def list_boards(self, actor: str, include_archived: bool = False) -> list[tuple[Board, str]]:
        """Visible boards: pinned first, then most recently updated (original order)."""
        visible: list[tuple[Board, str]] = []
        for board in self.store.list():
            role = role_of(board, actor, self._inherited(board))
            if role is not None and (include_archived or not board.archived):
                visible.append((board, role))
        visible.sort(key=lambda item: item[0].updated_at, reverse=True)
        visible.sort(key=lambda item: not item[0].pinned)
        return visible

    def find_cards(
        self, board_id: str, actor: str, criteria: CardFilter, today: date | None = None
    ) -> tuple[Card, ...]:
        board, _ = self.get_board(board_id, actor)
        return filter_cards(board, criteria, today or date.today())

    def events_since(self, board_id: str, actor: str, seq: int = 0) -> tuple[BoardEvent, ...]:
        self.get_board(board_id, actor)
        return self.events.since(board_id, seq)

    # -- board commands -----------------------------------------------------

    def create_board(
        self, actor: str, title: str = "Neues Board", icon: str = "📋",
        template_key: str | None = None, board_id: str | None = None,
    ) -> Outcome:
        chosen = None
        if template_key is not None:
            chosen = template(template_key)
            if chosen is None:
                raise KanbanError("VALIDATION_ERROR", f"Unbekannte Vorlage '{template_key}'")
        new_id = check_board_id(board_id or self.new_id())
        if self.store.get(new_id) is not None:
            raise KanbanError("BOARD_EXISTS", "Board existiert bereits")
        ctx = self.context(actor)
        result = bc.create_board(ctx, new_id, title, icon, chosen)
        self.store.save(result.board, None)
        events = self.events.record(new_id, result.board.version, actor, ctx.now, result.changes)
        return Outcome(result.board, result, events)

    def update_board(self, board_id: str, actor: str, *, title: str | None = None,
                     icon: str | None = None, pinned: bool | None = None,
                     archived: bool | None = None, expected_version: int | None = None) -> Outcome:
        return self.run(board_id, actor, lambda b, c: bc.update_board(
            b, c, title=title, icon=icon, pinned=pinned, archived=archived), expected_version)

    def delete_board(self, board_id: str, actor: str) -> None:
        board = self._load(board_id)
        ctx = self.context(actor, board)
        authorize(board, actor, Action.DELETE_BOARD, ctx.inherited).raise_if_denied()
        self.store.delete(board.id)
        self.events.record(board.id, board.version + 1, actor, ctx.now,
                           (Change("board.deleted"),))

    def configure_columns(self, board_id: str, actor: str, columns: Sequence[Column],
                          transitions: TransitionPolicy | None = None,
                          expected_version: int | None = None) -> Outcome:
        return self.run(board_id, actor,
                        lambda b, c: bc.configure_columns(b, c, columns, transitions),
                        expected_version)

    def share(self, board_id: str, actor: str, user_id: str, permission: str) -> Outcome:
        """Owner check, permission, self-share, then user existence (original order)."""

        def command(board: Board, ctx: Context) -> CommandResult:
            check_share(board, ctx.actor, user_id, permission).raise_if_denied()
            if self.user_exists is not None and not self.user_exists(user_id):
                raise KanbanError("USER_NOT_FOUND", "Benutzer nicht gefunden")
            return bc.share_board(board, ctx, user_id, permission)

        return self.run(board_id, actor, command)

    def revoke(self, board_id: str, actor: str, user_id: str) -> Outcome:
        return self.run(board_id, actor, lambda b, c: bc.revoke_share(b, c, user_id))

    # -- card commands ------------------------------------------------------

    def create_card(self, board_id: str, actor: str, fields: Mapping[str, object],
                    expected_version: int | None = None) -> Outcome:
        return self.run(board_id, actor, lambda b, c: cc.create_card(b, c, fields),
                        expected_version)

    def update_card(self, board_id: str, actor: str, card_id: str,
                    fields: Mapping[str, object], expected_version: int | None = None) -> Outcome:
        return self.run(board_id, actor, lambda b, c: cc.update_card(b, c, card_id, fields),
                        expected_version)

    def move_card(self, board_id: str, actor: str, card_id: str, column_id: str, *,
                  before_id: str | None = None, after_id: str | None = None,
                  index: int | None = None, expected_version: int | None = None) -> Outcome:
        return self.run(board_id, actor, lambda b, c: cc.move_card(
            b, c, card_id, column_id, before_id=before_id, after_id=after_id, index=index),
            expected_version)

    def delete_card(self, board_id: str, actor: str, card_id: str,
                    expected_version: int | None = None) -> Outcome:
        return self.run(board_id, actor, lambda b, c: cc.delete_card(b, c, card_id),
                        expected_version)

    def toggle_done(self, board_id: str, actor: str, card_id: str,
                    expected_version: int | None = None) -> Outcome:
        return self.run(board_id, actor, lambda b, c: cc.toggle_done(b, c, card_id),
                        expected_version)
