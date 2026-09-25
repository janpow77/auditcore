# Festlegungen für die gemeinsamen Vertragsfälle

**Status: vorläufig** (Stand 25.09.2026). Die Nutzerentscheidungen aus der
Inventur (`docs/reports/app-helfer-ts.md`, Abschnitt 6, „Offene Festlegungen“)
stehen noch aus. Bis dahin gelten die Werte unten. Sie sind zentral in
[`decisions.json`](decisions.json) hinterlegt; die Falldateien verweisen mit
`{"$decision": "<schlüssel>"}` darauf. Eine Änderung dort wirkt auf alle
Verträge, ohne dass Falldateien angepasst werden müssen.

| Schlüssel | Vorläufiger Wert | Wirkung | Offene Frage an den Nutzer |
|---|---|---|---|
| `empty_value` | „—“ (Geviertstrich, U+2014) | Ersatzwert jedes Anzeigeformatierers für leer/ungültig (`empty-value`, `format-*`) | Einheitlich „—“? (heute „-“, „–“, „“, „N/A“, „k.A.“) |
| `filesize_base`, `filesize_units` | 1024 mit B/KB/MB/GB/TB, Dezimalkomma, höchstens eine Nachkommastelle | `format-filesize` | „KB/MB“ (Status quo) oder „KiB/MiB“? |
| `ambiguous_single_dot_de` | `invalid` | `parse-number`, Modus `de`: „1.5“ ist ungültig, die Oberfläche zeigt einen Hinweis („mehrdeutig“) | „1.5“ in Betragsfeldern als 15, als 1,5 oder ablehnen? |
| `display_timezone` | Europe/Berlin | `format-date`, `format-datetime`: Anzeige immer in Berliner Zeit, reine Datumswerte ohne Umrechnung | Feste Zeitzone oder Browserzeit? |
| `probe_timezone` | America/New_York | Der Vertragsläufer startet die Hilfsfunktionen mit dieser Prozess-Zeitzone, damit fehlendes `timeZone` und `new Date('JJJJ-MM-TT')` sichtbar werden | – (technisch) |
| `money_rounding` | kaufmännisch (half-up) | `format-money`: 0,125 → 0,13 € | Python `round()`/`format()` runden heute 0,125 → 0,12 |
| `datetime_separator` | „, “ | `format-datetime`: „15.07.2026, 12:05“ (Intl-Standard) | Komma oder nur Leerzeichen? |
| `csv_delimiter`, `csv_bom`, `csv_formula_prefix` | „;“, BOM, Präfix „'“ vor `= + - @` Tab CR | `csv-cell`, `csv-document` | – |

Weitere vorläufige Einzelregeln (in den Falldateien selbst):

- Beträge: geschütztes Leerzeichen U+00A0 vor „€“ (wie `Intl.NumberFormat`). Handgebaute „ €“ mit normalem Leerzeichen verletzen den Vertrag.
- Zahlen in CSV: Dezimalkomma, keine Tausendertrenner, kein Formelschutz-Präfix; leere Werte bleiben leer (nicht „—“).
- Zeitstempel ohne Zonenangabe („2026-07-15T10:05:00“) sind **nicht** Teil der Verträge, weil ihre Bedeutung (UTC oder Ortszeit) je Backend verschieden ist. Offen.
- API-Fehlertexte: nur Inhaltsprüfung (`contains`/`not_contains`), keine feste Formulierung.

## Sonderwerte in Falldateien

| Kodierung | TypeScript | Python |
|---|---|---|
| `{"$undefined": true}` | `undefined` | Fall entfällt (nur `languages: ["ts"]`) |
| `{"$nan": true}` | `NaN` | `float("nan")` |
| `{"$date": "…Z"}` | `new Date(…)` | `datetime` mit Zone |
| `{"$error": "Text"}` | `new Error("Text")` | `Exception("Text")` |
| `{"$decision": "schlüssel"}` | Wert aus `decisions.json` | Wert aus `decisions.json` |

## Versionierung

Jede Falldatei trägt `version` (SemVer). Neue Fälle erhöhen die Nebenversion,
geänderte Erwartungen die Hauptversion. Mit der Nutzerentscheidung wechselt
`status` von „vorläufig“ auf „verbindlich“.
