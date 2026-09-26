"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from importlib.metadata import distribution
from importlib.util import find_spec

from auditcore_kanban import (
    BoardService,
    CardFilter,
    InMemoryBoardStore,
    board_schema,
    dumps,
    import_workspace,
    loads,
    rank_between,
    spread_ranks,
)
from auditcore_kanban.rest import KanbanApi


def main() -> None:
    package = distribution("auditcore_kanban")
    assert package.version == "0.1.1"
    assert [r for r in package.requires or [] if "extra ==" not in r] == []
    assert find_spec("auditcore") is None
    assert rank_between(None, None) == "V" and spread_ranks(3) == ["F", "V", "k"]
    assert board_schema()["properties"]
    service = BoardService(InMemoryBoardStore(), clock=lambda: "2026-09-25T12:00:00+00:00")
    api = KanbanApi(service)
    created = api.handle(
        "POST",
        "/boards",
        user_id="u1",
        body={"id": "b1", "title": "Prüfung", "template": "vorhabenpruefung"},
    )
    assert created.status == 201
    card = api.handle("POST", "/boards/b1/cards", user_id="u1", body={"title": "Belege"})
    moved = api.handle(
        "POST",
        f"/boards/b1/cards/{card.body['card']['id']}/move",  # type: ignore[index,call-overload]
        user_id="u1",
        body={"column_id": "pruefung"},
    )
    assert moved.status == 200
    assert api.handle("GET", "/boards/b1", user_id="u9").status == 404
    board, _ = service.get_board("b1", "u1")
    assert loads(dumps(board)) == board
    assert [c.title for c in service.find_cards("b1", "u1", CardFilter(query="beleg"))] == [
        "Belege"
    ]
    legacy = import_workspace(
        {"id": "p", "owner_user_id": 1},
        [{"id": "t", "title": "T", "status": "offen", "position": 1}],
    )
    assert legacy.cards[0].rank == "V"
    print("auditcore_kanban installed smoke PASS", board.version)


if __name__ == "__main__":
    main()
