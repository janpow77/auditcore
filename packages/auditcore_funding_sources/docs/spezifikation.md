# Spezifikation auditcore_funding_sources

Stand: 26.09.2026, Paketversion 0.1.5. Charakterisierung: 315 Fälle
flowworkshop (dazu 11 Harvest-Läufe gegen eine Wegwerf-PostgreSQL), 112 Fälle
flowsearch, 384 Fälle audit_designer (dazu 7 De-minimis-Ernteläufe)
(`tests/fixtures`, `tests/test_replay_*.py`).
Eigenschaftstests: `tests/test_spezifikation.py`.

## Zweck

Das Paket liest Begünstigtenlisten (Transparenzlisten der Länder und der EU),
Beihilfedaten und das zentrale De-minimis-Register (eAidRegister), vergibt
stabile Identitäten, plant die Bestandsänderung eines Abrufs und rechnet die
registrierten De-minimis-Beihilfen eines Unternehmens zu einem Stichtag
zusammen. Die Kumulierung ist eine nachvollziehbare Rechnung mit Begründung je
Meldung; die fachliche Beurteilung (Überschreitung, Rückforderung) bleibt bei
der Prüferin oder dem Prüfer. Abruf, Seitenfolge und Wiederholungen
übernimmt `auditcore_harvest`.

## Verträge

Die Quellvarianten bleiben getrennte Profile; gleiche Funktionsnamen
bedeuten nicht gleiche Semantik.

| Baustein | Eingabe | Ausgabe | Nebenwirkungen |
|---|---|---|---|
| `workshop` (Profil `flowworkshop.beneficiaries`) | Tabellenzeilen, Betrags-/Datums-/Namenstexte | `parse_amount` → `Decimal \| None`, `compute_record_hash` → 32 Hex (SHA-256), Spaltenerkennung, Fondsfilter, `validate_rows` | keine |
| `flowsearch` (Profil `flowsearch.beneficiaries`) | Datei, Mapping je Quelle | `parse_amount` → `float` (fehlend 0,0), `project_id` → 16 Hex (MD5), ZIP bis 64 MiB je Mitglied | keine |
| `designer` (Profile `designer.beneficiaries`, `designer.state_aid`) | Betrags-, Satz-, Datumstexte | `Decimal \| None`, eigener Hash | keine |
| `tables` | CSV (Standardbibliothek) oder XLSX (Extra `xlsx`) | Zeilen; `typing="legacy"`/`"text"`, `header_detection="legacy"`/`"strict"`, Ressourcengrenzen | keine |
| `snapshot.plan_snapshot(rows, context, mode=, stored_identities=)` | geparste Zeilen, Quellenkontext, Modus `smart`/`full-refresh`/`force`/`snapshot`, gespeicherte Identitäten | `SnapshotPlan` (Einfügungen, Aktualisierungen, Löschen vorab, Zähler, Status) | keine; ausgeführt wird der Plan vom Consumer |
| `deminimis` | Suchkriterien bzw. Registerantworten | Anfragen, geprüfte Antworten, Feldabbildung, Behördenebene | keine |
| `deminimis_inventory` | Registerläufe | Identitäten, Abgleich, Bestandsstand | keine |
| `cumulation.calculate(awards, reference_date=, undertaking_references=)` | Registermeldungen mit Feldnamen des eAidRegisters, Stichtag, Referenzen eines Unternehmens | `CumulationResult`: Einstufung je Meldung (`considered`/`excluded`/`unclear` mit Grund), Summen je Art, Höchstbetrag und Differenz nur bei vergleichbarer Lage, `decision = None` | keine |
| `adapters` | `funding.de_minimis_eaid`, `funding.eu_beneficiaries`, `funding.eu_beneficiaries.flowsearch` | Harvest-Datensätze, `RecordIssue`, `snapshot_complete` | Netz nur über den Transport des Hosts |

Kumulierungsprofil `designer.deminimis.cumulation` 2026.09.1 (Status
`REVIEW_REQUIRED`): Fenster drei Kalenderjahre bis zum Stichtag, beide
Randtage eingeschlossen, 29.02. → 28.02.; Höchstbetrag 300 000 EUR nur, wenn
ausschließlich Meldungen der allgemeinen Regelung (`GENERAL`) vorliegen.

## Invarianten

| Nr. | Invariante | Test |
|---|---|---|
| I1 | Jede Meldung wird genau einmal eingestuft (`considered`, `excluded`, `unclear`); die Summe ist genau die Summe der berücksichtigten Beträge und gleich der Summe über die Arten; das Ergebnis enthält nie ein Urteil (`decision = None`); vollständig genau dann, wenn nichts `unclear` ist. | `test_i1_every_award_is_classified_and_summed_once` |
| I2 | Höchstbetrag, Differenz und Überschreitung gibt es nur, wenn alle Meldungen geklärt sind und ausschließlich die allgemeine Regelung betreffen; dann ist die Überschreitung „Summe > 300 000 EUR“. Sonst bleiben alle drei leer, mit Begründung. | `test_i2_ceiling_comparison_only_when_clear` |
| I3 | Das Fenster reicht vom gleichen Kalendertag drei Jahre zurück (29.02. → 28.02.) bis zum Stichtag; beide Randtage zählen, der Vortag nicht. | `test_i3_window_is_three_calendar_years_with_both_edges` |
| I4 | Meldungen anderer Begünstigtenreferenzen werden ausgeschlossen; Reihenfolge der Meldungen und der Referenzen ändert das Ergebnis nicht. | `test_i4_undertaking_and_order_do_not_change_the_sum` |
| I5 | Fehlendes Datum, unlesbarer oder negativer Betrag ergeben `unclear` und ein unvollständiges Ergebnis ohne Vergleich; ein Stichtag, der kein Datum ist, wird abgewiesen (kein implizites „heute“). | `test_i5_unclear_awards_are_never_guessed` |
| I6 | Die flowworkshop-Identität ist 32 Hex über die Hashfelder des Profils und den Quellschlüssel; Groß-/Kleinschreibung, NFKC und Leerraum ändern sie nicht, andere Felder auch nicht. | `test_i6_record_identity_is_normalised_and_stable` |
| I7 | Bestandsplan: `force`/`snapshot` ersetzen den Bestand (gelöscht = gespeicherte Identitäten), `smart`/`full-refresh` behalten ihn; eingefügte Identitäten sind eindeutig; ohne Quellenkontext (Fonds, Periode, Land) wird der Plan abgelehnt, damit nichts gelöscht wird. | `test_i7_snapshot_plan_modes`, `test_i7_snapshot_without_context_is_rejected` |
| I8 | Alle drei Betragsvarianten lesen deutsche Beträge mit Tausenderpunkten und Dezimalkomma; nur bei reinen Punktgruppen (`1.234.567`) unterscheiden sie sich wie dokumentiert (flowworkshop `None`, Designer liest sie). | `test_i8_amount_variants_stay_separate` |
| I9 | flowsearch liest fehlende oder unlesbare Beträge als 0,0 (Quellverhalten), der Designer als `None`; die flowsearch-Identität ist deterministisch, 16 Hex (MD5). | `test_i9_flowsearch_defaults_and_md5_identity` |
| I10 | Die Behördenebene ist „Bund“, ein Land oder „unbestimmt“ – nie ein geratener Wert. | `test_i10_authority_level_is_closed` |

## Fehlerfälle

| Fall | Ergebnis |
|---|---|
| Unbekannter Modus, leerer Quellschlüssel, keine Zeile mit Begünstigtennamen | `ValueError` |
| Quellenkontext fehlt, negative Kosten, EU-Anteil größer als Gesamtkosten, Beginn nach Ende, Koordinaten außerhalb, zu viele namenlose Zeilen | `SnapshotRejected` mit allen Meldungen – der alte Bestand bleibt |
| Stichtag kein `date` | `TypeError` |
| Unerwartete Registerantwort | `RegisterResponseError` (`parse_award_list(strict=True)`) |
| Leere oder unlesbare Datei im Adapter | `ParserError` statt leerem Erfolg (FS-S04) |
| Kein gültiges ZIP, Tabellendatei im Archiv über 64 MiB | `SourceFormatError` statt Einlesen (FS-S03) |
| Unlesbarer Betrag | `None` (flowworkshop, Designer) bzw. 0,0 mit Eintrag in `defaulted` (flowsearch) |
| Designer `parse_amount(True)` | `InvalidOperation` wie im Original (FS-G01) |

## Abgrenzung

- Keine Datenbank, kein Scheduler; ein `SnapshotPlan` wird vom Consumer
  ausgeführt.
- Keine fachliche Beurteilung einer Kumulierung, keine Förderreserve, keine
  Prüfung der Unternehmenseigenschaft (Art. 2 Abs. 2 VO (EU) 2023/2831) – die
  Referenzen eines Unternehmens übergibt der Aufrufer.
- Keine Zusammenführung der Varianten flowworkshop, flowsearch und Designer.
- Datenlizenzen und Nutzungsbedingungen der Quellen prüft der Consumer.

## Bewusste Abweichungen vom Altverhalten

Vollständige Liste FS-W01 bis FS-W08, FS-S01 bis FS-S04, FS-G01, FS-D01 bis
FS-D07 in [behavior-changes.md](behavior-changes.md). Die Profilmodule
reproduzieren die Originale exakt; Korrekturen sind nur als ausdrücklich
gewählte Option oder im neuen Vertrag wirksam.

| Altverhalten | Gewollt | Legacy-Variante | Nachweis |
|---|---|---|---|
| pandas-Typinferenz: PLZ `01067` → `1067`, `150000` → `150000.0` je nach Dateikontext (FS-W02, FS-W03) | Text bleibt Text | `typing="legacy"` (Standard, weil Umstellung Identitäten ändert; HUMAN_DECISION_REQUIRED) | `tests/test_tables.py` |
| Erste numerische Datenzeile gilt als zweite Kopfzeile, Datenverlust (FS-W08) | Zweitkopfzeile nur mit Buchstaben | `header_detection="legacy"` | `tests/test_tables.py` |
| Unerwartete Registerantwort wird „kein Treffer“ (FS-D01) | Fehler | `parse_award_list(strict=False)` | `tests/test_deminimis.py` |
| Bestandsstand nach Fehllauf als vollständig gemeldet (FS-D02) | neuester Lauf, vollständig nur bei `ok` | `inventory_state(..., legacy=True)` | `tests/test_deminimis.py` |
| Negative Beträge mindern die Summe, alle Referenzen werden summiert, Stichtag „heute“ (FS-D05 bis FS-D07) | `unclear`, Unternehmen ausdrücklich, Stichtag Pflicht (I4, I5) | `cumulation.legacy_cumulation` | `tests/test_cumulation.py` |
| Alte Designer-Namen | neue Namen | `parse_betrag`, `parse_satz`, `parse_datum` (Aliase mit `DeprecationWarning`) | `tests/test_designer_aliases.py` |
| Quellkontext in der Identität leer (FS-W01), fehlender Betrag 0,0 (FS-S01) | unverändert, dokumentiert | – | I6, I9 |

Keine offenen Befunde aus den Eigenschaftstests.
