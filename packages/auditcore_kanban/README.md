# auditcore_kanban

Framework-freies Kanban-Domänenmodell für Anwendungen der FlowAudit-Familie.
Vorbild ist das Workspace-Board aus `audit_designer`; das Auftrags-Kanban aus
`cockpit` ist als Vorlage mit Statusabbildung und gesperrten Übergängen
abgebildet. Laufzeit: nur die Standardbibliothek.

```bash
pip install auditcore_kanban==0.1.0              # Kern
pip install 'auditcore_kanban[ui]==0.1.0'        # + Starlette-ASGI-App
pip install 'auditcore_kanban[fastapi]==0.1.0'   # + FastAPI-Router
```

- **Modell** (`model`): `Board`, `Column` (Farbe, WIP-Limit, `done`,
  Status-Aliase), `Card` (Titel, Beschreibung, Priorität hoch/mittel/niedrig,
  Tags, Zuständige, Frist, Farbe, Bild, Badge, Checkliste, Verknüpfungen z. B.
  `notebook-page`, Anhang-Metadaten, `extra` für App-Felder), `Label`, `Share`,
  `TransitionPolicy`. Alles unveränderlich (`frozen`).
- **Reihenfolge** (`rank`): Base-62-Rangschlüssel; Einfügen zwischen zwei Karten
  ändert nur die bewegte Karte. `rank_between`, `spread_ranks`.
- **Regeln** (`rules`): freie oder eingeschränkte Übergänge, gesperrte Spalten,
  feste Reihenfolge, WIP-Limits (`block` oder `warn`).
- **Rechte** (`permissions`): Rollen `owner`/`edit`/`read`, geerbte Freigaben
  (z. B. Notizbuch), deklarative Aktionstabelle; Unbeteiligte sehen nichts.
- **Befehle** (`commands`, `board_commands`): reine Funktionen, die Rechte,
  Validierung, Übergang und WIP prüfen und `(neues Board, Änderungen)` liefern.
- **Service** (`service.BoardService`): Laden, optimistische Versionsprüfung,
  Speichern, Ereignisprotokoll. Speicher-Port `BoardStore` mit
  `InMemoryBoardStore` und `FileSystemBoardStore` (atomar).
- **JSON** (`serialization`): Format `auditcore_kanban.board/1`, JSON-Schema
  `schemas/board.schema.json`.
- **Altdaten** (`legacy`): Import/Export des audit_designer-Formats
  (`board_columns` + Tasks mit Position).
- **Vorlagen** (`templates`): Standard, Vorhabenprüfung, Sprint, Einfach,
  Systemprüfung, Teamplanung, Jahresplanung, Aufträge (cockpit).
- **REST** (`rest`): framework-freier `KanbanApi`-Handler nach
  [`docs/kanban/rest-api.md`](../../docs/kanban/rest-api.md);
  `rest.asgi.create_app` (Extra `ui`) und `rest.fastapi_router.create_router`
  (Extra `fastapi`). Die eingebettete Oberfläche folgt mit `@flowaudit/ui`;
  `create_app(..., ui_directory=…)` ist der vorbereitete Einhängepunkt.

```python
from auditcore_kanban import BoardService, FileSystemBoardStore

service = BoardService(FileSystemBoardStore(Path("boards")))
board = service.create_board("u1", "Vorhabenprüfung 2026", template_key="vorhabenpruefung").board
card = service.create_card(board.id, "u1", {"title": "Belegliste anfordern"}).result.card
service.move_card(board.id, "u1", card.id, "pruefung", index=0)
```

Python und `@flowaudit/kanban-core` (TypeScript) entscheiden identisch; die
gemeinsamen Fälle stehen in `tests/fixtures/parity/`
([Format](../../docs/kanban/parity-fixtures.md)). Das Verhalten des Originals
ist in `tests/fixtures/legacy_kanban_observed.json` und
`tests/fixtures/cockpit_rules_observed.json` festgehalten; bewusste
Abweichungen: [docs/behavior-changes.md](docs/behavior-changes.md).
Funktionsinventur: [docs/kanban/paritaet-audit-designer.md](../../docs/kanban/paritaet-audit-designer.md).

Herkunft und Lizenz: siehe `NOTICE` und `provenance.json` (MIT, Freigabe des
Rechteinhabers vom 22.09.2026 für die Bibliothek). Debian-Paket:
`python3-auditcore-kanban`.
