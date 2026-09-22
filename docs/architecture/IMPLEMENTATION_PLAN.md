# Umsetzungsplan: auditcore als Plattform und Bibliotheksrepository

Stand: 22. September 2026. Architektur gemäß ausdrücklicher Nutzerentscheidung
in [ADR-001](ADR-001-multi-package-monorepo.md).
Dies ist der abgeschlossene Arbeitsplan, kein Abschlussbericht der Umsetzung.

**Verbindliche Reihenfolge: FRAMEWORK → FRAMEWORK-ABNAHMENACHWEIS →
FACHBIBLIOTHEKEN → ANWENDUNGSMIGRATIONEN.** Die Plattformarbeit hat Vorrang.
Fachbibliotheken werden erst nach dem technischen Plattformnachweis begonnen;
bereits vorbereitete Entwürfe sind zurückgestellt. Die für die Plattform nötigen
Tests verwenden isolierte technische Testpakete.

## 1. Verbindliches Zielbild

- Das Repository `auditcore` beherbergt, baut, prüft und verwaltet mehrere Pakete.
- `auditcore` ist selbst die Plattformbibliothek mit Quality, Consolidator,
  AppRefactor und Deployer.
- Fachbibliotheken sind separat installierbar, beispielsweise
  `auditcore_dummygenerator` und `auditcore_invoicegenerator`.
- Anwendungen bleiben in ihren eigenen Repositories und beziehen nur benötigte
  Pakete über Requirements/pip oder Debian-Abhängigkeiten/APT.
- Fachpakete ziehen weder automatisch alle anderen Fachpakete noch die
  Plattform als Laufzeitabhängigkeit nach.

## 2. Fachlicher Paketplan

| Paket | Inhalt | Reihenfolge |
|---|---|---|
| `auditcore` | Herstellung, Inventur, Quality/Policy, Migration und Paketierung | Vorhandene Plattform an Mehrpaket-Verwaltung anpassen |
| `auditcore_dummygenerator` | Synthetische Feld-/Zeilendaten, Verteilungen, reproduzierbare Szenarien und ausdrückliche Fehlervarianten | Erstes vollständiges Fachpaket |
| `auditcore_invoicegenerator` | Synthetische Testrechnungen mit Positionen, Beträgen, Beziehungen und bekannten Fehlerfällen; passende Ausgabeadapter | Zweites Fachpaket, Grunddaten über dummygenerator wiederverwenden |
| `auditcore_reporting` | Fachliche Berichts-/Tabellenmodelle und gemeinsame Formatierung | Bestehende Übernahme aus auditcore.reporting kontrolliert ausgliedern |
| `auditcore_documents` | Gemeinsame Dokumentmodelle, Parser, Normalisierung und dokumentbezogene Validatoren | Nach erster realer Consumer-Migration |
| `auditcore_sampling` | Stichprobenverfahren, Schichtung und methodische Berechnungen | Verfahren einzeln charakterisieren und übernehmen |
| `auditcore_statistics` | Benford, Ausreißer und weitere von Stichproben unabhängige Statistik | Nur bei belegten eigenständigen Consumern separat; reine Sampling-Helfer bleiben intern |
| `auditcore_risk` | Bewertungsmechanik mit expliziten versionierten Modellen | Nach Prüfung der fachlichen Varianten |
| `auditcore_procurement` | Vergabeprüfungen, Vorprüfungen und fachliche Datenmodelle | Rechtsstände und Regeln getrennt erhalten |
| `auditcore_privacy` | Pseudonymisierung und Maskierung | Nach gezielten Sicherheits-/Consumer-Tests |

Nach Fertigstellung des Frameworks bilden die drei ersten Fachpakete die erste
Fachbibliothekswelle. Weitere Pakete
werden mit belegtem Code und Bedarf angelegt, nicht als leere Gerüste.
Ein Rechnungsgenerator bedeutet hier synthetische Testrechnungen; ein System
für verbindliche betriebliche Rechnungsstellung ist nicht damit zugesagt.

### Sinnvolle Kombinationen

- Namens-, Adress-, Nummern-, Datums- und Betragsgeneratoren gehören gemeinsam
  in `auditcore_dummygenerator`, nicht in einzelne Kleinstpakete.
- `auditcore_invoicegenerator` verwendet diese Grunddaten und ergänzt die
  Rechnungszusammenhänge. Dafür werden keine Generatorfunktionen kopiert.
- Vorhandene Excel-/Tabellenformatierung verschiedener Anwendungen wird in
  `auditcore_reporting` zusammengeführt; abweichende Formate bleiben Profile.
- Dokumentparser und passende Validatoren bleiben im Dokumentpaket.
- Statistik-Hilfen werden nur bei tatsächlicher unabhängiger Wiederverwendung
  aus Sampling ausgegliedert. Fachliche Gewichte, Schwellenwerte und
  Rechtsauslegungen werden durch gemeinsame Mechanik nicht gleichgesetzt.

## 3. Repository und Paketierung

```text
auditcore/
  pyproject.toml                         Plattformbibliothek
  src/auditcore/tools/
  packages/
    auditcore_dummygenerator/
      pyproject.toml
      src/auditcore_dummygenerator/
      tests/
      README.md
      NOTICE oder belegte Lizenzdatei
    auditcore_invoicegenerator/
      pyproject.toml
      src/auditcore_invoicegenerator/
      tests/
    auditcore_reporting/
      ...
  docs/
```

Jedes Paket hat eigene Metadaten, öffentliche API, Requirements, Tests und
Buildartefakte. Builds bleiben pro Distribution getrennt. Eine gemeinsame
CI-/Releasekoordination verwaltet die Pakete; eine unabhängige Releaseorganisation
pro Paket wird nicht ohne Bedarf eingeführt. Anwendungen binden ihren geprüften
Paketstand ausdrücklich und aktualisieren ihn kontrolliert.

Zielbeispiel für eine Anwendung nach tatsächlicher Veröffentlichung:

```text
# requirements.txt
auditcore_dummygenerator==0.1.0
auditcore_invoicegenerator==0.1.0
```

Die Debian-Entsprechungen heißen `python3-auditcore-dummygenerator` und
`python3-auditcore-invoicegenerator`. Ein Debian-Anwendungspaket deklariert sie
in `Depends`. Wheel und .deb enthalten dieselbe geprüfte Fachimplementierung.

## 4. Phase A: Framework vollständig fertigstellen

1. **Mehrpaket-Verwaltung:** pro Bibliothek Pfad, Name, Version, Import-API,
   Abhängigkeiten, Consumer, Herkunft, Anwendbarkeit und Status verwalten.
   Bestehende Plattform weiterverwenden; keine Fachbibliotheken erzeugen.
2. **Quality und Framework-Policy:** jedes Paket eigenständig prüfen;
   MUSS/BEDINGT/SOLL und UNKNOWN korrekt auswerten, Quell- und Nachweisbindung
   sichern, tatsächlich anwendbare Tests bestimmen. Offene Policy-Mapping-
   Fehler beheben, keine ungeprüften Befunde zu PASS erklären.
3. **Consolidator:** fachliche Kandidaten erkennen, technische Duplikate
   aussortieren, eigenständige Distributionen planen, persistent und
   revisionsgebunden inventarisieren. KIRA und Graphify mit ehrlichem Status.
4. **AppRefactor:** echte Requirements-/Importumstellung, Funktion-/Klassen-
   Characterization, Compatibility Wrapper, Policy-Neubewertung und Rollback
   unterstützen. Vorher mit isolierten Consumer-Testprojekten prüfen.
5. **Deployer/Paketierung:** Wheel/sdist und .deb aus derselben geprüften
   Paketversion bauen; Requirements beziehungsweise Debian-Depends korrekt
   abbilden; Paketmanifest/SBOM und reproduzierbare Installationsnachweise
   erzeugen. CLI-Aufrufe müssen aus der installierten Plattform funktionieren.
6. **Paketbereitstellung vorbereiten:** Python-Paketquelle und signierte
   APT-Indizes erzeugen/prüfen können. Keine Veröffentlichung vorwegnehmen.
   Lokale Installationen müssen ohne manuelle Quellcodekopie funktionieren.
7. **CI und Dokumentation:** Plattform- und Paketprüfungen automatisieren,
   Entwicklungs-/Build-/Installationsweg dokumentieren und Abschlussbericht
   mit tatsächlich ausgeführten Ergebnissen schreiben.

## 5. Phase B: Technischen Framework-Nachweis abschließen

Die Plattform wird als Wheel installiert. Ihre vier CLI-Komponenten werden
ausgeführt. Isolierte Testpakete durchlaufen Analyse, Plan, Characterization,
Migration, Fehler/Rollback, Build, pip-Installation aus Requirements sowie
APT-Installation/Upgrade/Remove. Imports und tatsächliche Funktionsaufrufe
müssen auf die installierten Pakete zeigen. Eine normale isolierte venv wird
nicht fälschlich mit dem APT-Systempython gleichgesetzt.

Erforderlich: vollständige Plattformtests, Ruff, Typprüfung, Security-/Dependency-
Prüfung, fünf Self-Checks und GitHub-CI. Policy-Reviews und externe Blockaden
bleiben separat sichtbar. Technische Implementierungslücken werden behoben,
bevor Fachbibliotheken begonnen werden. Eine ausstehende konkrete menschliche
Fach-/Releaseentscheidung wird dokumentiert und nicht als Implementierungsfehler
oder als erfundene Freigabe behandelt.

## 6. Phase C: Fachbibliotheken und reale Consumer

Diese Phase beginnt erst nach Phase B.

1. **Inventur und Quellen festhalten.** Repository/Commit/Symbol, Consumer,
   Lizenz, Abhängigkeiten und fachliche Varianten erfassen. Tests, Alembic,
   API-Routen und Kopien fremder Teilprojekte aus ungeprüften Extraktionskandidaten
   entfernen. Ziel: nachvollziehbare Paketkandidaten statt Rohduplikatzahlen.
2. **Legacy-Verhalten beobachten.** Eingaben und tatsächliche Ausgaben vor
   Änderungen aufzeichnen. Fehler, Uhrzeit, Zufall, Parallelbetrieb und
   absichtliche Fehlerszenarien einschließen. Ziel: ausführbare Golden Tests.
3. **dummygenerator fertigstellen.** Vorhandenen Kern übernehmen, fachliche
   API abgrenzen, technische Workerfehler sichtbar machen, Parallelrekursion
   verhindern, Seed-/Datumsvertrag dokumentieren. API/UI bleiben Anwendung.
   Ziel: getestetes echtes Paket ohne FastAPI-/DB-/Plattformpflichtabhängigkeit.
4. **pip und APT tatsächlich prüfen.** Wheel/sdist/.deb bauen, in sauberen
   Umgebungen installieren, importieren und Funktionen ausführen; APT-Upgrade/
   Remove prüfen. Unbekannte Lizenz nur als expliziter lokaler Testbau behandeln,
   keine öffentliche Veröffentlichungsfreigabe erfinden.
5. **Ersten echten Consumer migrieren.** Separaten Checkout der bisherigen
   Testdatengenerator-Anwendung verwenden; Requirements und Imports umstellen.
   Nachweisen, dass Anwendungsaufrufe die installierte Bibliothek erreichen.
   Regression, Integration, anwendbare Policy-, Typ-, Security- und Dependency-
   Prüfungen ausführen. Fachliche Abweichungen blockieren die Migration.
6. **invoicegenerator übernehmen.** Vorhandene Rechnungs-/PDF-Generatoren
   prüfen und charakterisieren; Rechnungsmodelle, Positionen, Summen,
   Fehlerprofile und Renderergrenzen festlegen. Grunddaten aus dummygenerator
   beziehen. Anschließend denselben Paket-/Consumer-Prüfweg durchlaufen.
7. **Reporting und weitere Pakete ausbauen.** Nach derselben Abnahmefolge;
   KIRA, Inventar, Provenienz, API-Snapshots und Migrationsstatus aktualisieren.
8. **Paketquellen bereitstellen.** Geprüfte Wheels über eine Python-Paketquelle
   beziehungsweise kontrollierte Artefakte; .deb über ein indiziertes,
   signiertes APT-Repository. Öffentliche oder produktive Veröffentlichung erst
   bei belegter Nutzungsberechtigung und erfüllten anwendbaren Freigabekriterien.

Die öffentlich sichtbaren Paketnamen sind derzeit Zielnamen, keine Behauptung,
dass `pip install NAME` oder `apt install NAME` schon ohne eingerichtete Quelle
funktioniert. Vor Veröffentlichung werden lokale Installationswege geprüft.
Eine normale isolierte venv sieht eine APT-Systeminstallation nicht automatisch;
der Betriebsweg des tatsächlichen Consumers wird ausdrücklich getestet.

## 7. Agenten und Integration

| Verantwortung | Konkreter Auftrag |
|---|---|
| Quality-/Policy-Agent | Mehrpaket-Anwendbarkeit, Nachweisbindung und Framework-Tests; Fachbibliotheksarbeit bis Phase C zurückgestellt |
| Paketierungs-/Migrations-Agent | Sichere Wheel-/Debian-Paketierung, Installtests und Klassen-API-Characterization im AppRefactorer |
| Consolidator-Agent | Fachliche Kandidatenfilterung, eigenständige Distributionsziele, Consumer-/Lizenznachweise |
| Hauptagent | Architektur, gemeinsame CI, installierte Plattform-CLIs, technische Integrationstests, Code-Review, Gesamtprüfung und logische Commits |

Fachbibliotheks- und echte Consumer-Aufträge werden erst in Phase C verteilt.
Es werden keine Application-Repositories fusioniert.

## 8. Fertig bedeutet pro Bibliothek

Ein Paket ist erst abgeschlossen, wenn es vollständigen Quellcode und
Metadaten enthält, installierbar ist, tatsächlich importiert/ausgeführt wird,
fachliche Tests besteht und mindestens ein echter Consumer geprüft umgestellt
wurde. Ein bestandener Paket-Smoke-Test allein ist keine abgeschlossene
Anwendungsmigration. Nicht ausgeführte Prüfungen bleiben NOT_EXECUTED,
fehlende Entscheidungen REVIEW_REQUIRED. Veröffentlichungsstatus und technische
Installierbarkeit werden getrennt berichtet.
