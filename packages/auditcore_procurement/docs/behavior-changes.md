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
| P-C10 | EU-Schwellenwerte sind feste Zahlen ohne Zeitbezug (221.000 € Liefer/Dienst, 5.538.000 € Bau – die Werte 2024–2025). | Profil `procurement.hvtg 2026.09.2`: Werte je Geltungszeitraum mit amtlicher Fundstelle; `strict` wählt den Zeitraum über `reference_date` (Datum der Maßnahme/Bekanntmachung) oder `year`. Ohne Stichtag oder ohne eingetragenen Zeitraum: `REVIEW_REQUIRED`, kein Rückfall auf einen anderen Zeitraum. |
| P-C11 | Liefer-/Dienstleistungen nutzen immer den Wert für sonstige Auftraggeber; der niedrigere Wert für zentrale Regierungsbehörden (§ 106 Abs. 2 Nr. 1 GWB) fehlt. | `authority_type` `central`/`sub_central`; ohne Angabe `REVIEW_REQUIRED`, sobald das Ergebnis davon abhängt (Wert zwischen beiden Schwellen). |
| P-C12 | Stufe `BELOW_EU` gilt bis einschließlich Schwellenwert (`<=`). | `strict`: EU-Recht ab Erreichen des Schwellenwerts (§ 106 Abs. 1 Satz 1 GWB „erreicht oder überschreitet“); nationale Stufen behalten `<=` aus dem Regelwerk. |
| P-C09 | TED-Seitenschleife: nicht listenförmige `notices` oder eine leere Seite beenden den Abruf wie ein reguläres Ende; Fehler brechen alles ab und verwerfen bereits gelesene Seiten. | Adapter über `auditcore_harvest`: nicht listenförmige Antwort = `ParserError`; bestätigte Seiten bleiben bestätigt, Wiederanlauf am Checkpoint. |

Nicht verändert wurden Feldaliase und Spaltenreihenfolge, Sprachpriorität
(`deu`, `ger`, `de`, `eng`, `en`), Datumslayouts, Listen-Deduplizierung,
größter Betrag bei Listen, Zuordnung „Bau“ im Leistungsartnamen, Stufenfolge,
Mindestangebote, Abweichungsschwellen 10/20 % und die Meldungstexte der Quelle
(einschließlich ihrer ASCII-Umschreibungen, damit Consumer-Ausgaben gleich bleiben).

## EU-Schwellenwerte je Zeitraum (Profil `procurement.hvtg` 2026.09.2)

Nutzerentscheidung vom 23.09.2026: „vergabeschwellen sollen pro jahr hinterlegt sein“.
Eingetragen sind nur Zeiträume mit gelesener amtlicher Fundstelle (Stand 23.09.2026):

| Zeitraum | Bau (Art. 4 lit. a) | Liefer/Dienst zentral (lit. b) | Liefer/Dienst sonstige (lit. c) | Quelle |
|---|---:|---:|---:|---|
| 01.01.2024–31.12.2025 | 5.538.000 € | 143.000 € | 221.000 € | Delegierte VO (EU) 2023/2495, ABl. L 2023/2495 vom 16.11.2023 |
| 01.01.2026–31.12.2027 | 5.404.000 € | 140.000 € | 216.000 € | Delegierte VO (EU) 2025/2152, ABl. L 2025/2152 vom 23.10.2025; BAnz AT 18.12.2025 B4 |

Die Quellwerte 221.000 €/5.538.000 € gehören zum Zeitraum 2024–2025. Frühere und
spätere Zeiträume sind nicht eingetragen. Konzessionen (Richtlinie 2014/23/EU) und
Sektorenaufträge kommen im Quellregelwerk nicht vor und sind deshalb nicht Teil des
Profils. Die nationalen Stufen 1.000 €/25.000 € stammen aus dem Regelwerk der
Anwendungen und bleiben `REVIEW_REQUIRED`. Der Legacy-Modus nutzt unverändert die
Quelltabelle; audit-portal bleibt beim Legacy-Modus (keine Verhaltensänderung).

## Offene fachliche Entscheidungen (HUMAN_DECISION_REQUIRED)

1. **Nationale Stufen** (1.000/25.000 €), Verfahrenszuordnung nach HVTG und
   Mindestangebote — ohne Norm im Regelwerk, fachlich nicht bestätigt. Ob Consumer auf
   `strict` mit Stichtag umstellen, entscheidet die jeweilige Anwendung.
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
