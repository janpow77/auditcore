# Paritätsfixtures Python ↔ TypeScript

`auditcore_kanban` (Python) und `@flowaudit/kanban-core` (TypeScript) müssen bei
Rang, Übergängen, WIP, Filter, Fristen, Rechten, Validierung, Befehlen und
der Gruppierung der Datenbankansicht
identisch entscheiden. Die gemeinsame Referenz sind die JSON-Dateien unter
`packages/auditcore_kanban/tests/fixtures/parity/`. Python erzeugt sie
(`tools/build_parity_fixtures.py`), ein Python-Test prüft, dass die Neuerzeugung
bitgleich ist (`--check`); die TS-Tests lesen dieselben Dateien und vergleichen
ihr Ergebnis mit `expected`.

Jede Datei ist eine Liste von Fällen `{"name": str, "input": JSON, "expected": JSON}`.
`input` enthält nur JSON; Boards stehen darin in der Form
`auditcore_kanban.board/1` (siehe unten und `schemas/board.schema.json`).
Entscheidungen haben die Form `{"allowed": bool, "code": str|null, "warnings": [str]}`
(`code` ist `null`, wenn erlaubt; bei WIP-Modus `warn` steht
`"WIP_LIMIT_REACHED"` in `warnings`).

| Datei | `input` | `expected` |
|---|---|---|
| `rank.json` | `{"op":"between","a":str\|null,"b":str\|null}` | Schlüssel oder `{"error":"INVALID_RANK"}` (ungültiger Schlüssel) / `{"error":"INVALID_RANK_ORDER"}` (a ≥ b) |
| | `{"op":"spread","count":int}` | Liste von Schlüsseln |
| | `{"op":"valid","key":str}` | bool |
| | `{"op":"sequence","steps":[{"a","b","key"}]}` | Endliste nach 60 Einfügungen (jeder Schritt: `rank_between(a,b) == key`) |
| `transitions.json` | `{"board","card_id","target"}` | Entscheidung von `check_move` (Übergang, dann WIP) |
| `wip.json` | `{"board","column_id","exclude_card_id":str\|null}` | Entscheidung von `check_capacity` |
| `filter.json` | `{"board","filter":{query?,priorities?,tags?,assignees?,columns?,due_states?},"today":"YYYY-MM-DD"}` | Karten-IDs in Board-Reihenfolge |
| `deadline.json` | `{"due":str\|null,"today":"YYYY-MM-DD"}` | `none` \| `overdue` \| `due_soon` \| `later` |
| `permissions.json` | `{"op":"authorize","board","user_id","action","inherited":{user:perm}\|null}` | `{"role":str\|null,"decision":…}` |
| | `{"op":"share","board","actor","target_user","permission"}` | Entscheidung von `check_share` |
| | `{"op":"revoke","board","actor","target_user"}` | Entscheidung von `check_revoke` |
| `validation.json` | `{"op":"card_fields","fields":{…}}` | `{"ok":true,"value":{…}}` oder `{"ok":false,"code","message"}` |
| | `{"op":"columns","columns":[…]}` | `{"ok":true,"value":[Spalten]}` oder Fehler |
| `commands.json` | `{"board","actor","now","new_id"?,"op":"move"\|"toggle_done"\|"create"\|"configure",…}` | `{"orders":{column_id:[[card_id,rank],…]},"version":int}` |
| `group.json` | `{"table":{"properties":[…],"rows":[{"id","cells"}]},"group_by":str}` (Datenbankansicht) | `[[option, [row_id, …]], …]` – führende Spalte `""` nur, wenn nicht leer (`group_by_value` / `groupRecords`) |

Regeln, die beide Seiten exakt gleich umsetzen:

- **Rang:** Alphabet `0-9A-Za-z` (Base 62, ASCII-sortiert), Schlüssel nie leer, nie
  mit `0` am Ende; Greenspan-Midpoint (`rank.py`); `spread_ranks(n)`: kleinste
  Länge L ≥ 1 mit 62^L > n (höchstens 6), Wert ⌊(i+1)·62^L/(n+1)⌋ in Base 62 auf L
  Stellen, abschließende `0` entfernt.
- **Reihenfolge in der Spalte:** `rank`, dann `created_at`, dann `id` (Zeichenkettenvergleich).
- **Suche:** `query.strip().lower()` bzw. `trim().toLowerCase()`; Teilstring in
  Titel, Beschreibung, Badge, Tags. Kein `casefold` (`ß` bleibt `ß`).
- **Frist:** Datumsteil `due[:10]`; Tage = due − heute; < 0 `overdue`, ≤ 3 `due_soon`.
- **Übergang:** Zielspalte unbekannt → `UNKNOWN_COLUMN`; gleiche Spalte →
  erlaubt, außer `fixed_order_columns` (`ORDER_FIXED`); Quelle in
  `locked_columns` → `COLUMN_LOCKED`; `mode` `restricted` und Paar nicht in
  `allowed` → `TRANSITION_NOT_ALLOWED`; danach WIP ohne die bewegte Karte
  (`WIP_LIMIT_REACHED`, im Modus `warn` nur als Warnung).
- **Rechte:** Rolle = Eigentümer → `owner`, sonst eigene Freigabe, sonst geerbte
  Freigabe. Ohne Rolle `NOT_VISIBLE`; fehlendes Recht `FORBIDDEN`. Tabelle in
  `permissions.py` (`ROLE_ACTIONS`).
- **Platzierung:** `before_id` / `after_id` / `index` (geklemmt auf 0…n), sonst Ende;
  sind die Ränge der Zielspalte nicht streng steigend, wird die Spalte mit
  `spread_ranks(n+1)` neu verteilt.
- **Prozent:** `(200·teil + gesamt) // (2·gesamt)` (= `Math.round`).

## Board-JSON (`auditcore_kanban.board/1`)

```json
{"schema_version": "auditcore_kanban.board/1", "id": "b1", "title": "…", "icon": "📋",
 "owner_id": "u1", "pinned": false, "archived": false, "version": 3,
 "created_at": "", "updated_at": "",
 "columns": [{"id": "offen", "label": "Offen", "color": "#7c3aed", "wip_limit": null,
              "done": false, "status_aliases": []}],
 "cards": [{"id": "a", "column_id": "offen", "rank": "V", "title": "…", "description": "",
            "priority": "mittel", "tags": [], "assignees": [], "due": null, "color": null,
            "image": null, "badge": null, "checklist": [{"text": "…", "done": false}],
            "links": [{"kind": "notebook-page", "target": "…", "title": ""}],
            "attachments": [{"id": "…", "filename": "…", "mime_type": "…", "size": 0}],
            "created_at": "", "updated_at": "", "extra": {}}],
 "labels": [{"id": "…", "name": "…", "color": "#6b7280"}],
 "shares": [{"user_id": "u2", "permission": "edit", "shared_by": "u1", "created_at": null}],
 "transitions": {"mode": "free", "allowed": [], "locked_columns": [], "fixed_order_columns": []},
 "wip_mode": "block", "extra": {}}
```

Nutzer-IDs sind Zeichenketten. `due` ist ein ISO-Datum (`YYYY-MM-DD`) oder – aus
Altdaten – ein ISO-Zeitpunkt; ausgewertet wird nur der Datumsteil.
