# Paritätsinventur Kanban: audit_designer und cockpit → auditcore

Stand 25.09.2026. Quellen (GitHub-verifiziert, Blob-SHAs in
`packages/auditcore_kanban/provenance.json`):

- **audit_designer** `2c726f3c1481775cd34aeaa83f87137d6ab12ffe`: Workspace-Board
  (`frontend/src/components/workspace/{WorkspaceBoard,WorkspaceTaskCard,WorkspaceTaskDetail,BoardSettingsDialog,BoardShareDialog,WorkspaceSidebar}.vue`,
  `composables/useWorkspace.ts`, `types/workspace.ts`,
  `composables/notebook/useDbKanban.ts`, `backend/app/api/vpai_notebook/workspace.py`,
  `backend/app/modules/vp_ai/utils/user_scoped.py`, Modelle `VpaiPage`,
  `VpaiWorkspaceTask`, `VpaiPageShare`, `VpaiNotebookShare`, Migration 049).
  Eigene Tests für das Board gibt es im Original nicht; das Backend wurde für
  diese Inventur ausgeführt (77 Fälle, `tests/fixtures/legacy_kanban_observed.json`).
- **cockpit** `df203d4c33e786eb8a8ad3fe53b3b7eb9241d406`: Auftrags-Kanban
  (`frontend/src/views/KanbanView.vue`, `components/kanban/{labels.ts,AuftragSpalte.vue,AuftragKarte.vue}`,
  `src/cockpit/routes/auftraege.py`, `services/auftraege.py`); `spalteVon` und
  `darfVerschieben` per node ausgeführt (`tests/fixtures/cockpit_rules_observed.json`).

Ziele: **Py** = `auditcore_kanban` (Python), **Core** = `@auditcore/kanban-core`
(TypeScript, gleiche Regeln, Paritätsfixtures), **UI** = Komponente in
`@auditcore/ui` (Vue 3 + `<flowaudit-kanban-board>` + React-Wrapper),
**Port** = Anbindung durch die Anwendung (Speicher-/Rechte-/Datei-Port).

Status: **übernommen** (in Py umgesetzt und getestet), **Core** (Regel in Py
fertig, TS-Spiegel in `@auditcore/kanban-core`), **UI übernommen** (Oberfläche in
`@auditcore/ui`, PR #84), **Port** (bleibt bei der Anwendung, Schnittstelle vorhanden),
**geändert Bx** (bewusste Abweichung, `packages/auditcore_kanban/docs/behavior-changes.md`).

## 1. Board, Spalten, Vorlagen

| Funktion (Original) | Ziel | Status |
|---|---|---|
| Board = Notizbuchseite `page_type="workspace"` (Titel, Icon, angeheftet, archiviert, Eigentümer) | Py `Board`; Notizbuchbezug über `extra.legacy_notebook_id` und geerbte Freigaben | übernommen |
| Standardspalten Offen/In Arbeit/Erledigt mit Farben `#7c3aed/#f59e0b/#10b981`, `board_columns = null` → Standard | Py `DEFAULT_COLUMNS` | übernommen |
| Eigene Spalten 1–10, ID `^[a-z0-9][a-z0-9_-]{0,49}$`, Label 1–80, eindeutige IDs, Trimmen | Py `validate_columns` (gleiche Reihenfolge und Meldungen) | übernommen (17 Fälle gegen Original) |
| Spalte entfernen → Karten in erste Spalte | Py `configure_columns` | geändert B3 (anhängen statt verzahnen) |
| Einstellungsdialog: Spalten hinzufügen („Neue Spalte“, max. 10), löschen (min. 1), per Drag-and-drop umsortieren, Label ändern, Farbe aus 8 Vorgaben oder eigenes Hex, Speichern nur bei Änderung und ohne leere Labels | UI `BoardSettings` + Core-Validierung | UI übernommen |
| Spalten-ID aus Label (`slugify`: Umlaute → ae/oe/ue/ss, `_2`…`_99`, Zufalls-ID) | Core `columnIdFromLabel` | Core |
| WIP-Limit je Spalte | Py `Column.wip_limit`, `rules.check_capacity`, Modus `block`/`warn` | neu, übernommen |
| „Erledigt“-Spalte | Py `Column.done`, sonst letzte Spalte (`done_column`) | übernommen |
| 7 Vorlagen der Seitenleiste (Standard, Vorhabenprüfung, Sprint, Einfach, Systemprüfung, Teamplanung, Jahresplanung) | Py `templates.TEMPLATES`, REST `/templates` | übernommen |
| Board-Titel inline umbenennen (Klick, Enter/Blur, Esc bricht ab, leer → alter Titel) | Py `update_board(title=…)` (owner, edit); UI Kopfzeile | Py/UI übernommen |
| Board löschen (Tasks kaskadiert), anheften | Py `delete_board`, `update_board(pinned=…)` (owner) | übernommen |

## 2. Karten

| Funktion (Original) | Ziel | Status |
|---|---|---|
| Titel (≤ 300 nach Trimmen, nicht leer), Beschreibung (≤ 10 000), Tags (≤ 20, je ≤ 80) | Py `validation`, gleiche Meldungen | übernommen (11 Fälle gegen Original) |
| Priorität hoch/mittel/niedrig, Standard mittel | Py `PRIORITIES` | übernommen (Meldung deutsch, B7) |
| Frist (ISO, `Z` erlaubt, `""` löscht beim Update) | Py `normalize_due` | übernommen; B4 für `""` beim Anlegen |
| Kartenfarbe, Hintergrundbild (Data-URI ≤ 2 MB im Frontend), `""` löscht | Py `color`/`image`; UI Farbwahl (10 Vorgaben, eigene Farbe), Textfarbe nach Luminanz | Py/UI übernommen |
| Badge (Frontend max. 10, Großbuchstaben; DB 20) mit Präfixfarben VP/SYS/SP/JKB/PRJ | Py `validate_badge` (≤ 20, B8); Core `badgeColor` | Py übernommen, Core |
| Checkliste `{text, done}` mit Fortschritt | Py `checklist`, `stats.checklist_progress` | übernommen |
| Dateianhänge (Base64-Upload, PDF-/Text-Extraktion, Speicherkontingent) | Py `attachments` (nur Metadaten); Bytes, Extraktion, Kontingent | Port |
| KI-Prompt erzeugen/kopieren/neu erzeugen (Ollama) | `extra.generated_prompt`, `extra.prompt_generated_at`; Aktion als Slot/Ereignis der UI | Port |
| Zuständige | Py `assignees` | neu |
| Verknüpfung zu Notizbuchseiten | Py `links` (`kind: "notebook-page"`) | neu |
| Karte: Prioritätsstreifen, Kurzbeschreibung (80 Zeichen), max. 3 Tags + „+n“, Checklistenzähler, Frist (überfällig rot mit „!“, ≤ 3 Tage gelb), Dateizahl, Prompt-Stern, Alter (neu/h/d/w/mo), erledigt durchgestrichen | Py `deadline_state`; Core `ageLabel`, `cardView`; UI `KanbanCard` | übernommen (Py, Core, UI) |
| Detailpanel: Badge, Titel, Status (fest 3 Knöpfe), Priorität, Frist, Beschreibung (wächst mit), Tags, Checkliste, Kartendesign, Dateien, Prompt, Zeitstempel; Löschen | UI `CardDetail` (Status aus den Board-Spalten statt fest 3) | UI übernommen |

## 3. Reihenfolge, Verschieben, Drag-and-drop

| Funktion (Original) | Ziel | Status |
|---|---|---|
| Position 1..N je Spalte, Neuanlage ans Ende | Py `rank` (Rang-Schlüssel), `create_card` | geändert B1 |
| Verschieben mit 1-basierter Position, Klemmung (0/negativ → Anfang, zu groß → Ende), Quell- und Zielspalte neu nummeriert | Py `move_card(index/before_id/after_id)` | übernommen (Reihenfolge = Original, 13 Fälle), B1 |
| Statuswechsel per Update → Ende der neuen Spalte | Py `update_card(column_id=…)` | übernommen |
| Update mit Position (Gleichstand nach Erstellzeit) | nur `move_card` | geändert B2 |
| Neue Karte: Position des Frontends wird verworfen | Py `create_card` Ende oder `index` | geändert B6 |
| Drag-and-drop zwischen Spalten (vuedraggable) | UI eigene Pointer-Events-Umsetzung (Maus/Stift/Touch), Vorschau, Ablegen vor/hinter Karte; vuedraggable/SortableJS (MIT) geprüft, verworfen | UI übernommen |
| Abhaken (Kreis auf der Karte): letzte Spalte ↔ erste Spalte oben | Py `toggle_done` | übernommen |
| Doppelte Ränge aus Altdaten | Py `place` verteilt die Spalte einmal neu (`column.rebalanced`) | neu |

## 4. Suche, Filter, Ansicht

| Funktion (Original) | Ziel | Status |
|---|---|---|
| Suche in Titel, Beschreibung, Tags (klein geschrieben) | Py `filtering.matches_query` (+ Badge, getrimmt) | übernommen, B9 |
| Prioritätsfilter | Py `CardFilter.priorities` | übernommen; zusätzlich Tags, Zuständige, Spalten, Fristzustand |
| Fortschritt erledigt/gesamt mit Prozent, Mini-Balken je Spalte, Zähler | Py `board_stats`, `percent` (= `Math.round`) | übernommen (Py/UI) |
| Seitenleisten-Statistik nur offen/in_arbeit/erledigt | Py `board_stats` je Spalte | geändert B10 |
| Vollbild (Route `/workspace/{id}/fullscreen`) | UI-Ereignis `fullscreen` | UI übernommen (Ereignis) / Port (Routing) |
| Lade- und Fehleranzeige, Nur-Lese-Banner „Geteilt von … – Nur Lesezugriff“ | UI | UI übernommen |
| Datenbankansicht `useDbKanban`: Gruppieren nach Select-Eigenschaft, führende Spalte „ohne Wert“, Ablegen setzt den Wert | Py `group_by_value`; Core `groupByValue`, `groupRecords`, `RecordPort`; UI `FaDbKanban` (`<flowaudit-db-kanban>`) | übernommen (Parität `group.json`) |

## 5. Tastatur und Barrierefreiheit

| Funktion (Original) | Ziel | Status |
|---|---|---|
| audit_designer: `N` neue Aufgabe in erster Spalte, `F` Vollbild, `Esc` schließt Detail (nicht in Eingabefeldern; Nur-Lesen nur `Esc`) | UI Tastaturbelegung als Tabelle | UI übernommen |
| cockpit: Strg+←/→ zwischen erlaubten Spalten, Strg+↑/↓ innerhalb der Spalte, Ansage über `aria-live` („Karte nach …, Position …“), Enter öffnet | Py `movable_targets`; UI mit ARIA | Py/UI übernommen (Strg+Pfeile, zusätzlich Aufnehmen mit Leertaste) |
| `prefers-reduced-motion` | UI | UI übernommen |

## 6. Teilen und Rechte

| Funktion (Original) | Ziel | Status |
|---|---|---|
| Rollen owner/edit/read; Unbeteiligte 404 | Py `permissions` (`NOT_VISIBLE`) | übernommen (6 Nutzerfälle gegen Original) |
| Seitenfreigabe vor Notizbuch-Freigabe (geerbt) | Py `role_of(..., inherited)`, `BoardService(inherited_grants=…)` | übernommen |
| Nur-Lesen bei Schreibaktion → 403 | Py `FORBIDDEN` | übernommen |
| Eigentümeraktionen für Bearbeiter/Leser → 404 | Py `FORBIDDEN` 403 | geändert B5 |
| Teilen nur owner, nur `read`/`edit`, nicht mit sich selbst, unbekannter/inaktiver Nutzer 404, Upsert | Py `check_share`, `share_board`, `BoardService(user_exists=…)` | übernommen |
| Widerrufen: owner alle, Empfänger sich selbst, sonst 403; fehlende Freigabe 404 | Py `check_revoke` | übernommen |
| Freigabedialog: Nutzersuche (Name, Benutzername, E-Mail; max. 8; bereits Geteilte ausgeblendet), Rechte ändern, Widerruf mit Bestätigung | UI `ShareDialog`; Nutzerverzeichnis | UI übernommen, Port (Nutzersuche `searchUsers`) |
| **Befund:** Dialog sendet `"write"`, Backend verlangt `"edit"` → 400 | Import liest `write` als `edit`; UI sendet `edit` | behoben im Ersatz |
| „Mit mir geteilt“ mit Rechte-Label, Eigentümer-Initialen/-Kurzname | Py `list_boards` (Rolle je Board); Core Initialen | übernommen (Py, Core, UI) |

## 7. Seitenleiste und Notizbuch

| Funktion (Original) | Ziel | Status |
|---|---|---|
| Eigene Boards: angeheftet zuerst, dann zuletzt geändert | Py `BoardService.list_boards` | übernommen |
| Anheften, Löschen, relative Zeit („vor 5 Min.“, „vor 2 Tagen“), Fortschrittsbalken | Core `relativeTime`; UI `BoardList` | übernommen (Core, UI) |
| Neues Board mit Vorlagenauswahl | Py `create_board(template_key=…)`, REST `POST /boards` | übernommen |
| Schnellnavigation Notizbuch, Tagesnotiz, KI-Fragen, Befunde | UI-Ereignis `navigate` | Port |

## 8. cockpit-Board

| Funktion (Original) | Ziel | Status |
|---|---|---|
| Neun Status auf fünf Spalten (`freigabe`/`unterbrochen` → `rueckfrage`, `fehler`/`abgebrochen` → `fertig`) | Py `Column.status_aliases`, `column_for_status`, Vorlage `cockpit-auftraege` | übernommen (9 Fälle ausgeführt) |
| Nutzer darf nur `eingang` ↔ `geplant` verschieben, innerhalb jeder Spalte umsortieren | Py `TransitionPolicy(mode restricted)` | übernommen (45 Fälle ausgeführt) |
| Laufender Auftrag: Statuswechsel → 409 | Py `locked_columns={"laeuft"}` → `COLUMN_LOCKED` (409) | übernommen |
| Reihenfolge `reihenfolge` mit Lücke +10, Umsortieren patcht alle Karten der Spalte | Py Rang-Schlüssel (eine Karte je Verschiebung) | geändert B1 |
| Ablegen vor einer Karte, Ablegen nur auf erlaubte Spalten hervorheben | Py `before_id`, `check_move`; UI | Py/UI übernommen |
| Polling alle 10 s mit Sperre während Mutationen, Deduplizierung nach ID | Py Ereignisprotokoll `GET /events?since=`; Core `BoardPort.events()`; UI: Änderungswarteschlange, Neuladen bei `VERSION_CONFLICT` | Py/Core übernommen; zeitgesteuertes Nachladen offen (Anwendung ruft `reload()`) |
| Auftragsspezifisches (Agent, Profil, Modus, Protokoll, PR, Runner, Kontingent) | `extra` + eigene Detailansicht | Port |

## Offene Punkte

- Core und Oberfläche sind umgesetzt (`@auditcore/kanban-core`,
  `@auditcore/ui` Kanban-Komponenten, `<flowaudit-kanban-board>`,
  React-Hüllen; Parität 312 Fixturefälle, REST-Vertrag gegen den
  Python-Server geprüft, 12 Playwright-Abläufe).
- Datenbankansicht (`useDbKanban`): `FaDbKanban` / `<flowaudit-db-kanban>`
  mit Kern in `@auditcore/kanban-core` (`groupRecords`, `RecordPort`) und
  `@auditcore/ui-core` (`createDbKanbanController`).
- Offen: zeitgesteuertes Nachladen über `events()`, Auslieferung der gebauten
  Oberfläche über `create_app(ui_directory=…)`.
- Umstellung von audit_designer und cockpit (Migration über
  `legacy.import_workspace`, Einbindung des Routers) übernimmt der Hauptagent.
- Dateiablage, Prompt-Erzeugung, Nutzerverzeichnis und Routing bleiben Ports
  der Anwendungen.
