# Vorschlag zur Bibliothekskonsolidierung

Stand: 22. September 2026. Status: **VORSCHLAG**, keine fachliche Freigabe
und kein Nachweis bereits erfolgter Anwendungsmigrationen.

**Ausführung erst nach fertiggestelltem Framework.** Die nachfolgenden
Paketkandidaten beschreiben Phase C des verbindlichen
[Umsetzungsplans](IMPLEMENTATION_PLAN.md). Vorrang haben dort Phase A und B:
Plattform fertigstellen und technisch nachweisen.

## Entscheidungsvorschlag

**Die Anwendungen bleiben vollständig eigenständige Projekte.** Jedes
Anwendungsrepository behält seine Oberfläche, Datenbank, Berechtigungen,
Deployment-Konfiguration und seinen eigenen Releasezyklus. Es werden keine
Anwendungsrepositories zusammengelegt. Eine Anwendung bindet nur die benötigten
APIs der benötigten, jeweils eigenständig installierbaren Fachbibliotheken ein.

Verbindlich ist [ADR-001](ADR-001-multi-package-monorepo.md): ein gemeinsames
Repository mit der Plattformbibliothek `auditcore` und separaten Fachpaketen
wie `auditcore_dummygenerator`. Die spätere Nutzerpräzisierung ersetzt die
ursprüngliche Ein-Python-Projekt-Vorgabe. So installieren Anwendungen nur ihre
benötigte Fachlogik samt zugehörigen Abhängigkeiten. Pakete entstehen erst mit
konkreten, charakterisierten Implementierungen.

Die vorhandenen Modelle, Regeln, Exceptions und Provenienz bleiben gemeinsame
Grundlagen der Plattform. Die vier technischen Werkzeuge behalten ihre
Zuständigkeiten unter `auditcore.tools`. Fachbibliotheken bekommen keine
pauschale Laufzeitabhängigkeit von der Plattform oder den übrigen Fachpaketen.

## Die Bibliothek wird tatsächlich eingebunden und ausgeführt

Eine Extraktion ist erst vollständig, wenn ein echter Consumer die gebaute
Bibliothek installiert, importiert und im bisherigen Anwendungspfad verwendet.
Eine Kopie im auditcore-Repository oder ein noch nicht angewandter Patch reicht
dafür nicht aus.

Beispiel für den angestrebten Consumer-Code:

```python
from auditcore_reporting import get_number_format

cell.number_format = get_number_format(column_name, cell.value)
```

Der AppRefactorer ergänzt die geprüfte Fachpaket-Version als Abhängigkeit im
Anwendungsprojekt, stellt Aufrufe um und erhält notwendige Compatibility Wrapper.
Die konkrete Anwendung wird in einer isolierten Umgebung mit dem gebauten
Fachbibliotheks-Wheel installiert. Integrationstests durchlaufen die bisherigen
Anwendungsfunktionen und prüfen sowohl die Benutzung der Bibliotheksfunktion
als auch die unveränderten fachlichen Ergebnisse. Ein erfolgreicher Import
allein belegt diesen vollständigen Aufrufpfad nicht.

Das Wheel wird über den vorhandenen kontrollierten Artefaktweg bereitgestellt;
ein öffentlicher PyPI-Release wird nicht vorausgesetzt. Jede Anwendung legt
ihren geprüften Versionsstand fest und aktualisiert ihn in einem eigenen
Migration-/Releasevorgang. Für Debian-Deployments wird die Bibliothek bereits
beim Build zusammen mit den übrigen Python-Abhängigkeiten eingebunden; der
Zielserver muss sie nicht aus PyPI nachladen. Alternativ deklariert eine
System-Python-Anwendung passende Debian-Abhängigkeiten, die APT installiert.
Jede Fachbibliothek hat eine eigene Distribution. Ein reines Quellrepository
ersetzt keinen Paketindex; Veröffentlichung und Paketquellen müssen eingerichtet
und gesondert nachgewiesen werden.

## Vorgeschlagene fachliche Bibliotheken

| Bibliothek | Zusammenzuführende Aufgaben | Abgrenzung |
|---|---|---|
| `auditcore_dummygenerator` | Synthetische Felder, Zeilen, zusammenhängende Testdatenszenarien und explizite Fehlerfälle | Kein Webserver, UI, Produktivdatenzugriff oder impliziter KI-/DB-Client; Szenariopakete nur bei tatsächlichem Bedarf |
| `auditcore_reporting` | Zahlen-/Tabellenformate, gemeinsame Berichtsmodelle, wiederkehrende Ergebnisdarstellung aus Flowlib und Fachanwendungen | Keine HTTP-Endpunkte oder Datenbankabfragen; Renderer-Anbindungen zunächst in den Anwendungen |
| `auditcore_documents` | Dokumentmodelle, reine Parser, Text-/Feldnormalisierung, dokumentbezogene Validierung | Upload-Berechtigungen, Virenprüfung, Speicherorte und Aufbewahrung bleiben Anwendung/Betrieb zugeordnet |
| `auditcore_statistics` | Wiederverwendbare numerische Verfahren, etwa Benford- und Ausreißerberechnungen aus Flowstat | Liefert Kennzahlen; legt keine fachliche Risikoeinstufung oder Prüfentscheidung fest |
| `auditcore_sampling` | Stichprobenziehung, Schichtung, MUS/SRS und zugehörige methodische Berechnungen | Verfahren, Annahmen, Zufallsstartwerte und Rundung explizit; kann statistics verwenden |
| `auditcore_risk` | Bewertung anhand expliziter versionierter Risikomodelle und nachvollziehbare Bewertungsbeiträge | Gewichte, Schwellen und Rechtsauslegung bleiben getrennte Regelwerke |
| `auditcore_procurement` | Vergabedatenmodelle, fachliche Vorprüfungen und parametrische Prüfregeln | Verfahrensarten, Rechtsstände und Korrektursätze nicht still vereinheitlichen |
| `auditcore_privacy` | Gemeinsame deterministische Pseudonymisierungs-/Maskierungsmechanik | Schlüssel, Mapping-Speicherung und Berechtigungen bleiben beim Consumer; Pseudonymisierung nicht als Anonymisierung ausgeben |

Dies sind fachliche Paketkandidaten, keine bereits veröffentlichten Pakete.
`auditcore.reporting` existiert derzeit als Modul der Plattform mit einer
übernommenen Funktion; dessen Ausgliederung zu `auditcore_reporting` muss die
bestehende API kontrolliert migrieren. Ein separates `auditcore_statistics`
lohnt sich nur bei unabhängigen Statistik-Consumern; andernfalls bleiben reine
Hilfsberechnungen zunächst intern in `auditcore_sampling`.

## Konkrete Kombinationen aus dem Inventar

0. **Testdatengenerator und passende Szenariofunktionen:** der Feld-/Zeilenkern
   aus `flowaudit_testdatengenerator_frontend/backend/generator.py` eignet sich
   als erster Kandidat für `auditcore_dummygenerator`. Fachliche Szenarien und
   Ground-Truth aus Flowinvoice können diesen später ergänzen. Der tatsächliche
   Generatorcode ist FastAPI-/DB-frei und benötigt neben der Standardbibliothek
   optional joblib. Vor Übernahme sind Lizenz, Characterization, Uhrzeit-/Seed-
   Vertrag und Fehlerbehandlung der Worker zu klären. Zufällige IBAN-Prüfziffern
   dürfen nicht als zugesicherte IBAN-Validität ausgegeben werden.
1. **Flowlib-Reporting und Excel-Helfer aus Fachanwendungen:** gemeinsame
   Formatierung in `reporting`. `flowlib.get_number_format` ist bereits
   charakterisiert übernommen. Die gleichnamige Funktion in `auswertungjkb`
   hat abweichendes Verhalten: getrennte benannte Formatprofile beibehalten,
   bis eine fachliche Entscheidung die Gleichsetzung trägt. Die übrigen
   Flowlib-Bestandteile wie JWT-, HTTP-, Memory- und Ollama-Clients gehören
   nicht in diesen Fachkern.
2. **Berechnungsfunktionen aus Flowstat und eingebetteten Flowstat-Kopien in audit_designer/audit-portal:**
   ein gemeinsamer statistischer Kern und ein gemeinsamer Stichprobenkern.
   Gleiche Methoden werden einmal implementiert; Anwendungs- und API-Schichten
   verwenden sie über Adapter. Eingebettete Kopien sind nicht automatisch
   voneinander unabhängige Consumer und müssen versionsbezogen geprüft werden.
   Die Anwendungen bleiben eigenständig; ersetzt werden nur die jeweils
   geprüften lokalen Implementierungen durch Bibliotheksaufrufe.
3. **Vergabeprüfungen in flowinvoice und audit-portal:** gemeinsame reine
   Vorprüfungen und Datenverträge in `procurement`. Die gesamten Services
   werden nicht ungeprüft übernommen: Zugriff auf Datenbank, KI-Provider und
   fachliche Freigaben muss vorher vom Berechnungsteil getrennt sein.
4. **StablePseudonyms in flowinvoice und riskanalysis:** das Inventar meldet
   AST-identische Methoden. Das ist ein konkreter Kandidat für `privacy`,
   benötigt aber zusätzlich Tests für Kollisionsbehandlung, Mandantengrenzen,
   Wiederholbarkeit, Mapping-Lebensdauer und Nichtoffenlegung von Originalwerten.

Gemeinsame Parser und Validatoren kommen zuerst in ihre Domain. Ein zentrales
`utils`- oder `validation`-Sammelmodul wird aus den Rohklassifikationen nicht
abgeleitet. Kleine domainunabhängige Primitiven werden erst gemeinsam gemacht,
wenn mindestens zwei reale Consumer denselben Vertrag benötigen.

## Was fachlich getrennt bleibt

- Dokumentaufbereitung und Berichtserstellung teilen Datenverträge, behalten
  aber getrennte Zuständigkeiten: Eingaben interpretieren und Ergebnisse darstellen.
- Statistik, Stichprobendesign und Risikoentscheidung bleiben getrennte
  Module. Ein Ausreißer ist noch kein festgestellter fachlicher Risikofall.
- Die Mechanik für Versionierung, Provenienz und strukturierte Regel-Diffs
  kann gemeinsam in `rules`/`provenance` liegen. Das vereinheitlicht keine
  Schwellenwerte, Gewichtungen oder rechtlichen Auslegungen.
- Authentifizierung, Autorisierung, Mandantentrennung, Datenbankmigrationen,
  KI-Anbindungen und Betriebsdienste bleiben außerhalb des Fachkerns.
- Quality, Consolidator, AppRefactor und Deployer bleiben vier getrennte
  Werkzeuge innerhalb derselben Distribution.

## Reihenfolge der Umsetzung

1. **Kandidaten bereinigen:** Tests, generierten Code, Alembic-Migrationen,
   API-Routen und eingebettete Repository-Kopien kennzeichnen. Lizenz und
   tatsächliche Consumer pro Kandidat feststellen.
2. **Reporting als ersten vollständigen Durchlauf abschließen:** vorhandene
   34 Characterization-Fälle beibehalten; echte Consumer-Integration ergänzen,
   Paketinstallation und bestehende Consumer-Checks reparieren, dann den
   vorbereiteten Compatibility Wrapper nach Policy-Prüfung anwenden.
3. **Flowstat-Verfahren einzeln extrahieren:** zunächst eine klar abgegrenzte
   deterministische Statistikfunktion, danach ein Stichprobenverfahren mit
   explizitem Seed und dokumentierten Annahmen. Für jedes Verfahren getrennte
   Golden Tests und Nachweise aus mindestens einem echten Consumer.
4. **Dokument- und Reporting-Verträge konsolidieren:** fachliche Modelle und
   wiederverwendbare Parser vor plattformspezifischen Renderern.
5. **Privacy, Risk und Procurement nach gezielter Prüfung:** technische
   Gleichheit nachweisen; Sicherheits- und Regelvarianten ausdrücklich
   erhalten. Keine automatische fachliche Harmonisierung.

Jede Extraktion durchläuft: festgehaltene GitHub-Revision → beobachtete
Legacy-Eingaben/-Ausgaben → gemeinsame Implementierung → Compatibility Wrapper
→ Consumer-Regression/Integration → erneute Policy- und Quality-Prüfung.
Danach Inventar, KIRA, Provenienz und API-Snapshot aktualisieren. Legacy-Code
erst entfernen, wenn die bekannten Consumer umgestellt sind.

Die zusätzlichen Consumer-Prüfungen sind echte technische Arbeit, nicht nur
eine fehlende Freigabe: Im unveränderten Flowlib-Stand scheitert die Installation
an der in `python/pyproject.toml` referenzierten, fehlenden `README.md`; Ruff
meldet 15 Befunde. Diese Baseline wurde am 22. September separat ausgeführt.
Sie ist kein durch die auditcore-Migration verursachter Fehler. Die dortige
Testsammlung enthält derzeit nur `tests/__init__.py`.

## Evidenz und Grenzen

Grundlage: persistentes Inventar vom 22. September 2026,
Run `553272de-ce48-4343-9041-ee75ae5d214a` und
[Inventurübersicht](../reports/inventory-summary.json).
71 Repositories, 84.752 Symbole und 2.438 automatische Kandidatengruppen.
Die Gruppen sind keine 2.438 freigegebenen Bibliotheksbausteine.

Konkrete Fehlklassifikation: `run_migrations_online` in Alembic-Dateien wurde
unter `documents` eingeordnet; auch Router-Healthchecks und Tests kommen in
Domain-Kandidatengruppen vor. Pfad-/Namensheuristik und AST-Ähnlichkeit reichen
für eine Extraktionsentscheidung nicht aus. Die Inventur deckt Python-AST und
Dependency-Manifeste ab; eine vollständige semantische VBA-/TypeScript-Analyse
ist damit nicht nachgewiesen.

| Quelle | Revision | Konkreter Ausgangspunkt |
|---|---|---|
| flowlib | `aca2dc6aad25aea0720312dbcc6da00b0bcba330` | `python/flowlib/excel/formats.py:get_number_format` |
| auswertungjkb | `3e250425bac59a64da9f6d1c9dde966665d7a65e` | `audit_excel_utils.py:get_number_format` |
| flowstat | `d665ac221f50ba1f465b7337bdd4aa218d78ec8a` | `backend/app/services/analysis_core_service.py:run_benford`, `sampling_service.py:_calculate_mus_sample_size` |
| flowinvoice | `fb2d18568d2eaf64574d131ceae51a936b9aac02` | `backend/app/services/procurement_analyzer.py:ProcurementPreChecker.run_prechecks`, `backend/app/verwk/services/pseudonymization.py:StablePseudonyms.code` |
| riskanalysis | `b5c523bf7eaa326153778d9751f176f03d4d56ed` | `backend/app/services/pseudonymization.py:StablePseudonyms.code` |

Flowlib ist im Inventar als MIT belegt. Bei den weiteren hier genannten
Quellen ist die Lizenz im Inventar UNKNOWN bzw. NOASSERTION; die konkrete
Nutzungsberechtigung ist vor Übernahme festzustellen. Das ist kein Nachweis
fehlender Rechte. Die Tabelle fixiert den analysierten Quellstand und behauptet
keine erneute Prüfung aller heutigen Remote-HEADs.
