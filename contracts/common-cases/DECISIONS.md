# Festlegungen für die gemeinsamen Vertragsfälle

**Status: festgelegt (Nutzer 2026-09-25).** Der Nutzer hat die offenen
Festlegungen aus der Inventur (`docs/reports/app-helfer-ts.md`, Abschnitt 6)
am 25.09.2026 entschieden (Auftrag „korrigiere erstmal alles“). Die Werte sind
zentral in [`decisions.json`](decisions.json) hinterlegt (Listen `festgelegt`,
`vorläufig`, `technisch`); die Falldateien verweisen mit
`{"$decision": "<schlüssel>"}` darauf. Eine Änderung dort wirkt auf alle
Verträge, ohne dass Falldateien angepasst werden müssen.

### Festgelegt (Nutzer 2026-09-25)

| Schlüssel | Wert | Wirkung |
|---|---|---|
| `empty_value` | „—“ (Geviertstrich, U+2014) | Ersatzwert jedes Anzeigeformatierers für leer/ungültig (`empty-value`, `format-*`); ersetzt „-“, „–“, „“, „N/A“, „k.A.“ |
| `filesize_base`, `filesize_units` | 1024 mit B/KB/MB/GB/TB, Dezimalkomma, höchstens eine Nachkommastelle | `format-filesize` („KB/MB“, nicht „KiB/MiB“) |
| `ambiguous_single_dot_de` | `invalid` | `parse-number`, Modus `de`: „1.5“ ist in Betragsfeldern ungültig, die Oberfläche zeigt einen Hinweis („mehrdeutig“); weder 1,5 noch 15 wird geraten |
| `amount_max_fraction_digits_de` | 2 | `parse-number`, Modus `de`: höchstens zwei Nachkommastellen bei Beträgen; „1.234“ (eine Dreiergruppe ohne Komma) und „1,234“ sind mehrdeutig mit Hinweis, „.“/„€“/„-“ allein gelten als leer – übernommen aus der strikten Betragsauslegung von flowinvoice (`german-decimal.ts`, `amount_parsing.py`, `german-amount-cases.json`). Die Grenze gilt für Beträge; Mengen und Sätze dürfen sie ausdrücklich aufheben (`auditcore_common.numbers_de`, `max_fraction_digits=None`) |
| `display_timezone` | Europe/Berlin | `format-date`, `format-datetime`: Anzeige immer in Berliner Zeit (nicht Browserzeit), reine Datumswerte ohne Umrechnung |

Verträge, deren Festlegungen damit vollständig entschieden sind, tragen den
Status `verbindlich`: `parse-number`, `empty-value`, `format-date`,
`format-filesize`.

### Noch vorläufig

| Schlüssel | Vorläufiger Wert | Wirkung | Offene Frage an den Nutzer |
|---|---|---|---|
| `money_rounding` | kaufmännisch (half-up) | `format-money`: 0,125 → 0,13 € | Python `round()`/`format()` runden heute 0,125 → 0,12 |
| `datetime_separator` | „, “ | `format-datetime`: „15.07.2026, 12:05“ (Intl-Standard) | Komma oder nur Leerzeichen? |

`format-money` und `format-datetime` bleiben deshalb `vorläufig`.

### Technisch (keine Nutzerfrage)

| Schlüssel | Wert | Wirkung |
|---|---|---|
| `probe_timezone` | America/New_York | Der Vertragsläufer startet die Hilfsfunktionen mit dieser Prozess-Zeitzone, damit fehlendes `timeZone` und `new Date('JJJJ-MM-TT')` sichtbar werden |
| `csv_delimiter`, `csv_bom`, `csv_formula_prefix` | „;“, BOM, Präfix „'“ vor `= + - @` Tab CR | `csv-cell`, `csv-document` |

Weitere Einzelregeln (in den Falldateien selbst, vorläufig):

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
`status` einer Falldatei von „vorläufig“ auf „verbindlich“, sobald alle
Festlegungen, auf die sie sich stützt, entschieden sind; die Erwartungen
ändern sich dadurch nicht (keine neue Version).
