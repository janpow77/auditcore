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
3 CLI-Läufe, 5 Celery-Abläufe und 3 ecohesion-Worker-Läufe. Zwei Läufe mit
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
| DC-C04 | Das Änderungsdokument wird als Fließtext gelesen; Absätze, die mit „§“ beginnen, gelten als **Überschrift** und nie als Befehl. Die Muster „§ … wird aufgehoben“ und „§ … Absatz … wird wie folgt gefasst“ können deshalb nie greifen (Fall `al_befehle`: 3 statt 5 erkannte Befehle). | Profil `CORRECTED` (`auditcore.document_compare` 2026.09.1) liest jeden Absatz als möglichen Befehl und nennt sich in `metadata["profile"]`. `LEGACY` bleibt unverändert. | Offensichtlicher Defekt; die Umstellung ändert Ergebnisse → HUMAN_DECISION_REQUIRED (siehe unten). |
| DC-C05 | `subprocess.run(..., text=True)` dekodiert pdftotext-Ausgabe nach Gebietsschema; Pfade mit führendem „-“ würden als Option gelesen. | Ausdrücklich UTF-8 (sonst `ParseError`); führendes „-“ wird als `./-…` übergeben. | Umgebungsunabhängigkeit, Argumentinjektion. |
| DC-C06 | Nicht-Objekt-JSON des KI-Dienstes (`[1, 2]`) führt zu `AttributeError`. | `CompareError` „keine gültige JSON-Begründung“; Anbieter dürfen auch ein Mapping liefern. | Einheitlicher Fehlervertrag. |
| DC-C07 | `load_settings`/`save_settings` lesen ohne Pfad `AUDIT_DOCUMENT_COMPARE_CONFIG` bzw. `~/.config/audit_designer/…`. | Pfad ist Pflicht; der Standardpfad des Originals liegt in `legacy.audit_designer_config_path()`. | Eine Bibliothek liest keine Anwendungsumgebung. |
| DC-C08 | `generate_reason` importiert `app.modules.standards.mcp_tools` (FlowAgent). | Port `ReasonProvider`; `mcp_tool_provider(execute)` bildet den Aufruf `("document_compare_reason", {"alt", "neu", "modell"})` exakt nach. Ohne Port: `CompareError`. | Keine KI-Abhängigkeit im Kern. |
| DC-C09 | `ParseError(ValueError)` getrennt von `CompareError(ValueError)`, die Fassade übersetzt. | `ParseError`, `DependencyError`, `LimitExceededError` sind Unterklassen von `CompareError`; Texte unverändert. | Ein `except CompareError` erfasst alle fachlichen Fehler. |
| DC-C10 | Uhr, PDF-Seitenquelle und Protokollierung fest verdrahtet (`logger.warning` in der Celery-Schleife). | `ReadContext(now, page_source, ocr_callback, limits)`; `apply_reasons_worker(on_progress, on_error)`; die Bibliothek protokolliert nicht. | Testbarkeit, T-14. |

## Beibehaltenes, fachlich fragwürdiges Originalverhalten (DC-L)

| ID | Verhalten | Status |
|---|---|---|
| DC-L01 | „Nach § 3 Absatz 1 wird folgender Absatz 2 eingefügt“ nummeriert die folgenden Absätze nicht um; danach gibt es zweimal „§ 3 Absatz 2“, spätere Befehle treffen den eingefügten. | **HUMAN_DECISION_REQUIRED**: Zählweise nach Einfügung (amtlich folgt meist „Der bisherige Absatz 2 wird Absatz 3“, das nicht unterstützt ist). |
| DC-L02 | Ersetzungsbefehle ersetzen **jedes** Vorkommen im Absatz; Angaben zu Satz, Nummer oder Buchstabe („In § 11 Absatz 1 Satz 1 …“) werden überlesen. Bei der KassenSichV (einmaliges Vorkommen) ist das Ergebnis korrekt. | **HUMAN_DECISION_REQUIRED**: ob ohne „jeweils“ nur das erste Vorkommen bzw. nur der genannte Satz ersetzt werden soll. |
| DC-L03 | Nur Befehle auf Absatzebene im Stil „wird wie folgt gefasst“. Die seit 2024 übliche Formulierung „wird durch den folgenden … ersetzt“ (BGBl. 2026 I Nr. 223) und Nummern-/Satzbefehle bleiben „offen“. | Funktionserweiterung, keine Entscheidung; offene Befehle werden sichtbar ausgewiesen. |
| DC-L04 | PDF-Zeilenumbruch nach Bindestrich wird zusammengezogen: „BSI-\nGesetzes“ → „BSIGesetzes“ (BGBl.-Seite 55). | beibehalten, dokumentiert. |
| DC-L05 | Modus „auto“ erkennt eine DOCX-Checkliste erst ab 6 Tabellenzeilen; kleinere Checklisten gelten als Fließtext und scheitern mit „keine vergleichbaren Textstellen“. | beibehalten (charakterisierte Fälle 2, 24, 25). |
| DC-L06 | Umgestellte Zeilen (`moved`) fehlen in der Sortiertabelle und stehen am Ende. | beibehalten. |
| DC-L07 | Absätze eines PDF entstehen an Satzenden, nicht an Gesetzesabsätzen; mit der amtlichen KassenSichV-PDF als Stammgesetz wird „§ 11 Absatz 1“ deshalb nicht gefunden (Fall 3), mit der DOCX-Fassung schon. | beibehalten; für Synopsen DOCX-Stammtexte verwenden. |
| DC-L08 | Zeitangaben im DOCX (`geändert …`, `Erstellt …`) in lokaler Prozesszeitzone. | beibehalten. |
| DC-L09 | Die Reihenfolgenwahl bei gleichem Ähnlichkeitswert ist „erster Kandidat“. | beibehalten. |

## Offene Entscheidungen

1. Übernahme von DC-C04 (Profil `CORRECTED`) in audit_designer/ECOHESION statt `LEGACY`.
2. DC-L01 und DC-L02 (Zählweise nach Einfügung, Umfang von Ersetzungen).
3. Ob audit_designer ohne rapidfuzz überhaupt vergleichen darf (heute: Rückfall
   auf difflib; Bibliothek: Fehler, siehe DC-C01).
