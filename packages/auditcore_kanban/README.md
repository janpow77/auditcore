# auditcore_kanban

## Zweck

Framework-freies Kanban-Domänenmodell mit Rang-Schlüsseln, Übergangsregeln, WIP-Limits, Rechten, Ereignisprotokoll und einem REST-Vertrag für die Anwendungen der FlowAudit-Familie.

Vorbild ist das Workspace-Board aus `audit_designer`; das Auftrags-Kanban aus
`cockpit` ist als Vorlage mit Statusabbildung und gesperrten Übergängen
enthalten. Die Oberfläche liefert `@flowaudit/ui`, die gleiche Logik in
TypeScript `@flowaudit/kanban-core`. Anwendungen behalten Authentifizierung,
Benutzerverwaltung und Datenbank.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install auditcore_kanban \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Version 0.1.0 ist noch nicht veröffentlicht; nach dem nächsten Release steht
sie mit Direkt-URL und Hash unter
`https://janpow77.github.io/auditcore/simple/auditcore-kanban/`. Muster für eine
hashgebundene `requirements.txt`:

```text
auditcore_kanban @ https://github.com/janpow77/auditcore/releases/download/v<release>/auditcore_kanban-0.1.0-py3-none-any.whl#sha256=<sha256 aus dem Index>
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-kanban
```

Extras: `[ui]` – Starlette-ASGI-App `rest.asgi.create_app`; `[fastapi]` –
FastAPI-Router `rest.fastapi_router.create_router`; `[dev]` – Test- und
Prüfwerkzeuge.

## Schnellstart

```python
from auditcore_kanban import BoardService, InMemoryBoardStore, KanbanError

service = BoardService(InMemoryBoardStore())
board = service.create_board(
    "u1", "Vorhabenprüfung 2026", template_key="vorhabenpruefung"
).board
card = service.create_card(board.id, "u1", {"title": "Belegliste anfordern"}).result.card
service.move_card(board.id, "u1", card.id, "pruefung", index=0)

current, role = service.get_board(board.id, "u1")
assert role == "owner" and current.version == 3

# Unbeteiligte sehen das Board nicht.
try:
    service.create_card(board.id, "fremd", {"title": "x"})
except KanbanError as error:
    assert error.code == "NOT_VISIBLE"
else:
    raise AssertionError("KanbanError erwartet")
```

```pycon
>>> [column.id for column in current.columns]
['auswahl', 'pruefung', 'entwurf', 'kontradiktorisch', 'abschluss', 'followup']
>>> [(c.title, c.column_id) for c in current.cards]
[('Belegliste anfordern', 'pruefung')]
```

Dauerhaft speichert `FileSystemBoardStore(Path("boards"))` (atomar, eine
Datei je Board).

## API-Überblick

- **Modell** (`model`): `Board`, `Column` (Farbe, WIP-Limit, `done`,
  Status-Aliase), `Card` (Titel, Beschreibung, Priorität, Tags, Zuständige,
  Frist, Farbe, Bild, Badge, Checkliste, Verknüpfungen, Anhang-Metadaten,
  `extra`), `Label`, `Share`, `TransitionPolicy` – alles unveränderlich.
- **Reihenfolge** (`rank`): Base-62-Rangschlüssel, `rank_between`, `spread_ranks`.
- **Regeln** (`rules`), **Rechte** (`permissions`), **Befehle**
  (`commands`, `board_commands`: reine Funktionen → neues Board plus Änderungen).
- **Service** (`service.BoardService`): Laden, optimistische Versionsprüfung,
  Speichern, Ereignisprotokoll; Speicher-Port `BoardStore`.
- **JSON** (`serialization`, Format `auditcore_kanban.board/1`, Schema
  `schemas/board.schema.json`), **Altdaten** (`legacy`: audit_designer-Format),
  **Vorlagen** (`templates`), **REST** (`rest.KanbanApi`, Vertrag
  [docs/kanban/rest-api.md](../../docs/kanban/rest-api.md)).

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_kanban.__all__` (84):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `ALLOWED` | Konstante | – | `errors` |
| `DEFAULT_COLUMNS` | Konstante | audit_designer DEFAULT_COLUMNS (workspace.py) – used when a board has no own columns. | `model` |
| `DEFAULT_LIMITS` | Konstante | – | `validation` |
| `DIGITS` | Konstante | – | `rank` |
| `PERMISSIONS` | Konstante | – | `model` |
| `PRIORITIES` | Konstante | – | `model` |
| `ROLE_ACTIONS` | Konstante | Declarative role table; ``configure``, ``share``, ``delete_board``, ``pin`` are owner-only. | `permissions` |
| `SCHEMA_VERSION` | Konstante | – | `serialization` |
| `STATUS_BY_CODE` | Konstante | HTTP status per error code; the REST contract (docs/kanban/rest-api.md) uses this table. | `errors` |
| `TEMPLATES` | Konstante | – | `templates` |
| `Action` | Aufzählung | – | `permissions` |
| `Attachment` | Datenklasse | Attachment metadata only; the bytes stay with the consumer. | `model` |
| `Board` | Datenklasse | – | `model` |
| `BoardEvent` | Datenklasse | – | `events` |
| `BoardService` | Klasse | Framework-free use cases on top of a :class:`BoardStore`. | `service` |
| `BoardStore` | Protokoll | – | `storage` |
| `BoardTemplate` | Datenklasse | – | `templates` |
| `Card` | Datenklasse | – | `model` |
| `CardFilter` | Datenklasse | All given criteria must hold; an empty criterion matches everything. | `filtering` |
| `CardLink` | Datenklasse | Reference to something outside the board, e.g. kind ``notebook-page``. | `model` |
| `Change` | Datenklasse | What a command changed; the service turns it into a :class:`BoardEvent`. | `events` |
| `ChecklistItem` | Datenklasse | – | `model` |
| `Column` | Datenklasse | A board column; ``status_aliases`` map external statuses onto it (cockpit). | `model` |
| `CommandResult` | Datenklasse | – | `commands` |
| `Context` | Datenklasse | Who acts, when, with which inherited grants and limits. | `commands` |
| `Decision` | Datenklasse | Outcome of a rule check; ``warnings`` carries non-blocking codes (WIP warn mode). | `errors` |
| `EventLog` | Protokoll | – | `events` |
| `FileSystemBoardStore` | Klasse | One JSON document per board in ``root``; writes are atomic (temp file + rename). | `storage` |
| `InMemoryBoardStore` | Klasse | Thread-safe store for tests, demos and single-process consumers. | `storage` |
| `InMemoryEventLog` | Klasse | Process-local log; sequence numbers are global and strictly increasing. | `events` |
| `JsonLinesEventLog` | Klasse | Log persisted as one JSON object per line (appended, never rewritten). | `events` |
| `JsonObject` | Typalias | – | `errors` |
| `JsonValue` | Typalias | – | `errors` |
| `KanbanError` | Ausnahme | A rejected operation with a stable machine code and a German message. | `errors` |
| `Label` | Datenklasse | – | `model` |
| `Limits` | Datenklasse | Defaults are the constants of the original backend. | `validation` |
| `Outcome` | Datenklasse | Result of a service call: the saved board, the command result and its events. | `service` |
| `Share` | Datenklasse | – | `model` |
| `TransitionPolicy` | Datenklasse | Movement rules. | `model` |
| `authorize` | Funktion | Decision for one action of one user on one board. | `permissions` |
| `board_from_json` | Funktion | Parse and structurally check a board document. | `serialization` |
| `board_schema` | Funktion | The packaged JSON Schema of the board document. | `serialization` |
| `board_stats` | Funktion | ``total``, ``by_column``, ``done`` and ``progress`` (0–100). | `stats` |
| `board_to_json` | Funktion | Complete board document; cards in board order for stable output. | `serialization` |
| `check_capacity` | Funktion | Can one more card enter ``column_id``? Warn mode allows it with a warning. | `rules` |
| `check_move` | Funktion | Full rule set for moving ``card`` into ``target`` (transition, then WIP). | `rules` |
| `check_revoke` | Funktion | Owner revokes every share; a recipient may remove their own share. | `permissions` |
| `check_share` | Funktion | Owner-only sharing with a valid permission and never with oneself. | `permissions` |
| `check_transition` | Funktion | Column change rule without capacity (``source == target`` is a reorder). | `rules` |
| `column_for_status` | Funktion | Column whose id or alias equals an external status (cockpit ``spalteVon``). | `model` |
| `configure_columns` | Funktion | Replace the column set (owner only); cards of removed columns move to the first column. | `board_commands` |
| `create_board` | Funktion | New board owned by the acting user (default columns unless a template is given). | `board_commands` |
| `create_card` | Funktion | New card in ``column_id`` (default first column), appended unless a slot is given. | `commands` |
| `deadline_state` | Funktion | ``none``, ``overdue``, ``due_soon`` (≤ 3 days) or ``later`` (WorkspaceTaskCard). | `filtering` |
| `delete_card` | Funktion | – | `commands` |
| `done_column` | Funktion | First column flagged ``done``, otherwise the last column (audit_designer). | `model` |
| `dumps` | Funktion | – | `serialization` |
| `export_board_columns` | Funktion | ``board_columns`` value of the page (id, label, color). | `legacy` |
| `export_workspace_tasks` | Funktion | Task dicts with ``status`` = column and ``position`` 1..N per column. | `legacy` |
| `filter_cards` | Funktion | Matching cards in board order (columns, then rank). | `filtering` |
| `first_column` | Funktion | First column (target for removed columns and for re-opening cards). | `model` |
| `group_by_value` | Funktion | Group items into one bucket per option (useDbKanban). | `filtering` |
| `import_workspace` | Funktion | Board from ``VpaiPage.to_dict()``, task dicts and share rows. | `legacy` |
| `is_valid_rank` | Funktion | True for a non-empty key over the alphabet that does not end with ``0``. | `rank` |
| `loads` | Funktion | – | `serialization` |
| `matches` | Funktion | True if ``card`` satisfies every criterion. | `filtering` |
| `movable_targets` | Funktion | Columns the card may currently be moved into (keyboard/menu helpers). | `rules` |
| `move_card` | Funktion | Move into ``column_id`` before/after a card or at ``index`` (default: end). | `commands` |
| `percent` | Funktion | Rounded percentage, half up (same as JavaScript ``Math.round``). | `stats` |
| `place` | Funktion | Rank for a card at ``slot``; rebalances the column only if ranks collide. | `commands` |
| `rank_between` | Funktion | Key strictly between ``before`` and ``after``; None means open end. | `rank` |
| `resolve_slot` | Funktion | Insert position among ``siblings`` (default: end; index is clamped). | `commands` |
| `respread_column` | Funktion | Replace the ranks of one column by evenly spaced keys (keeps the order). | `board_commands` |
| `revoke_share` | Funktion | Owner revokes any share, a recipient their own. | `board_commands` |
| `role_of` | Funktion | Role of ``user_id``: owner, the board's own share, else an inherited grant. | `permissions` |
| `share_board` | Funktion | Grant or update (upsert) a share; the owner is the only one who may share. | `board_commands` |
| `spread_ranks` | Funktion | ``count`` evenly spaced increasing keys (import, rebalancing). | `rank` |
| `template` | Funktion | – | `templates` |
| `toggle_done` | Funktion | Done column -> top of the first column; otherwise -> end of the done column. | `commands` |
| `update_board` | Funktion | Rename (owner, edit), pin/archive (owner only). | `board_commands` |
| `update_card` | Funktion | Change card fields; a different ``column_id`` moves the card to that column's end. | `commands` |
| `utc_now` | Funktion | Default clock: UTC ISO timestamp with seconds precision. | `events` |
| `validate_columns` | Funktion | Column set in the original check order: count, unique ids, then each column. | `validation` |
| `wip_states` | Funktion | Current load against the limit for every column. | `rules` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_kanban.board_commands` | Pure board-level commands: create, rename/pin, configure columns, share, revoke. |
| `auditcore_kanban.card_fields` | Parse JSON-like card fields (REST bodies, Python callers) into validated values. |
| `auditcore_kanban.commands` | Pure card commands: each checks rights, validation, transitions and WIP and returns the new board plus the changes (no I/O). |
| `auditcore_kanban.errors` | Error and decision contract shared by commands, the service and the REST handler. |
| `auditcore_kanban.events` | Append-only event log of board changes. |
| `auditcore_kanban.filtering` | Search, filters, deadline state and grouping of records by a property. |
| `auditcore_kanban.legacy` | Bridge to the audit_designer workspace format (``vpai_pages`` + ``vpai_workspace_tasks``). |
| `auditcore_kanban.model` | Immutable domain model: board, column, card, label, share and transition policy. |
| `auditcore_kanban.permissions` | Access model as pure logic: who may read, move, edit, configure and share a board. |
| `auditcore_kanban.rank` | Rank keys: ordered strings that allow inserting between two cards without renumbering. |
| `auditcore_kanban.rest` | REST contract: framework-free handler plus optional Starlette/FastAPI adapters. |
| `auditcore_kanban.rules` | Movement rules: column transitions, locked columns, fixed order and WIP limits. |
| `auditcore_kanban.serialization` | JSON (de)serialization of boards; format ``auditcore_kanban.board/1``. |
| `auditcore_kanban.service` | Application service: load, check version, run a pure command, save, log events. |
| `auditcore_kanban.stats` | Counts per column and progress (done column, else last column – audit_designer). |
| `auditcore_kanban.storage` | Storage port with an in-memory and a file-system implementation. |
| `auditcore_kanban.templates` | Board templates: the seven WorkspaceSidebar templates of audit_designer and the cockpit job board (status aliases, restricted transitions, locked column). |
| `auditcore_kanban.validation` | Input validation with the limits and German messages of audit_designer (workspace.py). |
<!-- api-overview:end -->

## Profile und Konfiguration

Vorlagen (`templates`): Standard, Vorhabenprüfung, Sprint, Einfach,
Systemprüfung, Teamplanung, Jahresplanung (aus audit_designer) und Aufträge
(cockpit). Grenzen über `Limits` mit den Werten des Originals (Titel 300,
Beschreibung 10 000, 20 Tags à 80 Zeichen, 1–10 Spalten, Badge 20 Zeichen,
Checkliste 200). WIP-Modus je Board `block` oder `warn`; Übergänge `free` oder
`restricted` mit gesperrten Spalten und fester Reihenfolge.

`BoardService` nimmt `events` (Ereignisprotokoll, Speicher oder JSON Lines),
`clock`, `new_id`, `limits`, `inherited_grants` (geerbte Freigaben, z. B. eines
Notizbuchs) und `user_exists` (Teilen mit unbekannten Nutzern → 404) entgegen.
`create_app(service, identity, ui_directory=…)` und
`create_router(service, current_user)` binden die Identität der Anwendung ein.

## Herkunft und Charakterisierung

Neuimplementierung gegen charakterisierte Verträge: das ausgeführte Backend des
audit_designer-Workspace-Boards (Commit `2c726f3c`, 77 Fälle,
`tests/fixtures/legacy_kanban_observed.json`) und die per Node ausgeführten
cockpit-Regeln (Commit `df203d4c`, `tests/fixtures/cockpit_rules_observed.json`).
Grenzwerte, deutsche Meldungen, Standardspalten und Vorlagen sind übernommen,
der Code neu geschrieben. Python und `@flowaudit/kanban-core` entscheiden
identisch; gemeinsame Fälle in `tests/fixtures/parity/`
([Format](../../docs/kanban/parity-fixtures.md)). Funktionsinventur:
[docs/kanban/paritaet-audit-designer.md](../../docs/kanban/paritaet-audit-designer.md).

## Bewusste Verhaltensabweichungen

Zehn Abweichungen mit beobachtetem Altwert in
[docs/behavior-changes.md](docs/behavior-changes.md), unter anderem:
Rang-Schlüssel statt Umnummerieren der Positionen (B1), Umsortieren nur über
`move_card` (B2), Karten entfernter Spalten ans Ende der ersten Spalte (B3),
leere Frist gleich „keine Frist“ (B4), `FORBIDDEN` statt 404 für Beteiligte
ohne Recht (B5), Einfügen an Index/vor/nach einer Karte (B6), deutsche
Meldungen (B7), Badge-Länge vor der Speicherung geprüft (B8), getrimmter
Suchtext (B9), Statistik über alle Spalten (B10).

## Abhängigkeiten

Python ≥ 3.11, zur Laufzeit nur die Standardbibliothek. Optional
`starlette>=0.26` (`[ui]`) und `fastapi>=0.92` (`[fastapi]`). Keine
Abhängigkeit von der Plattform `auditcore` oder anderen Fachpaketen.

## Sicherheit und Datenschutz

Karten enthalten Namen von Zuständigen und freie Texte der Anwendung –
personenbezogene Daten, deren Speicherung und Löschung die Anwendung
verantwortet. Die Rechteprüfung (owner/edit/read, geerbte Freigaben) läuft in
jedem Befehl; Unbeteiligte erhalten `NOT_VISIBLE`. Authentifizierung ist nicht
Teil des Pakets: die REST-Anbindung übernimmt die Identität der Anwendung.
`FileSystemBoardStore` akzeptiert nur dateinamensichere Board-IDs (keine
Pfadtrenner, keine Punkte) und schreibt atomar. Eingaben werden vor dem
Speichern gegen die Grenzen validiert.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Freigabe des Rechteinhabers vom 22.09.2026 für die
Bibliothek; audit_designer und cockpit behalten ihre eigene Lizenzierung.
Quelldateien mit Blob-SHAs: `provenance.json`; Zuschreibung: `NOTICE`.
Optionale Extras nutzen Starlette (BSD-3-Clause) und FastAPI (MIT).

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
