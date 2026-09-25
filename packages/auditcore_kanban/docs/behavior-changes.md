# Abweichungen vom Original (bewusst)

Grundlage: das ausgeführte Backend des audit_designer-Workspace-Boards
(`tests/fixtures/legacy_kanban_observed.json`, 77 Fälle, Commit
`2c726f3c`) und die ausgeführten cockpit-Regeln
(`tests/fixtures/cockpit_rules_observed.json`, Commit `df203d4c`). Gleiches
Verhalten prüfen `tests/test_legacy_characterization.py` und
`tests/test_cockpit_characterization.py`; die folgenden Abweichungen sind dort
mit dem beobachteten Altwert festgehalten.

| Nr. | Original (beobachtet) | Bibliothek | Grund |
|---|---|---|---|
| B1 | Reihenfolge über ganzzahlige `position` 1..N; jede Verschiebung nummeriert Quell- und Zielspalte neu | Rang-Schlüssel (`rank`); eine Verschiebung ändert nur die bewegte Karte (bei doppelten Rängen wird die Spalte einmal neu verteilt) | Weniger Schreibvorgänge, keine Wettläufe beim Umnummerieren, gleiche Reihenfolge |
| B2 | `update_task` mit `position` setzt die Zahl und löst Gleichstand über `created_at` auf: `position=1` für C ergibt A, C, B | Keine Position im Update; Umsortieren nur über `move_card` (C an Index 0 → C, A, B) | Das Original verfehlt die gewünschte Stelle bei Gleichstand |
| B3 | Entfernte Spalten: Karten erhalten den Status der ersten Spalte, behalten ihre Position → verzahnt (A, X, B, Y) | Karten entfernter Spalten werden in bisheriger Reihenfolge ans Ende der ersten Spalte gehängt (A, B, X, Y) | Deterministisch, kein Gleichstand |
| B4 | `create_task` mit `deadline=""` → 400 „Ungültiges Deadline-Format“ | Leere Frist bedeutet „keine Frist“, auch beim Anlegen | Update behandelte `""` schon so; einheitlich |
| B5 | Eigentümer-Aktionen (Einstellungen, Teilen, Freigaben lesen) für Bearbeiter/Leser → 404 „Nicht gefunden“ | `FORBIDDEN` (403) für Nutzer, die das Board sehen; Unbeteiligte weiter `NOT_VISIBLE` (404) | Wer das Board sieht, erfährt nichts Neues; die Meldung ist verständlicher |
| B6 | `create_task` kennt kein Positionsfeld (Pydantic verwirft das `position` des Frontends); neue Karten immer ans Ende | Ende als Standard, zusätzlich `index`/`before_id`/`after_id` | Wunsch „Aufgabe an dieser Stelle einfügen“ |
| B7 | Meldungen für Status/Priorität englisch („Invalid status …“) | Deutsch: „Unbekannte Spalte …“, „Ungültige Priorität …“ | Einheitlich deutsche Meldungen |
| B8 | Badge ohne Längenprüfung (DB-Spalte 20 Zeichen → Datenbankfehler) | `VALIDATION_ERROR` „Badge ist zu lang“ ab 21 Zeichen | Fehler vor der Speicherung |
| B9 | Suche verwendet den untrimmten Suchtext | Suchtext wird getrimmt | Leerzeichen am Rand liefern sonst keine Treffer |
| B10 | `list_boards`-Statistik zählt nur `offen`/`in_arbeit`/`erledigt` | `board_stats` zählt jede Spalte; erledigt = `done`-Spalte, sonst letzte Spalte | Eigene Spalten wurden falsch gezählt |

Unverändert übernommen: Grenzwerte (Titel ≤ 300 nach Trimmen, Beschreibung ≤
10 000, ≤ 20 Tags zu je ≤ 80 Zeichen, 1–10 Spalten, Spalten-ID-Regex, Label
1–80), die Prüfreihenfolge und die deutschen Meldungen der Spaltenprüfung,
Standardspalten, Positions-Klemmung (0/negativ → Anfang, zu groß → Ende),
Statuswechsel per Update ans Spaltenende, Rechteauflösung (Eigentümer, dann
Seitenfreigabe, dann Notizbuch-Freigabe; Seitenfreigabe hat Vorrang),
Teilen (nur `read`/`edit`, nicht mit sich selbst, Upsert, Empfänger darf sich
selbst entfernen, sonst 403 „Keine Berechtigung“), cockpit-Statusabbildung und
Verschieberegeln (nur `eingang` ↔ `geplant`; `laeuft` gesperrt).

Befunde im Original ohne Entsprechung in der Bibliothek: Der Freigabedialog
sendet `permission: "write"`, das Backend akzeptiert nur `read`/`edit` und
antwortet 400 (Teilen mit „Bearbeiten“ scheitert im Original). Der Import
(`legacy.import_workspace`) liest `write` als `edit`.
