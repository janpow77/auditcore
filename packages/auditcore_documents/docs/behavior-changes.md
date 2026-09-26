# Legacyverhalten und bewusst korrigiertes Verhalten

Quelle: `janpow77/audit_designer@030a71e083ef` (`backend/app/modules/document_compare`,
Blobs in `provenance.json`), tatsächlich ausgeführt mit `tools/capture_legacy.py`
in einer Umgebung wie der laufende `audit_designer_backend` (Python 3.11.16,
lxml 5.1.0, python-docx 1.1.0, pypdf 6.16.2, rapidfuzz 3.14.5, pdftotext 22.12.0,
TZ Europe/Berlin). Aufgezeichnet: 19 Normalisierungen, 7 Wortdifferenzen,
14 Ähnlichkeitswerte, 61 Lesefälle, 29 Modus-Erkennungen, 6 PDF-Extraktionen,
7 Seitenregeln, 62 Standardvergleiche (31 Fälle × 2 Ähnlichkeitsmaße),
7 Gesetzessynopsen, 31 Einstellungs-, 5 Schichtungs-, 4 Lade- und 1 Speicherfall,
5 Fundstellenprüfungen, 6 Begründungsantworten, 8 DOCX-Renderings,
3 CLI-Läufe, 5 Celery-Abläufe und 5 ecohesion-Worker-Läufe (davon 4 mit echter
PDF-Synopse über `research_pdf.render_pdf`, reportlab 4.0.8, DejaVuSans). Zwei Läufe mit
unterschiedlichem `PYTHONHASHSEED` sind byte-gleich. Die 9 Originaltests
bestehen gegen das Original und – umgestellt – gegen die Bibliothek.

Das Profil `LEGACY` (`audit_designer.document_compare` 1.1.0) reproduziert alle
aufgezeichneten Fälle exakt, einschließlich DOCX-Hauptteil, Kopf- und Fußzeile
(python-docx 1.1.0). Abweichungen gibt es nur hier:

## Korrekturen (DC-C)

| ID | Original | Bibliothek | Begründung |
|---|---|---|---|
| DC-C01 | Ähnlichkeitsmaß still nach Umgebung: `rapidfuzz.fuzz.token_set_ratio`, bei `ImportError` `difflib`. Beide ordnen verschieden zu (KassenSichV DOCX: 12 statt 7 geänderte Absätze). | Maß ist Profilbestandteil; fehlt rapidfuzz, `DependencyError`. Der Rückfall ist als Profil `LEGACY_DIFFLIB` ausdrücklich wählbar. | Ergebnisse dürfen nicht von zufällig installierten Paketen abhängen. |
| DC-C02 | `etree.fromstring` mit Standardparser. Mit lxml 5.1 werden interne Entitäten aufgelöst, externe nicht; **mit lxml 4.9.2 (Debian bookworm) liest der Originalcode eine externe Entität `file:///etc/hostname` in den Vergleichstext ein** (im Debian-Container nachgewiesen). | Gehärteter Parser (`resolve_entities=False`, keine DTD, kein Netz, keine übergroßen Bäume); Dokumente mit DTD werden mit `ParseError` abgewiesen. Extra `docx` verlangt lxml ≥ 6.1.0. | XXE/lokale Dateioffenlegung (CVE-2026-41066, pip-audit PYSEC-2026-87 für lxml < 6.1.0, betrifft die Produktionsfassung lxml 5.1.0 des Consumers); Word schreibt keine DTD. |
| DC-C03 | Keine Größen-/Seitengrenzen (nur der ecohesion-Worker setzt `RLIMIT_CPU`/`RLIMIT_AS`). | `ReadLimits`: Datei 512 MiB, entpacktes `document.xml` 128 MiB, 5000 PDF-Seiten, pdftotext 120 s; Überschreitung `LimitExceededError`. | Schutz vor ZIP-Bomben; Vorgaben ändern keinen charakterisierten Fall. |
| DC-C04 | Das Änderungsdokument wird als Fließtext gelesen; Absätze, die mit „§“ beginnen, gelten als **Überschrift** und nie als Befehl. Die Muster „§ … wird aufgehoben“ und „§ … Absatz … wird wie folgt gefasst“ können deshalb nie greifen (Fall `al_befehle`: 3 statt 5 erkannte Befehle). | Profil `CORRECTED` (`auditcore.document_compare` 2026.09.1) liest jeden Absatz als möglichen Befehl und nennt sich in `metadata["profile"]`. `LEGACY` bleibt unverändert. | Offensichtlicher Defekt; **DECIDED** (D1, 2026-09-23): `CORRECTED` ist das empfohlene Profil (siehe unten). |
| DC-C05 | `subprocess.run(..., text=True)` dekodiert pdftotext-Ausgabe nach Gebietsschema; Pfade mit führendem „-“ würden als Option gelesen. | Ausdrücklich UTF-8 (sonst `ParseError`); führendes „-“ wird als `./-…` übergeben. | Umgebungsunabhängigkeit, Argumentinjektion. |
| DC-C06 | Nicht-Objekt-JSON des KI-Dienstes (`[1, 2]`) führt zu `AttributeError`. | `CompareError` „keine gültige JSON-Begründung“; Anbieter dürfen auch ein Mapping liefern. | Einheitlicher Fehlervertrag. |
| DC-C07 | `load_settings`/`save_settings` lesen ohne Pfad `AUDIT_DOCUMENT_COMPARE_CONFIG` bzw. `~/.config/audit_designer/…`. | Pfad ist Pflicht; der Standardpfad des Originals liegt in `legacy.audit_designer_config_path()`. | Eine Bibliothek liest keine Anwendungsumgebung. |
| DC-C08 | `generate_reason` importiert `app.modules.standards.mcp_tools` (FlowAgent). | Port `ReasonProvider`; `mcp_tool_provider(execute)` bildet den Aufruf `("document_compare_reason", {"alt", "neu", "modell"})` exakt nach. Ohne Port: `CompareError`. | Keine KI-Abhängigkeit im Kern. |
| DC-C09 | `ParseError(ValueError)` getrennt von `CompareError(ValueError)`, die Fassade übersetzt. | `ParseError`, `DependencyError`, `LimitExceededError` sind Unterklassen von `CompareError`; Texte unverändert. | Ein `except CompareError` erfasst alle fachlichen Fehler. |
| DC-C11 | PDF-Synopse über ECOHESION `research_pdf.render_pdf` mit festen Texten „ECOHESION · Recherche & Auswertung“, „ecohesion.flowaudit.de“, Autor „ECOHESION“ und fest verdrahtetem Schriftpfad. | `render_synopsis_pdf`: Kopf-, Fußzeile, Autor und Schriftdatei sind Parameter; Vorgaben sind die Originaltexte. Seitentext, Titel und Autor sind mit reportlab 4.0.8 (Original) und 5.0.1 gleich. | Nutzbar außerhalb von ECOHESION ohne Codekopie. |
| DC-C10 | Uhr, PDF-Seitenquelle und Protokollierung fest verdrahtet (`logger.warning` in der Celery-Schleife). | `ReadContext(now, page_source, ocr_callback, limits)`; `apply_reasons_worker(on_progress, on_error)`; die Bibliothek protokolliert nicht. | Testbarkeit, T-14. |

## Beibehaltenes, fachlich fragwürdiges Originalverhalten (DC-L)

| ID | Verhalten | Status |
|---|---|---|
| DC-L01 | „Nach § 3 Absatz 1 wird folgender Absatz 2 eingefügt“ nummeriert die folgenden Absätze nicht um; danach gibt es zweimal „§ 3 Absatz 2“, spätere Befehle treffen den eingefügten. | **DECIDED** (D2, 2026-09-23): Im Profil `CORRECTED` (ab 2026.09.2) rücken die folgenden Absätze desselben Paragraphen um eins auf; spätere Befehle treffen die ursprünglichen Absätze. `LEGACY` bleibt unverändert. |
| DC-L02 | Ersetzungsbefehle ersetzen **jedes** Vorkommen im Absatz; Angaben zu Satz, Nummer oder Buchstabe („In § 11 Absatz 1 Satz 1 …“) werden überlesen. Bei der KassenSichV (einmaliges Vorkommen) ist das Ergebnis korrekt. | **DECIDED** (D2, 2026-09-23): Ersetzungen treffen weiterhin **alle** Vorkommen im Absatz – in `LEGACY` und `CORRECTED`. |
| DC-L03 | Nur Befehle auf Absatzebene im Stil „wird wie folgt gefasst“. Die seit 2024 übliche Formulierung „wird durch den folgenden … ersetzt“ (BGBl. 2026 I Nr. 223) und Nummern-/Satzbefehle bleiben „offen“. | Funktionserweiterung, keine Entscheidung; offene Befehle werden sichtbar ausgewiesen. |
| DC-L04 | PDF-Zeilenumbruch nach Bindestrich wird zusammengezogen: „BSI-\nGesetzes“ → „BSIGesetzes“ (BGBl.-Seite 55). | beibehalten, dokumentiert. |
| DC-L05 | Modus „auto“ erkennt eine DOCX-Checkliste erst ab 6 Tabellenzeilen; kleinere Checklisten gelten als Fließtext und scheitern mit „keine vergleichbaren Textstellen“. | beibehalten (charakterisierte Fälle 2, 24, 25). |
| DC-L06 | Umgestellte Zeilen (`moved`) fehlen in der Sortiertabelle und stehen am Ende. | beibehalten. |
| DC-L07 | Absätze eines PDF entstehen an Satzenden, nicht an Gesetzesabsätzen; mit der amtlichen KassenSichV-PDF als Stammgesetz wird „§ 11 Absatz 1“ deshalb nicht gefunden (Fall 3), mit der DOCX-Fassung schon. | beibehalten; für Synopsen DOCX-Stammtexte verwenden. |
| DC-L08 | Zeitangaben im DOCX (`geändert …`, `Erstellt …`) in lokaler Prozesszeitzone. | beibehalten. |
| DC-L09 | Die Reihenfolgenwahl bei gleichem Ähnlichkeitswert ist „erster Kandidat“. | beibehalten. |

## Entscheidungen

Entschieden am **2026-09-23** durch den Nutzer (Zitat: „alle empfehlungen“).
Status vorher: HUMAN_DECISION_REQUIRED, jetzt **DECIDED**.

| Nr. | Frage | Entscheidung | Umsetzung |
|---|---|---|---|
| D1 | Übernahme von DC-C04 (Profil `CORRECTED`) statt `LEGACY` | `CORRECTED` ist das empfohlene Vergleichsprofil. | `auditcore_documents.RECOMMENDED is CORRECTED`, Status `DECIDED_RECOMMENDED`, Version 2026.09.2 (`result_version` `1.1.0+auditcore.2026.09.2`); CLI-Voreinstellung `auditcore.document_compare`. |
| D2 | DC-L01/DC-L02: Zählweise nach Einfügung, Umfang von Ersetzungen | Absatznummerierung korrigiert; Ersetzungen treffen alle Vorkommen. | Profilfeld `renumber_after_insert=True` in `CORRECTED`; `apply_commands(..., renumber_after_insert=...)`. |
| D3 | Vergleich ohne rapidfuzz | Klarer Fehler statt stillem Rückfall auf difflib. | Empfohlenes Profil verlangt rapidfuzz (`DependencyError`); `LEGACY_DIFFLIB` bleibt ausdrücklich wählbar. |

`LEGACY` und `LEGACY_DIFFLIB` bleiben bitgenau, einschließlich ihrer
Fingerabdrücke (`test_legacy_fingerprints_are_stable`). Die Pipeline-Entscheidungen
D4 bis D8 stehen in `docs/pipeline.md`.

## 0.2.0: Donut (additiv)

| ID | Änderung | Wirkung auf bestehende Profile |
|---|---|---|
| DN-01 | `OcrBackend.DONUT`, `OcrStage(donut=…)`, `DonutPort`/`HttpDonut`/`FakeDonut`/`LocalDonut` | keine: nur bei `backend="donut"` aktiv |
| DN-02 | `DonutFieldMergeStage`, Regeln `VAL_DONUT_PLAUSIBILITY`/`VAL_DONUT_DISAGREEMENT` | nur in `DONUT_PIPELINE` |
| DN-03 | `PipelineProfile.ocr_backend`, `donut_min_field_confidence` (Vorgabe `None`) | Fingerabdrücke von `LEGACY_PIPELINE` und `CORRECTED_PIPELINE` unverändert (Vorgabewerte fließen nicht ein) |
| DN-04 | `PIPELINE_PROFILES` enthält zusätzlich `auditcore.pipeline.donut` | Registry erweitert |

## 0.3.2 – Befund für mehrdeutige Beträge

| Fall | bis 0.3.1 | ab 0.3.2 |
|---|---|---|
| `locale-aware`, Betrag `1.234` | Wert `None`, kein Befund in der Nachverarbeitung | Wert `None`, Befund `ambiguous` aus `normalize_fields_checked`, Flag `AMOUNT_AMBIGUOUS_TOTAL` |
| `locale-aware`, Betrag `12,5,0` | Wert `None`, kein Befund | Wert `None`, Befund `invalid`, Flag `AMOUNT_INVALID_<FELD>` |
| `legacy-de` | Wert geraten wie im Original | unverändert, keine Flags |

