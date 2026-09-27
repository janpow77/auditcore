# Spezifikation auditcore_documents

Stand: 27.09.2026, Paketversion 0.4.0 (mit Bestandsprüfung, noch nicht veröffentlicht). Charakterisierung: Dokumentvergleich
gegen `janpow77/audit_designer@030a71e083ef` (`document_compare`, u. a.
62 Standardvergleiche, 7 Gesetzessynopsen, 61 Lesefälle, 8 DOCX-Renderings;
`docs/behavior-changes.md`), Dokumentpipeline gegen
`janpow77/flowinvoice@fb2d18568d2e` (30 vollständige Läufe; `docs/pipeline.md`).
Eigenschaftstests: `tests/test_spezifikation.py` (I1–I10) und
`tests/test_spezifikation_bestand.py` (I11–I16, Bestandsprüfung und Regelmeldungen).

## Zweck

Das Paket vergleicht zwei Fassungen eines Dokuments – Checklisten (Tabellen)
und Fließtext aus DOCX/DOCM/PDF – und bereitet die Unterschiede als Synopse
auf; für Artikelgesetze wendet es die Änderungsbefehle auf das Stammgesetz an.
Daneben enthält es einen frameworkunabhängigen Kern der Dokumentpipeline
(Einlesen, OCR über Ports, Feldextraktion, Validierung, Hashing, Aufbewahrung)
für die Belegerkennung und eine Bestandsprüfung über viele Belege
(Extraktionsqualitäts-Watchdog C-01 bis C-13, A-07, B-12 und die Ergänzungen
ERG-01 Nummernlücken, ERG-02 USt-IdNr.-Konsistenz). Ein Vergleich ist eine Arbeitshilfe für Prüferinnen und
Prüfer: Er stellt Unterschiede fest, trifft aber keine Prüfungsentscheidung.

## Verträge

| Baustein | Eingabe | Ausgabe | Nebenwirkungen |
|---|---|---|---|
| `read_document(path, mode="auto", …)` | DOCX/DOCM/PDF, Modus `auto`/`checklist`/`text` | erkannte Dokumentart und `CompareItem`s | liest die Datei; Grenzen `ReadLimits` |
| `compare_items(old, new, *, mode, profile, threshold=85, include_answers=True, include_notes=True, include_editorial=False)` | Vergleichseinheiten zweier Fassungen, Profil | (`CompareRow`s, Zählwerte `old_count`, `new_count`, `matched_count`, `changed_count`, `removed_count`, `added_count`, `moved_count`) | keine (reiner Kern) |
| `compare_files(old, new, *, profile, options=None, context=None)` | zwei Dateien, Profil, `CompareOptions`, `ReadContext` (Uhr, Seitenquelle, OCR-Rückruf, Grenzen) | `ComparisonResult` (JSON-fähig, `to_dict`/`from_dict`) | liest beide Dateien |
| `compare_article_law_files` / `base_paragraphs` / `apply_commands(paragraphs, commands, *, renumber_after_insert=False)` | Stammgesetz, Änderungsbefehle | Synopse; Absätze mit neuer Fassung, Aufhebung, Einfügung; offene Befehle; Zahl erkannter Befehle | `apply_commands` verändert die übergebenen Absätze |
| `normalise_for_match`, `normalise_semantic`, `normalise_verbatim`, `word_diff` | Text; `normalise_for_match`/`normalise_semantic` zusätzlich `numbering="once"` (Standard, Original) oder `"all"` (idempotent) | normalisierter Text bzw. Wortdifferenz (`difflib.ndiff`) | – |
| `difflib_ratio`, `rapidfuzz_token_set`, `get_scorer` | zwei Texte | ganzzahlige Ähnlichkeit 0…100 | `rapidfuzz` nur im Extra `fuzzy` |
| `synopsis_records`, `render_docx` (Extra `docx-render`), `render_pdf` (Extra `pdf-render`) | Ergebnis | Tabellenzeilen bzw. Dokumentbytes | schreibt nur ausdrücklich benannte Ausgaben |
| `generate_reason`, `verify_legal_references`, `apply_reasons_*` | Zeilen, Port `ReasonProvider` | Begründungsvorschläge mit geprüften Fundstellen | ohne Port kein Netz (`CompareError`) |
| `load_settings`, `save_settings`, `merge_settings`, `sanitise_settings` | Pfad bzw. Einstellungen | bereinigte Einstellungen | `save_settings` schreibt atomar |
| `auditcore_documents.pipeline` (`build_pipeline`, `HashingService`, `RetentionSweeper`, Watchdog) | Dokument, Profil `LEGACY_PIPELINE` oder `CORRECTED_PIPELINE` (= `RECOMMENDED_PIPELINE`), Ports | Kontext mit Stufenergebnissen, Stufen-Hashes, Audit-Ereignissen | nur über Ports (Speicher, OCR, HTTP, Export) |
| `BatchCheckService.check(payload)` / `.export(payload)` (Vertrag `documents_batch_checks/1`, `docs/ui/batch-checks-rest.md`) | Belege als flache Datensätze oder Läufe von `documents_extraction/1`, Optionen (`total_volume`, Schwellen, `supplementary`) | Antwort mit `summary`, `metrics` (C-12), Status aller Regeln, Befunden mit Begründung und betroffenen Belegen, `documents`; Export JSON (C-11) oder CSV | keine; der Dienst speichert nichts |
| `pipeline.watchdog.inventory_checks` (`check_invoice_number_gaps`, `check_vat_id_consistency`) | Beleg-Datensätze, `WatchdogResult` | ergänzt Befunde ERG-01/ERG-02 | nur am übergebenen Ergebnis |
| `pipeline.stages.rule_messages` (`say`, `german_message`, `original_message`) | Meldungskennung bzw. Text | deutsche Meldung bzw. englischer Originalwortlaut | – |
| `auditcore_documents.web` (Extras `web`/`fastapi`) | REST-Anfragen der Synopse-Oberfläche und der Belegerkennung | JSON-Antworten | keine Authentifizierung; Eigentümer je Anfrage über `identify` |

Profile des Vergleichs: `CORRECTED` = `RECOMMENDED` (`auditcore.document_compare`
2026.09.2, verlangt `rapidfuzz`), `LEGACY` (Original mit rapidfuzz) und
`LEGACY_DIFFLIB` (Original ohne rapidfuzz). Das Profil steht in
`metadata["profile"]` jedes Ergebnisses.

## Invarianten

| Nr. | Invariante | Test |
|---|---|---|
| I1 | `normalise_verbatim` ist idempotent; `normalise_for_match` und `normalise_semantic` sind es mit `numbering="all"` für beliebige Texte, im Standard `numbering="once"` (Original) für Texte, die mit einem Wort beginnen (Befund B1, behoben durch die Variante `"all"`). | `test_i1_normalisation_is_idempotent`, `test_i1_numbering_all_is_idempotent`, `test_i1_numbering_once_keeps_original_behaviour` |
| I2 | `normalise_verbatim` hängt nicht von Art und Menge des Leerraums zwischen den Wörtern ab. | `test_i2_verbatim_ignores_whitespace_layout` |
| I3 | `word_diff(a, a)` ist leer; sonst ergeben die Zeilen mit „- “/„  “ die alte und die mit „+ “/„  “ die neue Wortfolge. | `test_i3_word_diff_reconstructs_both_versions` |
| I4 | Vergleich einer Fassung mit sich selbst (beide Modi, Profile `RECOMMENDED` und `LEGACY_DIFFLIB`): alle Einheiten zugeordnet, keine geänderte, entfallene, hinzugefügte oder umgestellte Zeile, keine Zeile vorausgewählt. | `test_i4_comparison_with_itself_finds_no_change` |
| I5 | Jede Einheit wird genau einmal verbucht: alt = zugeordnet + entfallen + umgestellt, neu = zugeordnet + hinzugefügt + umgestellt; zugeordnet = unverändert + geändert; Zeilenzahl = zugeordnet + entfallen + hinzugefügt + umgestellt. | `test_i5_every_unit_is_accounted_for_once` |
| I6 | `ComparisonResult.from_dict(r.to_dict()) == r`. | `test_i6_result_survives_dict_round_trip` |
| I7 | Ähnlichkeitsmaße liegen in 0…100; identische Texte ergeben 100 (`token_set` für nichtleere Texte); `rapidfuzz_token_set` ist symmetrisch. | `test_i7_similarity_is_bounded_and_full_for_identity` |
| I8 | `base_paragraphs` zählt die Absätze je Paragraf ab 1 lückenlos und übernimmt den Text unverändert. | `test_i8_base_paragraphs_count_per_section` |
| I9 | Zeilen ohne erkennbaren Änderungsbefehl werden übergangen: kein erkannter, kein offener Befehl, Stammtext unverändert. | `test_i9_lines_without_command_are_skipped` |
| I10 | `HashingService.linked_chain` ist deterministisch, präfixstabil und reihenfolgeabhängig; `verify_chain` bestätigt den eigenen Kettenhash jeder nichtleeren Kette. | `test_i10_linked_chain_is_prefix_stable_and_order_sensitive` |
| I11 | Jede Regelmeldung der Validierungsstufe lässt sich verlustfrei zwischen deutscher Fassung und englischem Originalwortlaut umrechnen (`original_message(say(code, …))` = Original, `german_message(Original)` = `say(code, …)`). | `test_i11_rule_messages_convert_both_ways` |
| I12 | Die Antwort der Bestandsprüfung verbucht jeden Befund genau einmal: Zahl der Befunde in `summary` = Länge von `findings` = Summe über `rules[].findings`; jeder Befund gehört zu einer Katalogregel, betroffene Belege liegen im Bestand, `documents_with_findings` ist ihre Vereinigung, Nummern `B-0001…` lückenlos; Status `findings` genau bei mindestens einem Befund. | `test_i12_answer_accounts_for_every_finding` |
| I13 | Der JSON-Export ist die Antwort von `POST /runs`; die CSV hat je Befund und betroffenem Beleg eine Zeile (Gesamtbefunde eine). | `test_i13_export_matches_the_run` |
| I14 | ERG-01 meldet genau die fehlenden Zählwerte zwischen zwei vorhandenen Nummern mit Abstand ≤ 50 und nie eine vorhandene Nummer. | `test_i14_gaps_lie_between_present_numbers` |
| I15 | Die Ergänzungsprüfungen ändern weder Eskalation (C-10), Blockade noch Kennzahlen, und die Katalogbefunde bleiben dieselben. | `test_i15_supplementary_checks_do_not_change_escalation` |
| I16 | Ein Lauf der Belegerkennung als Beleg ergibt dieselben Befunde, Regelstatus und Belegzeilen wie der entsprechende flache Datensatz. | `test_i16_extraction_runs_equal_flat_records` |

### Befunde aus den Eigenschaftstests

- **B1 (behoben)** – `normalise_for_match` entfernt im Original je Durchgang
  nur **eine** führende Nummerierung; `normalise_semantic` legt durch das
  Entfernen von Satzzeichen weitere führende Ziffern frei. Beispiele:
  „1. 2. Text“ → „2. text“ → „text“; „:0“ → „0“ → „“. Neu:
  `numbering="all"` wendet den Schritt bis zum Fixpunkt an und ist für
  beliebige Texte idempotent (`test_i1_numbering_all_is_idempotent`). Der
  Standard bleibt `numbering="once"` (Legacy-Variante), weil alle
  Vergleichsprofile – auch `RECOMMENDED` – die Zuordnungsschlüssel damit
  bilden und die Vergleichsergebnisse charakterisiert sind; ein Wechsel der
  Zuordnung auf `"all"` gehört in eine neue Profilversion.

## Fehlerfälle

| Eingabe | Ergebnis |
|---|---|
| beschädigte, geschützte, nicht unterstützte oder unlesbare Datei; DOCX mit DTD; keine vergleichbaren Textstellen | `ParseError` bzw. `CompareError` (gleiche Meldung) |
| fehlendes Extra (lxml, pypdf, rapidfuzz, python-docx); `RECOMMENDED` ohne rapidfuzz | `DependencyError` (kein stiller Wechsel auf difflib) |
| Datei > 512 MiB, entpacktes `document.xml` > 128 MiB, > 5 000 PDF-Seiten, pdftotext > 120 s | `LimitExceededError` |
| unbekannter Vergleichstyp, ungültige Optionen, Begründung ohne Port oder mit ungültigem JSON | `CompareError` |
| Stammgesetz ohne „§ …“-Überschriften | `ValueError` („keine Paragrafen mit Absätzen“) |
| unbekannte Felder in `ComparisonResult.from_dict` | `ValueError` |
| nicht anwendbarer Änderungsbefehl | kein Fehler: Befehl bleibt mit Grund offen |

Bestandsprüfung (`BatchCheckError`, Unterklasse von `auditcore_common.rest.ContractError`,
HTTP-Status im Fehlerkörper): kein JSON → 400 `invalid_json`; Körper zu groß
oder mehr als `max_documents` Belege → 413; leere Belegliste, Beleg kein
Objekt, Feldwert weder Text noch Zahl, OCR-Konfidenz außerhalb 0…1,
unzulässige Option, unbekanntes Exportformat → 422 `invalid_input`. Unlesbare
Beträge sind kein Fehler, sondern werden als Befund gemeldet (A-07, C-01).

`ParseError`, `DependencyError` und `LimitExceededError` sind Unterklassen von
`CompareError`.

## Abgrenzung

- Keine Prüfungsentscheidung, keine Bewertung der Unterschiede; die Auswahl
  der Zeilen für die Synopse trifft der Mensch.
- Keine Speicherung, kein Web-Login, keine Celery- oder KI-Abhängigkeit im
  Kern; KI-Begründungen nur über den Port `ReasonProvider`.
- Gesetzessynopse nur für Befehle auf Absatzebene („wird wie folgt gefasst“,
  „wird aufgehoben“, „eingefügt“, Wortersetzungen); Satz-, Nummern- und
  Buchstabenbefehle bleiben offen (DC-L03).
- Die Bestandsprüfung bewertet Extraktionsqualität und formale Merkmale; ihre
  Befunde sind Hinweise zur Nachprüfung, keine Feststellungen. Steuersätze und
  Pflichtangaben folgen dem deutschen UStG (§§ 12, 14), wie im Katalog.
- OCR-Modelle, Rasterung und Gateway-Aufrufe liegen hinter Ports; die
  Bibliothek lädt kein Modell aus dem Netz.

## Bewusste Abweichungen vom Altverhalten

Korrekturen (vollständig in `docs/behavior-changes.md` DC-C01…DC-C11 und
`docs/pipeline.md` PL-C01…PL-C08):

| Altverhalten | Gewolltes Verhalten | Nachweis |
|---|---|---|
| Ähnlichkeitsmaß wechselte still nach installierten Paketen | Maß ist Profilbestandteil; fehlt rapidfuzz, `DependencyError` (DC-C01) | `tests/test_contract.py` |
| XML-Parser löste Entitäten auf (XXE) | gehärteter Parser, DTD → `ParseError` (DC-C02) | `tests/test_contract.py` |
| keine Größen-/Seitengrenzen | `ReadLimits` (DC-C03) | `tests/test_contract.py` |
| „§ … wird aufgehoben“ nie als Befehl gelesen | im Profil `CORRECTED` gelesen (DC-C04, D1) | `tests/test_decisions.py` |
| keine Umnummerierung nach Einfügung | `renumber_after_insert` in `CORRECTED` (DC-L01, D2) | `tests/test_decisions.py` |
| Regelmeldungen der Validierungsstufe englisch | deutsch mit echten Umlauten, Codes/Ergebnisse unverändert (D9) | `tests/test_pipeline_replay.py`, `tests/test_spezifikation_bestand.py` (I11) |
| Watchdog nur als Bibliotheksfunktion, keine Nummernlücken-/USt-IdNr.-Prüfung | REST-Vertrag `documents_batch_checks/1`, Ergänzungen ERG-01/ERG-02 außerhalb der Eskalation | `tests/test_batch_checks.py`, I12–I16 |
| REVIEW_NEEDED wurde als OK gemeldet; IBAN-Muster lief über Zeilenenden | in `CORRECTED_PIPELINE` korrigiert (PL-C01, PL-C02) | `tests/test_pipeline_units.py` |

Beibehaltenes Altverhalten (Legacy-Varianten, bitgenau und mit stabilen
Fingerabdrücken; für neue Aufrufer gelten `RECOMMENDED` bzw.
`RECOMMENDED_PIPELINE`):

| Legacy-Variante | Verhalten |
|---|---|
| `LEGACY` | Original mit rapidfuzz: „§“-Absätze nie Befehle, keine Umnummerierung, Ersetzungen treffen alle Vorkommen im Absatz (DC-L02, auch in `CORRECTED`) |
| `LEGACY_DIFFLIB` | Original ohne rapidfuzz (difflib-Rückfall, andere Zuordnung) |
| `LEGACY_PIPELINE` | flowinvoice-Pipeline mit PL-L01…PL-L10 (u. a. englische Zahlenformate deutsch gelesen, Gateway-Ausfall → REJECTED, nur eine Aufbewahrungsfrist wirksam) |
| `numbering="once"` | Standard von `normalise_for_match`/`normalise_semantic`: genau eine führende Nummerierung je Aufruf, nicht idempotent (B1); Grundlage der Zuordnung in allen Vergleichsprofilen |
| `legacy_pdf_pages` | Originalreihenfolge der PDF-Textquelle: erst `pdftotext`, bei Fehlen/Fehler `pypdf` |
| `legacy.audit_designer_config_path` | Standardpfad der Einstellungsdatei des Originals (die Bibliothek liest selbst keine Umgebung) |

Weitere beibehaltene, dokumentierte Eigenheiten ohne eigenen Schalter:
Bindestrich-Zeilenumbruch im PDF wird zusammengezogen (DC-L04), DOCX-Checklisten
erst ab sechs Tabellenzeilen erkannt (DC-L05), umgestellte Zeilen stehen am Ende
(DC-L06), PDF-Absätze an Satzenden (DC-L07), bei gleichem Ähnlichkeitswert
gewinnt der erste Kandidat (DC-L09).
