# Paritätsinventur Screening-Trefferprüfung

Stand 25.09.2026. Vergleich der bestehenden Oberflächen für Sanktions- und
PEP-Abgleich mit der gemeinsamen Komponente `<flowaudit-screening-review>`
(`@auditcore/ui`) und dem REST-Vertrag
[`screening_review/1`](screening-rest.md).

Geprüfte Stände:

- **flowinvoice** `janpow77/flowinvoice` @ `5aea400` (React):
  `frontend/src/components/fraud-report/SanctionsCheck.tsx`,
  `frontend/src/components/fraud/SanctionsStatus.tsx`,
  `frontend/src/components/fraud-report/types.ts` (`SanctionsResult`, `PEPResult`),
  `backend/app/services/fraud_detection/{pep_checker,pep_store,models}.py`,
  `backend/app/verwk/services/sanctions_screening.py`.
- **audit_designer** (ecohesion) `janpow77/audit_designer` @ `2c726f3c` (Vue):
  `frontend/src/ecohesion/views/ResearchToolView.vue` (Werkzeug
  `sanctions-screening`), `components/ResearchRecordResults.vue`,
  `services/researchPresentation.ts`,
  `backend/app/core/shared/research/register/sanctions.py`.

Legende: **übernommen** = gleichwertig vorhanden; **erweitert** = vorhanden und
ausgebaut; **neu** = in keinem Vorbild vorhanden; **bewusst anders** = mit
Begründung abweichend; **nicht übernommen** = bleibt in der Anwendung.

## Eingabe und Abfrage

| Funktion | flowinvoice | audit_designer | Komponente | Status |
|---|---|---|---|---|
| Einzelname prüfen | über Rechnungsprüfung (Lieferanten) | Formular Name | Formular, mehrere Namen je Lauf | erweitert |
| Mehrere Namen je Lauf | alle Lieferanten einer Prüfung | – | bis 200 Namen, je Name eigene Trefferliste | übernommen |
| Geburtsdatum/Land als Vergleichsmerkmal | – | ja (Bonus/Malus) | ja, je Name | übernommen |
| Eintragstyp (Person/Organisation) | – | ja | ja (`schema`) | übernommen |
| Listenauswahl | fest | Auswahlkästchen, mind. eine Liste | Auswahl je Art aus `/sources` | übernommen |
| Mindestwert | fest im Code | 50–100, Vorgabe 70, Erklärtext | Bereich/Vorgabe aus dem Profil | übernommen |
| Profilwahl | implizit | implizit | ausdrücklich, empfohlenes Profil vorausgewählt | bewusst anders (kein stilles Standardprofil, Bibliotheksgrundsatz) |
| PEP-Abgleich | eigener Prüfschritt (Token-Abgleich, 0–1) | – | Art `pep` mit Profil `flowinvoice.pep_bulk` | übernommen |
| Vorgangsbezug | Rechnungsprüfung | – | `case_reference` | neu |

## Trefferliste

| Funktion | flowinvoice | audit_designer | Komponente | Status |
|---|---|---|---|---|
| Treffer je geprüftem Namen | Tabelle „Lieferant“ | je Suche | gruppiert je Name mit Status | übernommen |
| Liste, Name auf der Liste, Score | ja | ja | ja | übernommen |
| Getroffene Schreibweise / Alias-Treffer | `sanctionedNameOnList`, `via_alias` | `matched_name`, `matched_field` | ja, Alias gekennzeichnet | übernommen |
| Methode/Klasse (exakt, unscharf …) | `matchMethod` | `confidence` | Klasse mit Grenzen | übernommen |
| Geburtsdatum-/Land-Widerspruch | – | `dob_conflict`, `country_conflict` | Warnhinweis in Liste und Vergleich | übernommen |
| Zähler „exakte / ähnliche Treffer“ | ja | – | Zähler je Prüfstatus | bewusst anders (Prüfstatus trägt die Arbeit) |
| Ergebnis „keine Treffer“ | `isClean` grün | Text | `NO_HITS` / `INCOMPLETE` mit Hinweis „belegt keine Unbedenklichkeit“ | bewusst anders (kein „sauber“-Signal, REG-C01) |
| Nicht abgefragte Liste | „Aktualität nicht verifiziert“ | – | Befund je Liste, `searched: false` | erweitert |
| Filter | – | – | Prüfstatus, Liste, Name, Klasse, Mindestscore | neu |

## Vergleichsansicht

| Merkmal | flowinvoice | audit_designer | Komponente | Status |
|---|---|---|---|---|
| Eingabe vs. Listeneintrag nebeneinander | – | Details aufklappbar (nur Eintrag) | zweispaltig | neu |
| Namen und Aliasse | Name | Aliasse | Name, alle Aliasse (bis 50, Gesamtzahl) | erweitert |
| Geburtsdatum | – | ja | ja, mit Abgleichergebnis | übernommen |
| Staatsangehörigkeit/Land | PEP: Land | ja | ja, mit Abgleichergebnis | übernommen |
| Adresse | – | Anschriften | ja | übernommen |
| Kennungen, Programm/Rechtsakt, erstmals/zuletzt gesehen | PEP: first/last seen | ja | ja | übernommen |
| PEP-Funktion (Position) | `position` | – | Feld `sanctions` des Eintrags (Funktion laut Liste) | übernommen |
| Liste und Stand | Listenname, Aktualisierung | Listenname | Liste, Herausgeber, Stand zum Laufzeitpunkt, Datenlizenz | erweitert |
| Link zur Quelle | – | „Quellliste öffnen“ | Listen-URL im Quellenstand | übernommen |

## Score-Aufschlüsselung

| Funktion | flowinvoice | audit_designer | Komponente | Status |
|---|---|---|---|---|
| Methodenerklärung | `ExplainPanel` (Text, Parameter) | Erklärtext zum Mindestwert | Schritte aus `entity_matching`: Vergleichsformen, Basiswert, Zu-/Abschläge, Kappung, Ergebnis, Klassengrenzen | erweitert |
| Nachrechnung gegen Bibliothekswert | – | – | `consistent`, sichtbarer Hinweis bei Abweichung | neu |
| Rohwert und angepasster Wert | – | `score` | `raw_score` und `score` | erweitert |

## Entscheidung und Protokoll

| Funktion | flowinvoice | audit_designer | Komponente | Status |
|---|---|---|---|---|
| Treffer bestätigen / verwerfen / zurückstellen | – (Hinweis „manuelle Prüfung erforderlich“) | – | ja | neu |
| Pflichtbegründung | – | – | ja, leerer Text abgelehnt | neu |
| Vier-Augen-Option | – | – | je Entscheidung oder per Konfiguration je Ergebnis; zweite Person ≠ erste | neu |
| Protokoll | – | – | unveränderliches Ereignisprotokoll mit Person, Zeit, Begründung | neu |
| Gleichzeitige Bearbeitung | – | – | `expected_sequence`, Compare-and-Append, 409 | neu |

## Quellenstand und Aktualität

| Funktion | flowinvoice | audit_designer | Komponente | Status |
|---|---|---|---|---|
| Stand je Liste | `lastUpdate` (Lieferung, nicht Ladezeit) | Stand im Backend | `as_of` + Alter in Tagen | übernommen |
| Bewertung „veraltet“ | rot bei fehlendem Stand | – | `current`/`stale`/`unknown`/`not_judged` nach konfiguriertem Höchstalter | erweitert |
| Anzahl Einträge je Liste | ja | – | ja | übernommen |
| Datenquelle/Lizenz | `data_source` | – | Anbieter, Herausgeber, Lizenzstatus und -hinweis | erweitert |
| Listenimport auslösen | Admin-Knopf „Import“ | – | – | nicht übernommen (Betrieb der Anwendung, Harvest-Adapter) |

## Weitere Abweichungen

- **Kein Risikopunktwert.** flowinvoice rechnet PEP-/Sanktionstreffer in einen
  Betrugsrisikowert ein (`RiskScoreBreakdown`). Das bleibt in der Anwendung;
  die Komponente liefert Treffer und Entscheidungen, keine Risikogewichtung.
- **Mehrsprachigkeit.** Beide Vorbilder schalten DE/EN um. Die Komponente ist
  zunächst deutsch; die Beschriftungen liegen gesammelt in der View-Logik
  (`labels.ts`) und können als Satz ersetzt werden.
- **„Phonetische Varianten“.** Der Werkzeugeintrag des Designers wird nicht
  übernommen; es gibt kein phonetisches Verfahren (Entscheidung R9).
