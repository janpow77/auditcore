# ADR-001: Plattformbibliothek und eigenständige Fachbibliotheken

Status: **ANGENOMMEN durch ausdrückliche Nutzerpräzisierung am 22. September 2026.**

## Verbindliche Entscheidung

**Reihenfolge: zuerst die Plattform vollständig fertigstellen und prüfen,
danach die einzelnen Fachbibliotheken erstellen und Anwendungen migrieren.**
Die technische Paketverwaltung wird vorher mit isolierten Testpaketen geprüft.
Begonnene Fachpaket-Entwürfe gelten nicht als fertige Pakete und werden bis
zum Plattformnachweis zurückgestellt.

`auditcore` ist selbst eine installierbare Plattformbibliothek. Ihre Werkzeuge
Quality, Consolidator, AppRefactor und Deployer unterstützen Herstellung,
Prüfung, Pflege, Anwendungseinbindung und Auslieferung weiterer Bibliotheken.

Das Git-Repository `auditcore` beherbergt zusätzlich mehrere fachlich
abgegrenzte, **eigenständig installierbare Python-Pakete**, beispielsweise
`auditcore_dummygenerator` und `auditcore_reporting`. Jede Fachbibliothek erhält
eine eigene Distribution, einen eigenen Python-Importnamensraum und deklarierte
Abhängigkeiten. Eine Anwendung installiert nur benötigte Bibliotheken.
Die Plattform ist keine obligatorische Laufzeitabhängigkeit aller Fachpakete.

Alle Anwendungen bleiben in ihren eigenen Repositories. Ihre Oberfläche,
Datenbank, Berechtigungen, Konfiguration und Releaseentscheidung bleiben dort.
Wiederverwendbare Fachlogik wird nach Characterization extrahiert und in den
Anwendungen tatsächlich durch Bibliotheksaufrufe ersetzt. Ein unbenutztes Wheel
oder eine zusätzliche Codekopie gilt nicht als abgeschlossene Migration.

## Verhältnis zum ursprünglichen Lastenheft

Diese spätere ausdrückliche Nutzeranweisung ersetzt die frühere Vorgabe
`ONE PYTHON PROJECT` und die standardmäßige Unterbringung aller Fachlogik in
Domain-Modulen derselben Distribution. `ONE REPOSITORY` bleibt bestehen.
Die ursprüngliche Spezifikation bleibt als historische Quelle unverändert.

Technische Begründung: selektive Installation pro Anwendung, begrenzte
transitive Abhängigkeiten, unabhängige importierbare Fachverträge und passende
pip-/APT-Abhängigkeiten. Die Zahl der Pakete folgt tatsächlichen fachlichen
Grenzen; Parser und Validatoren werden nicht ohne Nutzen jeweils separat
paketiert. Bibliotheken können gemeinsam veröffentlicht werden. Eine zwingend
unabhängige Versionspolitik wurde nicht vereinbart; das bestehende gemeinsame
Releaseverfahren wird nur soweit technisch nötig erweitert.

## Zielstruktur und Paketverträge

```text
auditcore/                           Git-Repository
  pyproject.toml                     vorhandenes Plattformprojekt auditcore
  src/auditcore/                     Plattform und vier Werkzeuge
  packages/
    auditcore_dummygenerator/
      pyproject.toml
      src/auditcore_dummygenerator/
      tests/
    auditcore_reporting/
      pyproject.toml
      src/auditcore_reporting/
      tests/
  docs/
```

Die vorhandene Plattform muss nicht allein für die symmetrische Darstellung
umgezogen werden. Fachpaket-Verzeichnisse entstehen mit tatsächlichem Code und
Tests, nicht als leere Gerüste. Die dargestellten Fachpakete sind Zielstruktur;
dieses ADR behauptet nicht, dass sie schon gebaut oder veröffentlicht sind.

Beispiel der späteren Abhängigkeit in einer Anwendung:

```text
# requirements.txt — Zielvertrag, noch keine Veröffentlichung behauptet
auditcore_dummygenerator==0.1.0
```

Das zugehörige Debian-Paket heißt `python3-auditcore-dummygenerator`.
Eine Debian-Anwendung deklariert dieses Paket in `Depends`; der Name der
Python-Distribution muss dafür nicht geändert werden.

pip benötigt das gebaute Wheel bzw. eine konfigurierte Python-Paketquelle.
APT benötigt ein .deb bzw. ein korrekt indiziertes und signiertes APT-Repository.
Git-Quellcodehosting allein macht keinen dieser Paketdienste automatisch
verfügbar. Veröffentlichung wird erst nach realen Build-/Install-/Importtests
und anwendbaren Freigabeprüfungen behauptet.

Anwendungen mit eigener isolierter venv verwenden üblicherweise pip/Wheel.
Eine Installation über APT im System-Python ist für eine normale isolierte
venv nicht automatisch sichtbar. Die Betriebsvariante muss deshalb explizit
gewählt und im realen Anwendungsprozess getestet werden.

## Pflichten pro Fachbibliothek

- Eigenes `pyproject.toml`, Lizenz-/Herkunftsnachweise, öffentliche API,
  Abhängigkeiten, Dokumentation, Characterization- und Unit-Tests.
- Wheel/sdist sowie bei Bedarf ein Debian-Paket aus demselben geprüften Code;
  keine zweite Fachimplementierung für APT.
- Installation aus `requirements.txt` und echter Import/Funktionsaufruf in
  isolierter Umgebung. Für APT Installation und Import im Ziel-System-Python.
- Reale Consumer-Migration mit Regression, Integration, Policy-Neubewertung
  und deklarierter Versionsbindung. Keine Repository-Zusammenlegung.
- Fachlich unterschiedliche Regeln bleiben versionierte Varianten; keine
  automatische Harmonisierung aufgrund gleicher Funktionsnamen.

Der [fachliche Zuschnitt](LIBRARY_CONSOLIDATION_PROPOSAL.md) konkretisiert die
Kandidaten. Seine Einzelgrenzen sind Vorschläge; die Mehrpaket-Architektur und
die Rolle von auditcore als Plattformbibliothek sind verbindlich geklärt.
