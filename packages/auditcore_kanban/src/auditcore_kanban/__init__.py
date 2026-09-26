"""Framework-free Kanban domain: boards, columns, cards, ranks, rules, rights, events.

Contract ``auditcore_kanban.board/1``; see README and docs/kanban/rest-api.md.
"""

from .board_commands import (
    configure_columns,
    create_board,
    respread_column,
    revoke_share,
    share_board,
    update_board,
)
from .commands import (
    CommandResult,
    Context,
    create_card,
    delete_card,
    move_card,
    place,
    resolve_slot,
    toggle_done,
    update_card,
)
from .errors import ALLOWED, STATUS_BY_CODE, Decision, JsonObject, JsonValue, KanbanError
from .events import BoardEvent, Change, EventLog, InMemoryEventLog, JsonLinesEventLog, utc_now
from .filtering import CardFilter, deadline_state, filter_cards, group_by_value, matches
from .legacy import export_board_columns, export_workspace_tasks, import_workspace
from .model import (
    DEFAULT_COLUMNS,
    PERMISSIONS,
    PRIORITIES,
    Attachment,
    Board,
    Card,
    CardLink,
    ChecklistItem,
    Column,
    Label,
    Share,
    TransitionPolicy,
    column_for_status,
    done_column,
    first_column,
)
from .permissions import ROLE_ACTIONS, Action, authorize, check_revoke, check_share, role_of
from .rank import DIGITS, is_valid_rank, rank_between, spread_ranks
from .rules import check_capacity, check_move, check_transition, movable_targets, wip_states
from .serialization import (
    SCHEMA_VERSION,
    board_from_json,
    board_schema,
    board_to_json,
    dumps,
    loads,
)
from .service import BoardService, Outcome
from .stats import board_stats, percent
from .storage import BoardStore, FileSystemBoardStore, InMemoryBoardStore
from .templates import TEMPLATES, BoardTemplate, template
from .validation import DEFAULT_LIMITS, Limits, validate_columns

__version__ = "0.1.1"

__all__ = [
    "ALLOWED",
    "DEFAULT_COLUMNS",
    "DEFAULT_LIMITS",
    "DIGITS",
    "PERMISSIONS",
    "PRIORITIES",
    "ROLE_ACTIONS",
    "SCHEMA_VERSION",
    "STATUS_BY_CODE",
    "TEMPLATES",
    "Action",
    "Attachment",
    "Board",
    "BoardEvent",
    "BoardService",
    "BoardStore",
    "BoardTemplate",
    "Card",
    "CardFilter",
    "CardLink",
    "Change",
    "ChecklistItem",
    "Column",
    "CommandResult",
    "Context",
    "Decision",
    "EventLog",
    "FileSystemBoardStore",
    "InMemoryBoardStore",
    "InMemoryEventLog",
    "JsonLinesEventLog",
    "JsonObject",
    "JsonValue",
    "KanbanError",
    "Label",
    "Limits",
    "Outcome",
    "Share",
    "TransitionPolicy",
    "authorize",
    "board_from_json",
    "board_schema",
    "board_stats",
    "board_to_json",
    "check_capacity",
    "check_move",
    "check_revoke",
    "check_share",
    "check_transition",
    "column_for_status",
    "configure_columns",
    "create_board",
    "create_card",
    "deadline_state",
    "delete_card",
    "done_column",
    "dumps",
    "export_board_columns",
    "export_workspace_tasks",
    "filter_cards",
    "first_column",
    "group_by_value",
    "import_workspace",
    "is_valid_rank",
    "loads",
    "matches",
    "movable_targets",
    "move_card",
    "percent",
    "place",
    "rank_between",
    "resolve_slot",
    "respread_column",
    "revoke_share",
    "role_of",
    "share_board",
    "spread_ranks",
    "template",
    "toggle_done",
    "update_board",
    "update_card",
    "utc_now",
    "validate_columns",
    "wip_states",
]
