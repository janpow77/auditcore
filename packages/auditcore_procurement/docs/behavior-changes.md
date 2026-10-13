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

## Nachtrag 2014–2023 (Profil `procurement.hvtg` 2026.09.3, Paketversion 0.2.0)

Nutzerentscheidung vom 23.09.2026: „c2. ja“ (historische EU-Schwellen je Jahr
nachtragen). 2026.09.2 bleibt byte-gleich (SHA-256 `ac28af97…`, Fingerprint
`fbb7f26e…`) und liefert vor 2024 weiterhin `REVIEW_REQUIRED`. Jede Zahl wurde im
amtlichen deutschen Text der ändernden Verordnung gelesen (Cellar des Amts für
Veröffentlichungen, weil eur-lex.europa.eu automatisierte Abrufe mit einer
Challenge-Seite beantwortet); das Profil hält CELEX, ABl.-Fundstelle, EUR-Lex-URL
und SHA-256 des gelesenen Dokuments je Zeitraum.

| Zeitraum | Bau | Liefer/Dienst zentral | Liefer/Dienst sonstige | Quelle |
|---|---:|---:|---:|---|
| 01.01.2014–31.12.2015 | 5.186.000 € | 134.000 € | 207.000 € | VO (EU) Nr. 1336/2013, ABl. L 335 vom 14.12.2013, S. 17 (Art. 7 RL 2004/18/EG) |
| 01.01.2016–31.12.2017 | 5.225.000 € | 135.000 € | 209.000 € | Delegierte VO (EU) 2015/2170, ABl. L 307 vom 25.11.2015, S. 5 (RL 2014/24/EU), zugleich VO (EU) 2015/2342, ABl. L 330 vom 16.12.2015, S. 18 (RL 2004/18/EG) |
| 01.01.2018–31.12.2019 | 5.548.000 € | 144.000 € | 221.000 € | Delegierte VO (EU) 2017/2365, ABl. L 337 vom 19.12.2017, S. 19 |
| 01.01.2020–31.12.2021 | 5.350.000 € | 139.000 € | 214.000 € | Delegierte VO (EU) 2019/1828, ABl. L 279 vom 31.10.2019, S. 25 |
| 01.01.2022–31.12.2023 | 5.382.000 € | 140.000 € | 215.000 € | Delegierte VO (EU) 2021/1952, ABl. L 398 vom 11.11.2021, S. 23 |
| 2024–2027 | wie 2026.09.2 | | | gegen VO (EU) 2023/2495 und 2025/2152 erneut geprüft, unverändert |

- **Richtlinienwechsel 2016:** RL 2004/18/EG galt bis 17.04.2016 (Art. 91 RL
  2014/24/EU). Für 01.01.–17.04.2016 setzt VO (EU) 2015/2342 in RL 2004/18/EG
  dieselben Werte wie VO (EU) 2015/2170 in RL 2014/24/EU; der Zeitraum 2016–2017
  ist daher durchgehend und nennt beide Fundstellen.
- **Nicht eingetragen:** vor 2014 und ab 2028; Konzessionen (RL 2014/23/EU),
  Sektoren (RL 2014/25/EU), soziale und andere besondere Dienstleistungen
  (Art. 4 lit. d RL 2014/24/EU) und Wettbewerbe – das Profilschema kennt diese
  Kategorien nicht. Nationale Stufen unverändert `REVIEW_REQUIRED`.
- **`CURRENT_PROFILE`** ist jetzt 2026.09.3. `profile_from_ruleset(...,
  year_bound=True)` übernimmt damit 2014–2027; mit `eu_version="2026.09.2"` bleibt
  das Verhalten von 0.1.0 reproduzierbar.

## Profil 2026.10.1: EU-Schwellenwerte aller Regime (13.10.2026)

Anlass: Das Paket soll die EU-Schwellenwerte vollständig führen (Auftrag vom
13.10.2026; der Schwellenwert-Rechner der Anwendung zeigte Sektorenaufträge,
Konzessionen sowie soziale und andere besondere Dienstleistungen als „nicht
hinterlegt“). Kein bisheriges Ergebnis ändert sich; die Profile 2026.09.1 bis
2026.09.3 sind bytegleich.

Abruf am 13.10.2026 beim Amt für Veröffentlichungen
(`http://publications.europa.eu/resource/celex/<CELEX>`, deutsche Fassung). Die
Liste der Änderungsrechtsakte je Richtlinie stammt aus der Cellar-Abfrage
(`cdm:resource_legal_amends_resource_legal`). Werte in EUR ohne MwSt.

| Zeitraum | RL 2014/24/EU: Bau / L+D zentral / L+D subzentral | RL 2014/25/EU: Bau / L+D | RL 2014/23/EU: Konzession | RL 2009/81/EG: Bau / L+D |
|---|---|---|---|---|
| 01.01.2014–31.12.2015 | 5.186.000 / 134.000 / 207.000 – VO (EU) Nr. 1336/2013 Art. 2 (RL 2004/18/EG) | 5.186.000 / 414.000 – VO (EU) Nr. 1336/2013 Art. 1 (RL 2004/17/EG) | nicht eingetragen | 5.186.000 / 414.000 – VO (EU) Nr. 1336/2013 Art. 3 |
| 01.01.2016–31.12.2017 | 5.225.000 / 135.000 / 209.000 – VO (EU) 2015/2342 (bis 17.04.2016), Del. VO (EU) 2015/2170 | 5.225.000 / 418.000 – VO (EU) 2015/2341 (bis 17.04.2016), Del. VO (EU) 2015/2171 | 5.225.000 ab 18.04.2016 – Del. VO (EU) 2015/2172 | 5.225.000 / 418.000 – VO (EU) 2015/2340 |
| 01.01.2018–31.12.2019 | 5.548.000 / 144.000 / 221.000 – Del. VO (EU) 2017/2365 | 5.548.000 / 443.000 – Del. VO (EU) 2017/2364 | 5.548.000 – Del. VO (EU) 2017/2366 | 5.548.000 / 443.000 – VO (EU) 2017/2367 |
| 01.01.2020–31.12.2021 | 5.350.000 / 139.000 / 214.000 – Del. VO (EU) 2019/1828 | 5.350.000 / 428.000 – Del. VO (EU) 2019/1829 | 5.350.000 – Del. VO (EU) 2019/1827 | 5.350.000 / 428.000 – Del. VO (EU) 2019/1830 |
| 01.01.2022–31.12.2023 | 5.382.000 / 140.000 / 215.000 – Del. VO (EU) 2021/1952 | 5.382.000 / 431.000 – Del. VO (EU) 2021/1953 | 5.382.000 – Del. VO (EU) 2021/1951 | 5.382.000 / 431.000 – Del. VO (EU) 2021/1950 |
| 01.01.2024–31.12.2025 | 5.538.000 / 143.000 / 221.000 – Del. VO (EU) 2023/2495 | 5.538.000 / 443.000 – Del. VO (EU) 2023/2496 | 5.538.000 – Del. VO (EU) 2023/2497 | 5.538.000 / 443.000 – Del. VO (EU) 2023/2510 |
| 01.01.2026–31.12.2027 | 5.404.000 / 140.000 / 216.000 – Del. VO (EU) 2025/2152 | 5.404.000 / 432.000 – Del. VO (EU) 2025/2150 | 5.404.000 – Del. VO (EU) 2025/2151 | 5.404.000 / 432.000 – Del. VO (EU) 2025/2487 |

Soziale und andere besondere Dienstleistungen: 750.000 EUR (Art. 4 Buchst. d
RL 2014/24/EU, Anhang XIV) und 1.000.000 EUR (Art. 15 Buchst. c RL 2014/25/EU,
Anhang XVII), eingetragen vom 18.04.2016 bis 31.12.2027. Keine der
Änderungsverordnungen berührt diese Buchstaben.

- **Richtlinienwechsel 2016:** Im Block `eu_regimes` ist der Zeitraum 2016–2017
  für öffentliche Aufträge und Sektorenaufträge am 17./18.04.2016 geteilt und
  nennt je Teil die Verordnung zur damals geltenden Richtlinie; die Werte sind
  gleich. Die Jahrestabelle der Vorprüfung behält den durchgehenden Zeitraum.
  Konzessionen und der Schwellenwert für soziale und andere besondere
  Dienstleistungen beginnen am 18.04.2016 (Ablauf der Umsetzungsfrist); ein
  Stichtag davor ergibt „nicht hinterlegt“.
- **Verteidigungsbereich nach RL 2014/24/EU:** Art. 4 Buchst. b gilt bei
  Lieferaufträgen öffentlicher Auftraggeber im Verteidigungsbereich nur für
  Waren nach Anhang III, sonst Buchst. c. Das Profil führt dafür keine eigene
  Auftragsart; der Hinweis steht bei der Auftraggeberart `central`.
- **Nicht eingetragen:** vor 2014 und ab 2028; Baukonzessionen nach Art. 56
  RL 2004/18/EG vor dem 18.04.2016; subventionierte Aufträge (Art. 13
  RL 2014/24/EU); Wettbewerbe als eigene Auftragsart; die Regeln zur Schätzung
  des Auftragswerts.
- **`CURRENT_PROFILE`** ist jetzt 2026.10.1. `profile_from_ruleset(...,
  year_bound=True)` übernimmt damit auch die Regimetabelle; der Fingerprint des
  so gebauten Profils ändert sich, die Ergebnisse nicht. Mit
  `eu_version="2026.09.3"` bleibt der bisherige Fingerprint.

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
