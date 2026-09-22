# Legacyverhalten und bewusst korrigiertes Verhalten

Grundlage ist das tatsächlich ausgeführte Original
(`tools/capture_procurement_legacy.py`, Fixture
`tests/fixtures/procurement_legacy_observed.json`): 57 Normalisierungs-,
Datei- und Query-Fälle, 13 Abrufszenarien der TED-Seitenschleife gegen einen
`httpx.MockTransport`, 27 Precheck-Fälle und 30 Fälle der TED-/HAD-Clients
aus Flowinvoice und Designer. Zusätzlich bestehen die 28 vorhandenen
Originaltests `test_ted_harvest.py` und `test_audit_prep_ted_normalize.py`
am fixierten audit-portal-Commit.

Der Legacy-Vertrag (Standard der reinen Funktionen, `mode="legacy"`,
`legacy_*`) reproduziert alle Ausgaben exakt; die Tests prüfen jede Abweichung
zusammen mit dem Legacy-Ergebnis.

| ID | Beobachtung im Original | Korrigierter Vertrag |
|---|---|---|
| P-C01 | Unbekannte Schwellenstufe: erwartete Vergabeart ist `""`, die Teilstring-Prüfung ergibt deshalb **PASS** für jede Vergabeart. | `mode="strict"`: Verfahrens- und Mindestangebotsprüfung `NOT_CHECKED` mit Begründung. |
| P-C02 | Auftrags-/Vertragswert `0` gilt als „nicht angegeben“; Wertabweichung wird bei Wert 0 übersprungen. | `strict`: 0 ist ein Wert (Stufe `BELOW_1K`, Abweichung „Vertragswert ist 0“). |
| P-C03 | Vergabeart und Pflichtdokument-Regel werden per gegenseitigem Teilstring zugeordnet (`Direktvergabe (Ausnahme)` passt). | `strict`: exakte Bezeichnung (ohne Groß-/Kleinschreibung). |
| P-C04 | Fehlt nur einer von Vertrags- oder Abrechnungswert, entfällt die Prüfung ohne Hinweis. | `strict`: `NOT_CHECKED` „Vertrags- oder Abrechnungswert fehlt“. |
| P-C05 | Schwellen, Verfahren und Pflichtdokumente sind Code-Konstanten ohne Version; Zeitstempel ist Systemzeit. | Versioniertes Profil `procurement.hvtg-legacy 2026.09.1` mit Herkunft und Fingerprint; `now` injizierbar; `strict` nennt das Profil im Ergebnis. |
| P-C06 | Textbeträge verlieren jedes Komma: `"1.234,56"` → 1.23456. | Wert bleibt aus Kompatibilitätsgründen gleich; `inspect_notice` meldet `ambiguous_amount` (blockierend), `unparsed_amount`, `unparsed_date`, `correction_notice`. |
| P-C07 | Abruf und Normalisierung liefern nur Zuschlagsbekanntmachungen mit Auftragnehmer (`notice-type=can-standard AND winner-name=*`); Notices ohne Auftragnehmer verschwinden. | Abdeckung ausdrücklich `award_notices_with_winner`; `require_contractor=False` behält alle Bekanntmachungstypen; der Harvest-Adapter meldet übersprungene Notices als `RecordIssue` (Status `PARTIAL`). |
| P-C08 | TED-/HAD-Company-Clients: HTTP-Fehler, ungültiges JSON, Parser- und Netzwerkfehler ergeben stillschweigend eine leere Trefferliste; Flowinvoice verliert bei mehrsprachigem Titel die restlichen Treffer. | `ted_company_result`/`had_result` liefern `ok`, `no_hit`, `rate_limited` oder `failed` mit Grund; HTTP 404 ist nur in der Designer-HAD-Variante „kein Treffer“ (Quellsemantik). |
| P-C09 | TED-Seitenschleife: nicht listenförmige `notices` oder eine leere Seite beenden den Abruf wie ein reguläres Ende; Fehler brechen alles ab und verwerfen bereits gelesene Seiten. | Adapter über `auditcore_harvest`: nicht listenförmige Antwort = `ParserError`; bestätigte Seiten bleiben bestätigt, Wiederanlauf am Checkpoint. |

Nicht verändert wurden Feldaliase und Spaltenreihenfolge, Sprachpriorität
(`deu`, `ger`, `de`, `eng`, `en`), Datumslayouts, Listen-Deduplizierung,
größter Betrag bei Listen, Zuordnung „Bau“ im Leistungsartnamen, Stufenfolge,
Mindestangebote, Abweichungsschwellen 10/20 % und die Meldungstexte der Quelle
(einschließlich ihrer ASCII-Umschreibungen, damit Consumer-Ausgaben gleich bleiben).

## Offene fachliche Entscheidungen (HUMAN_DECISION_REQUIRED)

1. **Aktualität der Schwellenwerte** im Profil (Liefer-/Dienstleistungen 221.000 €,
   Bau 5.538.000 €, nationale Stufen 1.000/25.000 €) und die Verfahrenszuordnung
   nach HVTG — nicht bestätigt; ein neues Profil braucht fachliche Freigabe.
2. Ob der `strict`-Modus in Flowinvoice/Portal den Legacy-Modus ersetzen soll.
3. Drei TED-Varianten bleiben getrennt: Portal (v3 POST, eForms-Felder,
   Zuschlagsfilter), Flowinvoice (`/api/v3.0` GET, Mnemonik-Felder) und Designer
   (v3 POST, Mnemonik-Felder, Alpha-3-Ländercodes). Ob die Flowinvoice-Variante
   gegen die heutige TED-API noch funktioniert, ist nicht live geprüft
   (NOT_CONFIGURED).
4. Die HAD-Spaltenzuordnung ist eine Heuristik der Quelle (Position in der
   Zeile); bei Div-Layouts landet Linktext im Feld `vergabeart`. Ohne echte
   Originalseite (Rechte/Zugang ungeprüft) bleibt der Parser nur synthetisch belegt.
5. Versions-/Berichtigungsbezug (`notice-type=corr`, Änderungsbekanntmachungen)
   modelliert das Quellformat nicht; `inspect_notice` macht ihn nur sichtbar.
