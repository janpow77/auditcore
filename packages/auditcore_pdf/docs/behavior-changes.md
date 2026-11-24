# Verhalten gegenüber dem Original (pdf-editor)

`auditcore_pdf.redaction` übernimmt die Schwärzung aus
`janpow77/pdf-editor@c5b3e1d` (`backend/app/services/redaction.py`, ein
einzelnes Modul). Der Code (2 444 Zeilen) wurde in 22 Module zerlegt,
durchgehend typisiert (`mypy --strict`, ohne `Any`) und auf die
Qualitätsgrenzen von auditcore gebracht (Funktionen höchstens 60 Zeilen,
Komplexität höchstens 10). Fachlich ist nichts geändert. Einzige Ausnahme seit
0.3.0 ist die strengere Typprüfung von `Selection.from_dict` (siehe
Abweichungen).

## Nachweis

Die Gleichheit wurde am 23.11.2026 lokal nachgewiesen (Python 3.12,
PyMuPDF 2.1 mit MuPDF 1.28.6). Die Vergleiche brauchen das Original und sind
deshalb nicht als CI-Test in auditcore hinterlegt; dauerhaft sichern die
Bibliothekstests unter `tests/` und nach der Umstellung die Schwärzungstests
des pdf-editor in dessen CI.

- Golden-Vergleich: 44 synthetische Fälle aus dem Prüfkorpus, je in zwei
  Einstellungen (alle Muster ohne KI; alle Muster mit KI-Namen über spaCy
  3.7.5 mit `de_core_news_sm` 3.7.0 und Begriffen). Verglichen werden der
  vollständige Plan (`Plan.to_dict()` ohne Datei-Hash), der
  Anwendungsbericht bei Auswahl jeder zweiten Fundstelle und der Text der
  geschwärzten Ausgabe. Ergebnis: gleich in allen Fällen, nach jedem
  Umbauschritt erneut geprüft.
- Differenzieller Zufallstest von `Selection.from_dict` (alt gegen neu):
  keine Abweichung, auch bei ungültigen Eingaben (gleiche Fehlerklasse und
  Meldung). Das gilt für 0.2.0; seit 0.3.0 weist `from_dict`
  falsch typisierte Eingaben ab, die das Original umgedeutet hat.
- Unabhängige Gegenprüfung (Code-Audit): jeder Aufruf von `build_plan`,
  `apply_plan`, `redact_all` und `Selection.from_dict` aus den
  Bibliothekstests zusätzlich gegen das Original (362 Aufrufe),
  20 000 Zufallseingaben für `Selection.from_dict`, 30 000 Zufallstexte je
  Muster und 300 Dokumente mit einer Ersatz-NER, die zu einem Drittel
  ungültige Spannen liefert. Keine Abweichung in Plan, Bericht, Ausgabetext,
  Fehlerklasse und Meldung. Die Ausgabebytes selbst sind schon im Original
  nicht reproduzierbar; verglichen wurden Text und Bericht.
- Die 247 Schwärzungstests des pdf-editor liefen lokal über eine
  Übergangsschicht gegen die Bibliothek. Diese Schicht greift noch auf
  interne Helfer zu (`ner_text._hard_parts`, `ner_text._short_segments`,
  `page_text._page_text`, `raw_scan._RawScanner`); bei der Umstellung des
  pdf-editor werden die betroffenen Tests auf den öffentlichen Vertrag
  umgestellt.

## Abweichungen

| Stelle | Original | auditcore_pdf.redaction | Begründung |
|---|---|---|---|
| Einstieg | ein Modul `app.services.redaction` | Unterpaket mit ausdrücklichem `__all__`; interne Helfer in Untermodulen | Wartbarkeit; der öffentliche Vertrag (`build_plan`, `apply_plan`, `redact_all`, `Plan`, `Selection`, `Criteria`, Fehlerklassen, `PATTERNS`, Grenzwerte) ist gleich |
| `spacy_ner(nlp)` | nimmt jedes Objekt | erwartet ein Objekt mit `pipe` (Protokoll `SpacyPipeline`) | Typisierung; eine spaCy-Pipeline erfüllt das Protokoll, das Verhalten ist gleich |
| Fehlende PDF-Engine | `RedactionError("PyMuPDF nicht verfügbar")` beim Öffnen | `RuntimeError("PyMuPDF ist nicht verfügbar. Bitte auditcore_pdf[pymupdf] installieren.")` aus `engine.require_engine` | einheitliche Meldung aller auditcore_pdf-Funktionen; ein fehlendes Extra ist ein Installationsfehler, kein Eingabefehler. Der Import gelingt in beiden Fällen auch ohne Engine |
| `Selection.from_dict` (seit 0.3.0) | `sanitize`, `case_sensitive`, `whole_word` über `bool()`; `rect` jede Folge (auch ein Text wie `"0101"`) | Wahrheitswerte und eine Liste aus Zahlen verlangt, sonst `RedactionError` | `"false"` oder `0` wurden bisher stillschweigend umgedeutet; über REST hätte das eine andere Schwärzung ergeben als ausgewählt. Gültige Eingaben verhalten sich gleich |
| KI-Namenserkennung | spaCy im Anwendungscode | austauschbare `NerFn`; spaCy nur über Extra `[ner]`, Sprachmodell installiert die Anwendung | keine Pflichtabhängigkeit und kein Modell im Paket |

## Abgrenzung zu 0.1.0

Die Funktionen aus 0.1.0 (`redact_document`, `find_redaction_targets`,
`verify_redaction`, `sanitize_*`) bleiben unverändert erhalten. Für neue
Anwendungen ist `auditcore_pdf.redaction` der empfohlene Weg: Vorschau mit
bestätigter Auswahl, Prüfziffern, versteckte Ablagen und fail-closed
Nachprüfung im Rohinhalt.

Nicht übernommen: FastAPI-Routen, Upload-Grenzen und Rechteprüfung des
pdf-editor sowie das Laden des spaCy-Modells.

## Was die Anwendung selbst begrenzen und schützen muss

Diese Punkte gelten wie im Original; dort deckte die Anwendung sie ab.

- **Klartext.** Klartext steht nicht nur im Plan (`Plan.to_dict()`, `repr`
  von `Candidate`), sondern auch in `Selection.criteria.terms`, in den
  Schlüsseln von `ApplyReport.by_source` (`begriff:<Suchbegriff>`) und in
  `RedactionVerificationError` (Meldung und `problems` nennen die ersten drei
  Zeichen eines noch lesbaren Fundtexts). Nichts davon protokollieren oder
  ungefiltert an Nutzer anderer Vorgänge ausgeben.
- **Größe.** Der Schwärzungspfad prüft keine Seitenzahl
  (`engine.MAX_PAGES` gilt nur für `engine.open_pdf`). `apply_plan`
  durchsucht das Dokument dreimal (erneute Suche, Textgruppen, Nachprüfung);
  mit KI geht der Text aller Seiten in einem Aufruf an die `NerFn`. Dateigröße
  und Seitenzahl begrenzt der Aufrufer.
- **Umfang der Nachprüfung.** Fail-closed nachgeprüft werden die ausgewählten
  Fundstellen (Seitentext und Rohinhalt) sowie bei `sanitize` Metadaten, XMP
  und Anhänge. Das Entfernen von JavaScript und Anwendungsdaten wird nicht
  nachgeprüft; die Suche nach JavaScript liest höchstens 20 000 Objekte und
  überspringt unlesbare.
- **`verified` im Bericht.** `redact_all` gibt eine Datei ohne Fundstelle und
  ohne `sanitize` unverändert zurück; `ApplyReport.to_dict()` meldet auch dann
  `"verified": true`, obwohl keine Nachprüfung lief.
- **Nachsuche von KI-Namen.** Ein belegter Name wird im ganzen Dokument
  nachgesucht, aber nur bis zu einer Grenze: höchstens
  `max(10, 4 × Zahl der verschiedenen direkten Fundtexte)` Fundstellen. Namen
  aus einem Satz, aus der Listenform oder mit vollständiger Bestätigung im
  Mustersatz haben keine Grenze; für Belege über Zellgrenzen hinweg und für
  teilweise bestätigte Belege liegt die Untergrenze bei 50; Spaltenköpfe
  werden aus Zellbelegen nie ohne Anrede nachgesucht. Liegt ein Name über der
  Grenze, bleiben nur die Fundstellen mit Anrede oder Titel davor; an den
  übrigen Stellen wird er nicht nachgesucht. Die Nachprüfung meldet das
  nicht, weil sie nur die Auswahl prüft. Bei `redact_all` ohne Vorschau fällt
  das niemandem auf.
