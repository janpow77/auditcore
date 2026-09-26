# REST-Vertrag `auditcore_kanban` (Version 1)

Umsetzung: `auditcore_kanban.rest.KanbanApi` (framework-frei), eingebunden über
`rest.asgi.create_app` (Starlette, Extra `ui`) oder
`rest.fastapi_router.create_router` (FastAPI, Extra `fastapi`). Pfade sind
relativ zum Einhängepunkt der Anwendung (z. B. `/api/kanban`). Alle Körper sind
JSON (UTF-8). Board-Dokumente haben die Form `auditcore_kanban.board/1`
([Schema](../../packages/auditcore_kanban/src/auditcore_kanban/schemas/board.schema.json),
[Beispiel](parity-fixtures.md#board-json-auditcore_kanbanboard1)).

## Identität

Die Bibliothek authentifiziert nicht. Der Consumer liefert die Nutzer-ID
(Zeichenkette): Starlette über `identity(headers) -> str | None`, FastAPI über
eine eigene Abhängigkeit (`current_user`, z. B. `get_current_user`). Ohne
Nutzer: `401 UNAUTHENTICATED`.

## Versionen und Nebenläufigkeit

Jedes Board hat `version` (ganzzahlig, +1 je Änderung). Antworten mit einem
Board tragen `ETag: "<version>"`. Schreibende Aufrufe dürfen die erwartete
Version als `expected_version` im Körper oder als `If-Match: "<version>"`
mitgeben; weicht sie ab: `409 VERSION_CONFLICT`. Ohne Angabe gewinnt der
letzte Schreiber, die Speicherung selbst bleibt atomar versionsgeprüft.

## Endpunkte

| Methode | Pfad | Körper | Erfolg | Recht |
|---|---|---|---|---|
| GET | `/templates` | – | 200 `{"templates":[{key,name,icon,description,columns}]}` | angemeldet |
| GET | `/boards?archived=true` | – | 200 `{"boards":[{id,title,icon,owner_id,pinned,archived,version,updated_at,role,stats}]}` (angeheftet zuerst, dann zuletzt geändert) | sichtbare Boards |
| POST | `/boards` | `{title?,icon?,template?,id?}` | 201 `{board,role,stats}` | angemeldet (wird Eigentümer) |
| GET | `/boards/{id}` | – | 200 `{board,role,stats}` | read |
| PATCH | `/boards/{id}` | `{title?,icon?}` (edit), `{pinned?,archived?}` (owner), `expected_version?` | 200 `{board,role,stats}` | s. Körper |
| DELETE | `/boards/{id}` | – | 204 | owner |
| PUT | `/boards/{id}/columns` | `{columns:[{id,label,color?,wip_limit?,done?,status_aliases?}], transitions?:{mode,allowed,locked_columns,fixed_order_columns}, expected_version?}` | 200 `{board,role,stats}`; Karten entfernter Spalten ans Ende der ersten Spalte | owner |
| GET | `/boards/{id}/cards?q=&priority=&tag=&assignee=&column=&due=&today=` | – | 200 `{"cards":[…]}` in Board-Reihenfolge; Listen kommagetrennt; `due` ∈ none, overdue, due_soon, later | read |
| POST | `/boards/{id}/cards` | Kartenfelder + `column_id?`, `index?`/`before_id?`/`after_id?`, `id?`, `expected_version?` | 201 Änderungsantwort | edit |
| PATCH | `/boards/{id}/cards/{card}` | Kartenfelder; `column_id` verschiebt ans Spaltenende | 200 Änderungsantwort | edit |
| DELETE | `/boards/{id}/cards/{card}` | `expected_version?` | 200 Änderungsantwort | edit |
| POST | `/boards/{id}/cards/{card}/move` | `{column_id, before_id?\|after_id?\|index?, expected_version?}` | 200 Änderungsantwort | edit |
| POST | `/boards/{id}/cards/{card}/toggle-done` | – | 200 Änderungsantwort (erledigt ↔ erste Spalte) | edit |
| GET | `/boards/{id}/shares` | – | 200 `{"shares":[{user_id,permission,shared_by,created_at}]}` | owner |
| PUT | `/boards/{id}/shares/{user}` | `{permission: "read"\|"edit"}` | 200 Änderungsantwort (anlegen oder ändern) | owner |
| DELETE | `/boards/{id}/shares/{user}` | – | 200 Änderungsantwort | owner oder der Empfänger selbst |
| GET | `/boards/{id}/events?since=<seq>` | – | 200 `{"events":[{seq,board_id,version,kind,actor,at,card_id,data}]}` | read |

Kartenfelder: `title`, `description`, `priority` (hoch|mittel|niedrig),
`tags`, `assignees`, `due` (ISO-Datum/-Zeitpunkt, `""`/`null` löscht),
`color`, `image`, `badge` (`""`/`null` löscht), `checklist` `[{text,done}]`,
`links` `[{kind,target,title?}]`, `attachments` `[{id,filename,mime_type?,size?}]`,
`extra` (Objekt, ersetzt das bisherige).

Änderungsantwort:

```json
{"version": 7, "card": {…}|null, "changed_cards": [{…}], "warnings": ["WIP_LIMIT_REACHED"],
 "events": [{"seq": 12, "kind": "card.moved", "card_id": "…", "data": {"from": "offen",
  "to": "in_arbeit", "rank": "V", "index": 0}, …}]}
```

`changed_cards` enthält Karten, deren Rang durch eine Neuverteilung der Spalte
geändert wurde (nur bei doppelten Rängen aus Altdaten).

Ereignisarten: `board.created`, `board.updated`, `board.configured`,
`board.deleted`, `card.created`, `card.updated`, `card.moved`, `card.deleted`,
`column.rebalanced`, `share.created`, `share.updated`, `share.revoked`.

## Fehler

Körper immer `{"error": {"code": "…", "message": "…"}}` (Meldung deutsch).

| Status | Codes |
|---|---|
| 400 | `VALIDATION_ERROR`, `INVALID_PERMISSION`, `SELF_SHARE`, `UNKNOWN_COLUMN` |
| 401 | `UNAUTHENTICATED` |
| 403 | `FORBIDDEN` (Board sichtbar, Recht fehlt) |
| 404 | `NOT_VISIBLE` (Board fehlt oder unsichtbar – nicht unterscheidbar), `CARD_NOT_FOUND`, `SHARE_NOT_FOUND`, `USER_NOT_FOUND`, `ROUTE_NOT_FOUND` |
| 405 | `METHOD_NOT_ALLOWED` |
| 409 | `TRANSITION_NOT_ALLOWED`, `COLUMN_LOCKED`, `ORDER_FIXED`, `WIP_LIMIT_REACHED`, `VERSION_CONFLICT`, `BOARD_EXISTS` |
| 422 | `INVALID_REQUEST` (Typfehler, ungültiges JSON, falsche Abfrageparameter), `INVALID_DOCUMENT` |

## Eingebettete Oberfläche

`create_app(service, identity, ui_directory=Path(...))` liefert die
Oberfläche unter `/ui/` aus. Assets werden erst mit `@auditcore/ui`
(`<flowaudit-kanban-board>`) mitgeliefert; bis dahin bleibt der Parameter leer.
