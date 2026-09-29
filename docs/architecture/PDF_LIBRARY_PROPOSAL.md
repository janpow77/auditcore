# PDF-Bibliothek aus pdf-editor: Übernahmevorschlag

Stand: 29. September 2026. Status: technische Voruntersuchung, keine Extraktion
oder Migration durchgeführt. Quelle:
[`janpow77/pdf-editor@ce3441312975`](https://github.com/janpow77/pdf-editor/tree/ce34413129751dfd72fac6cefa55b02718bff27b).
Dieser Commit war zum Prüfzeitpunkt der Kopf des Standardbranches.

## Ergebnis

Die PDF-Funktionen sind für auditcore gut geeignet. Empfohlen wird eine eigene
Distribution `auditcore_pdf` für PDF-Operationen und eine gemeinsame UI-Gruppe
`pdf` in den vorhandenen Vue-/React-Paketen. Der Name ist ein Vorschlag, kein
bereits vorhandenes oder veröffentlichtes Paket.

Die Anwendung bleibt eigenständig. Ihre Dienste werden nach Extraktion durch
Bibliotheksaufrufe ersetzt. Auch audit_designer kann später dieselbe Bibliothek
verwenden; laut Quell-README stammen Teile der Dienste und Komponenten von dort.
Eine vollständige Gleichheitsprüfung der heutigen Kopien wurde nicht durchgeführt.

Die Schwärzung entfernt bereits echte Seiteninhalte. Vor einer Bibliotheksfreigabe
sind jedoch präzisere Verträge und zusätzliche Prüfungen nötig. Die sieben unten
dokumentierten Charakterisierungsszenarien sind keine vollständige Sicherheitsabnahme.

## 1. Vorhandene Bausteine und Wiederverwendung

| Bedarf | Beobachtete Quelle | Vorgesehene Zuordnung |
|---|---|---|
| PDF aus Bildern, Zusammenführen, Teilen, Drehen, Seiten zusammenstellen | `pdf_tools_service.py` | `auditcore_pdf` |
| Seitenzahlen, Kopf-/Fußzeilen, Lesezeichen, Annotationen und Textbearbeitung | `pdf_editor_service.py` | `auditcore_pdf`, in getrennten Operationsmodulen |
| Suche, Muster, Namenslisten, Schwärzen, Bates-Nummern, Formulare | `pdf_extras_service.py` | `auditcore_pdf`, Schwärzung mit eigenem Prüfvertrag |
| Bereinigung, Prüfakte, Qualitätsprüfung, Bildaustausch | `pdf_more_service.py` | `auditcore_pdf` nach Charakterisierung |
| Office → PDF | LibreOffice-Aufruf in `pdf_more_service.py` | Optionaler Prozessadapter mit isolierter Ausführung |
| OCR und PDF/A | Tesseract/OCRmyPDF/Ghostscript-Anbindung | Optionale Adapter; vorhandene Dokumentpipeline anbinden |
| Digitale Signaturen und Prüfung | pyHanko-Anbindung | Separater optionaler Adapter und eigener Abnahmenachweis |
| PDF anzeigen und bearbeiten | `PdfViewer.vue`, `PdfWorkbench.vue`, `PdfRedact.vue`, `PdfAnnotate.vue` | Gemeinsamer UI-Kern und native Vue-/React-Komponenten |
| Dokumentvergleich und Synopse | Bereits `auditcore_documents` | Wiederverwenden; keine zweite identische Vergleichslogik |
| Berichte aus strukturierten Daten/Vorlagen als PDF | Bereits `auditcore_reporting`, ReportLab | Bestehenden Renderer erweitern, nicht parallel neu schreiben |

PDF-Erstellung ist damit kein einzelner Vorgang: strukturierte Berichte,
Office-Konvertierung und Bearbeitung bestehender PDFs haben unterschiedliche
Eingaben und Abhängigkeiten. Gemeinsame Ausgaben können von `auditcore_pdf`
nachbearbeitet werden, beispielsweise für Nummerierung oder Zusammenführung.

Der vorliegende GUI-Entwurf für Konto und Mandant wurde aus einer statischen
HTML-Druckvorlage mit Chrome erzeugt. Das ist keine bereits erfolgte Integration
mit dem PDF-Editor und kein Nachweis für die Office-/Schwärzungsfunktionen.

## 2. Tatsächlich ausgeführte Charakterisierung

Der Quellcode wurde in einen separaten temporären Checkout gelesen und unverändert
ausgeführt. Eine isolierte Umgebung enthielt Python 3.14.4 und PyMuPDF 1.28.2.
Es wurden ausschließlich synthetische PDFs erzeugt und direkt an die bestehenden
Services übergeben. Für einen Textentfernungsfall wurde zusätzlich Poppler
`pdftotext` als unabhängiger Leser verwendet.

Maschinenbericht:
[`pdf-editor-characterization-20260929.json`](../reports/pdf-editor-characterization-20260929.json).
Nach dem Lauf wurde zunächst dieser Bericht ausgewertet und dann gezielt der
betroffene Quelltext nachgelesen.

| Fall | Beobachtung | Konsequenz |
|---|---|---|
| Sichtbarer Geheimtext plus Kopien in Titel, Anhang und Kommentar | Seiteninhalt entfernt, übriger Seitentext erhalten; alle drei versteckten Kopien bleiben vorhanden | Seiten-Schwärzung und vollständige Bereinigung dürfen nicht gleichgesetzt werden |
| Unabhängige Textextraktion desselben Ergebnisses | Auch Poppler liest den entfernten Seiteninhalt nicht mehr aus | Positive Bestätigung dieses konkreten Textfalls, kein Nachweis für sämtliche PDF-Objekte |
| Einfache Suche nach `Alpha` mit `match_case=True` | Auch `alpha` entfernt; zwei Schwärzungen gemeldet | Groß-/Kleinschreibung im einfachen Suchpfad korrigieren |
| Namensliste mit `Erika Musterfrau`, auf zwei Zeilen getrennt | Keine Fundstelle | Mehrzeilige Begriffe und OCR-Zeilenumbrüche ausdrücklich behandeln |
| Scan ohne Textebene | Muster findet nichts; einfache Suchschwärzung meldet Erfolg mit null Treffern | Fehlende Suchbarkeit sichtbar machen; OCR oder manuelle Bereichsauswahl anbieten |
| Neues Textkommentar auf PDF mit vorhandener offener Schwärzungsmarkierung | Bestehende Markierung wird gleichzeitig angewendet; markierter Text verschwindet | Annotation und Ausführen einer Schwärzung strikt trennen |
| E-Mail-Musterschwärzung | E-Mail entfernt, öffentlicher Kontext erhalten | Geeignete Grundlage für eine korrigierte gemeinsame Such-/Schwärzungspipeline |

Die versteckten Kopien sind eine Grenze der isolierten Schwärzungsoperation.
Die App besitzt zusätzlich `clean_pdf`; sie wird von den geprüften
Schwärzungsfunktionen nicht automatisch aufgerufen. Daraus wird nicht abgeleitet,
dass jede Kombination der heutigen Werkzeuge denselben Restinhalt erzeugt.

### Zugehörige Quellstellen

- `backend/app/services/pdf_extras_service.py:490`: Mustererkennung gruppiert
  Text nach einzelnen Zeilen; `:612` führt die daraus bestimmten Schwärzungen aus.
- `backend/app/services/pdf_extras_service.py:1020`: `match_case` verändert
  Textextraktionsflags, aber nicht die Groß-/Kleinschreibung von `search_for`.
  Die [PyMuPDF-Dokumentation zur Suche](https://pymupdf.readthedocs.io/en/latest/page.html#Page.search_for)
  beschreibt deren eigenes Verhalten und die Einschränkung bei Nicht-ASCII-Zeichen.
- `backend/app/services/pdf_editor_service.py:514`: nach beliebigen Annotationen
  wird `apply_redactions()` auf allen Seiten ausgeführt.
- `backend/app/services/pdf_more_service.py:290`: separate Bereinigung mit
  `scrub`, unter anderem für Metadaten, JavaScript und Anhänge; Formularwerte
  bleiben durch `reset_fields=False` ausdrücklich erhalten.
- `backend/app/api/pdf_extras.py:323`: die Vorschau liefert höchstens 500
  Fundstellen, während die Ausführung alle Suchtreffer verarbeitet.

Die breite Anforderung `PyMuPDF>=1.23.8` sichert kein einheitliches Verhalten
für Text, Bilder und Vektorgrafiken. Die Grafikoption wurde erst mit 1.23.27
ergänzt. Für die Bibliothek sind explizite Einstellungen und ein geprüfter
Versionsbereich nötig. Quelle:
[PyMuPDF apply_redactions](https://pymupdf.readthedocs.io/en/latest/page.html#Page.apply_redactions).

## 3. Zielablauf für das Schwärzen

1. **Prüfen:** Seiten, Textebene, Bilder, Rotation, Verschlüsselung, Signaturen,
   Anhänge und bestehende Schwärzungsmarkierungen erfassen. Grenzen der Verarbeitung anzeigen.
2. **Vorschlagen:** manuell Rechtecke markieren oder Begriffe/Muster suchen.
   Optionale Namenserkennung liefert Vorschläge; fehlende Treffer bedeuten keine Freigabe.
3. **Sichten:** Treffer mit Seite und Position anzeigen, einzeln annehmen oder
   ablehnen, weitere Bereiche ergänzen. Alle Treffer sind erreichbar, etwa durch Pagination.
4. **Bestätigen:** einen Plan aus bestätigten Bereichen und Bereinigungsoptionen
   an den Hash der Eingabedatei binden. Eine geänderte Datei macht den Plan ungültig.
5. **Ausführen:** nur bestätigte Bereiche irreversibel entfernen und eine neue
   Ausgabedatei schreiben. Original und Ausgabe dürfen nicht verwechselt werden.
6. **Nachprüfen:** Datei erneut öffnen, Text und Objekte prüfen und eine
   Ergebnisvorschau bereitstellen. Verbleibende Risiken ausdrücklich melden.
7. **Exportieren:** neue PDF und einen Prüfbericht ohne entfernte Klartextinhalte ausgeben.

Zwei deutlich bezeichnete Zwecke:

- **Markierte Bereiche entfernen:** gezielte Seitenoperation. Andere Inhalte
  bleiben erhalten; die Ausgabe behauptet keine vollständige Anonymisierung.
- **Zur Weitergabe bereinigen:** zusätzlich ein gemeinsames, versioniertes
  Bereinigungsprofil für Metadaten, Kommentare, Anhänge, Formularwerte, aktive
  Inhalte und weitere unterstützte Strukturen. Nicht prüfbare Inhalte sperren
  eine positive Freigabe oder verlangen einen ausdrücklich ausgewiesenen Alternativweg.

OCR-Suchergebnisse werden auf die Bildbereiche zurückgeführt. Nur die unsichtbare
Textebene zu löschen reicht bei Scans nicht. Auch Originalbilder, Masken, mehrfach
referenzierte Bilder, Vektortext, Formularobjekte, CropBox/Rotation und frühere
inkrementelle Revisionen benötigen eigene Prüfbeispiele. Die statische Textsuche
kann keine Aussage „vollständig anonymisiert“ begründen.

Ein Signaturbild ist von einer kryptografischen Signatur zu unterscheiden.
PDF-Bearbeitung kann bestehende Signaturen ungültig machen. Die Oberfläche zeigt
diesen Effekt vor dem Export; Schwärzung darf keinen unveränderten Signaturstatus behaupten.

## 4. Vue und React

Der bestehende Viewer verwendet `pdfjs-dist` und rendert im Browser. Die Vue-App
enthält schon Seitenvorschau, Werkzeuge und eine explizite Schwärzungsbestätigung.
Das ist eine gute UI-Vorlage. Es wurde keine bereits vorhandene React-Fassung gefunden.

Vorgeschlagene gemeinsame Ansicht:

```text
Dokumentname                          Original / Entwurf / Ergebnis
Seitenminiaturen | PDF-Seite mit Zoom | Werkzeug und Fundstellen
                 | Markierte Bereiche| Auswahl, Seite, Begründung
---------------------------------------------------------------
Änderungen verwerfen      Vorschau prüfen      Schwärzung anwenden
```

`@auditcore/ui-core` hält Auswahl, Koordinaten, Suchplan, Status und Texte.
Viewer-Anbindung und gemeinsam nutzbare Browserlogik bleiben frameworkunabhängig.
Vue und React erhalten native Renderer mit gleichem Verhalten, gemeinsamen
Design-Tokens und den vorhandenen Paritätstests. Fachlogik aus den Vue-Komponenten
wird nicht in React kopiert.

Die App bietet bereits lokale Sitzungssicherung in IndexedDB und exportierbare
Arbeitsstände. Im Zielvertrag ist diese Speicherung eine bewusste Option mit
klarer Kennzeichnung: Ein Arbeitsstand kann das ungeschwärzte Original enthalten.
Er darf nicht als bereinigte Ergebnisdatei weitergegeben werden. Der sichere
Standard speichert Dokumente nicht ungefragt dauerhaft im Browser.

## 5. Paketgrenzen, Betrieb und Lizenzen

Die fünf gelesenen PDF-Service-Dateien umfassen zusammen 5.795 Zeilen. Eine
unveränderte Übernahme würde die auditcore-Vorgaben für Module und Verträge
verfehlen. Der Bestand wird entlang der Operationen zerlegt und typisiert.
`PdfToolResult` ist ein Ausgangspunkt, braucht aber präzise Metadatenmodelle,
stabile Fehlercodes und eine klare Unterscheidung zwischen Erfolg, keinen Treffern
und unvollständig durchführbarer Prüfung.

Der Kern erhält keine FastAPI-, SQLAlchemy-, Auth-, E-Mail- oder App-Konfigurations-
Abhängigkeiten. Dateiablage, Zugriffsrechte, Quoten und Jobverwaltung bleiben in
der Anwendung. Office/OCR/PDF/A laufen über eigene optionale Adapter mit festen
Zeit- und Ressourcenlimits sowie kontrollierten temporären Verzeichnissen.
Eine fehlgeschlagene Sicherheitskonfiguration darf dabei keinen stillen Rückfall
auf weniger geschützte Prozessausführung auslösen.

Das heutige Repository enthält bereits ein zentrales Abhängigkeitsregister in
`backend/app/pdf_backend.py`. Dieses Wissen wird wiederverwendet. Die README-Aussage
„vollständig im Arbeitsspeicher“ muss nach Verarbeitungspfad differenziert werden:
Office-Konvertierung schreibt temporäre Dateien; Browser-Arbeitsstände können
optional persistiert werden. Automatisches Aufräumen ist kein Nachweis physischer
Löschung auf sämtlichen beteiligten Speichern.

**Lizenzpunkt vor Veröffentlichung:** PyMuPDF wird unter AGPL oder kommerzieller
Lizenz angeboten; Ghostscript ist ebenfalls gesondert zu berücksichtigen. Die
Herstellerquelle für PyMuPDF ist
[PyMuPDF Licensing](https://pymupdf.io/licensing). Eine optionale Abhängigkeit oder
ein Adapter hebt diese Bedingungen nicht auf. Im geprüften Repository wurde keine
Lizenzdatei für den eigenen Anwendungscode gefunden; eine neue MIT-Freigabe des
extrahierten Codes wird hier nicht unterstellt.

Empfehlung: zuerst einen engineunabhängigen Operationsvertrag festlegen und dann
den passenden Lizenz-/Auslieferungsweg dokumentieren. PyMuPDF ist technisch ein
naheliegender erster Provider, aber keine automatisch MIT-kompatible Gesamtlieferung.
Ein Enginewechsel ist eine eigene Implementierung mit derselben Charakterisierung,
kein bloßer Austausch eines Importnamens. Konkrete Lizenzrechte des Betreibers
wurden in dieser Untersuchung nicht geprüft.

## 6. Reihenfolge und Grenzen dieser Untersuchung

1. Herkunft, Lizenzweg, Operationsverträge und repräsentative Charakterisierung fixieren.
2. Viewer, Seitenoperationen und Bild-zu-PDF als erste durchgehende Referenz extrahieren.
3. Schwärzungsplan, korrigierte Suche, unabhängige Nachprüfung und Bereinigungsprofil ergänzen.
4. Formulare, Office, OCR/PDF/A und Signaturen jeweils mit eigenen Abnahmen anbinden.
5. Vue-/React-Parität und Bibliotheks-Gates abschließen; danach die Quellanwendungen migrieren.

Gelesen wurden die Inventurzusammenfassung und Paketübersicht in auditcore sowie
README, Modulkatalog, ausgewählte Services, API-Routen, Vue-Komponenten und Tests
des PDF-Editors. Im Quellcheckout wurden weder `AGENTS.md` noch ein
`.auditcore-runner.toml` oder ein passender gespeicherter Maschinenbericht gefunden.
Die vorhandenen Quelltests wurden gelesen, aber nicht als vollständige Suite ausgeführt.

Der eigene Maschinenbericht enthält sieben ausgeführte Charakterisierungsszenarien,
darunter einen unabhängigen Poppler-Lesetest. Keine OCR-, Office-, Signatur-,
Bild-/Vektorschwärzungs-, vollständige Frontend- oder produktive Sicherheitsabnahme.
Die Produktionsversion der PDF-Engine wurde nicht ermittelt. In auditcore wurden
nur diese Auswertung und der Datenbericht ergänzt; kein Anwendungscode geändert
und kein `auditcore-runner`-Lauf ausgeführt.
