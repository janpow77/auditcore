# Auditcore-Bibliotheken: Fortschritt und offene Arbeit

Stand: 30. September 2026. Arbeitsgrundlage: `PACKAGE_REVIEW_20260929.md`,
`ECOHESION_REVIEW_20260929.md` und die Maschinenberichte vom 29.09.2026.

## Abgeschlossen und committet

| Commit | Änderung | Nachweis |
|---|---|---|
| `a01a8b1` | Neues `@auditcore/layout`-Workspace-Paket samt Layout-Übernahmeplanung; `auditcore_account` erhält atomare Revisionsprüfung für Startpasswort, Einladung und Reset, Version 0.1.1 | Layout: Typprüfung, Build, ESLint, 5 Tests und Pack-Dry-Run bestanden (vorangehender Arbeitslauf). Account: 46 Tests, Ruff, Formatprüfung, mypy strict, Codegate und Wheel-Build bestanden. |
| `cf5f00f` | Runner-Dokumentationsprüfung unter Funktions-/Komplexitätsgrenzen gebracht und Ruff-Befunde bereinigt | 172 Tests, Ruff, Formatprüfung, mypy strict, Codegate und Wheel-Build bestanden. |
| `b95b4b7` | Neues Paket `auditcore_pdf` (0.1.0): vollständige PDF-Verarbeitung, Anzeige, Seitenoperationen, nachprüfbare Schwärzung und Bereinigung aller 7 Mängel aus der PDF-Editor-Charakterisierung | 29 Tests, Ruff, Formatprüfung, mypy strict, Codegate und Wheel-Build bestanden. Runner-Profil `pdf`: 0 Befunde. |
| `ba52b3c` | Neues Paket `auditcore_checklists` (0.1.0): Checklisten-Kern mit hierarchischem Prüfbaum, Antworten, Auswertung und vollständiger Parität zum Paketaustauschformat von `audit_designer` | 23 Tests, Ruff, Formatprüfung, mypy strict, Codegate und Wheel-Build bestanden. Runner-Profil `checklists`: 0 Befunde. |
| `a610990` | Neues Paket `auditcore_privacy` (0.1.0): deterministische, kollisionsfreie Pseudonymisierung, Maskierung und Scoped-Zuordnungsverwaltung (nur Einweg-Hashes, keine Klartexte) | 23 Tests, Ruff, Formatprüfung, mypy strict, Codegate und Wheel-Build bestanden. Runner-Profil `privacy`: 0 Befunde. |

Die Account-Version 0.1.1, das Layout-Paket und die drei neuen Bibliotheken `auditcore_pdf`,
`auditcore_checklists` sowie `auditcore_privacy` liegen als Quellstand im Repository;
sie sind noch nicht veröffentlicht. Der Runner bleibt 0.1.0 und ist ebenfalls noch
nicht im öffentlichen Paketindex. Die Veröffentlichungsaktion wurde nicht ausgeführt.

## Bestandslage

- Der Inventurbericht weist 20 Python-Pakete mit Laufzeitdateien aus, die vom
  veröffentlichten Wheel abweichen. Byteabweichungen sind einzeln fachlich zu prüfen;
  vor einer neuen Version sind Paket- und Consumer-Tests erforderlich.
- Exakte interne Versionspins machen bei einem Release aller 20 Pakete insgesamt
  26 Pakete abhängig. Diese Kette ist noch nicht aktualisiert.
- `auditcore` 0.3.0 und `auditcore_runner` 0.1.0 fehlen im öffentlichen Index; die
  Implementierungen und ein allgemeiner GitHub-Release-Workflow sind vorhanden.
- Der globale Codegate-Bericht läuft auf PASS gegen die bestehende Baseline.
- `auditcore_pdf`, `auditcore_checklists` und `auditcore_privacy` sind vollständig
  implementiert, qualitätsgeprüft und im Runner integriert.

## Nächste Arbeit

1. Für die 20 abweichenden Wheel-Inhalte eine Release-Matrix mit konkreten
   Quell-Diffs, Versionssprung, exakten internen Pins, Paketprüfungen und betroffenen
   Consumer-Repositories erstellen. Änderungen nicht nur aufgrund von Dateihashes
   als Verhaltensänderung einstufen.
2. Plattform und Runner mit installierbaren Wheels, CLI-Smoke und signierten
   Release-Artefakten vorbereiten. Vor jeder externen Veröffentlichung Versions- und
   Indexstatus erneut prüfen.
3. `auditcore_privacy` anhand der vorhandenen Pseudonymisierung charakterisieren:
   Scope-Bindung, deterministische Wiederholung, Kollisionsfreiheit, Schutz und
   Lebensdauer der Zuordnung. Nicht als Anonymisierung bezeichnen.
4. `auditcore_pdf` zunächst auf Anzeige und Seitenoperationen begrenzen. Die
   vorliegende Charakterisierung hat bei PDF-Schwärzung Klartextreste in Metadaten,
   Anlagen und Kommentaren sowie fehlende OCR-/Mehrzeilenfunde gezeigt. Ein
   Schwärzungsrelease benötigt daher separate Inhalts- und Metadatenprüfung.

   *Stand 04.10.2026 (teilweise überholt):* `b95b4b7` hat die Schwärzung samt
   Metadaten-, Anhangs- und Kommentarprüfung bereits umgesetzt; 0.1.0 ist seit
   v0.6.0 veröffentlicht. Die beim Einsatz in regulierung gefundenen Restlücken
   (Issue #239) schließt 0.2.0 (noch nicht veröffentlicht): Prüfung und Bereinigung
   von Lesezeichen, Formularfeldern, Verknüpfungen, benannten Zielen,
   Seitenbeschriftungen, Ebenen (auch ausgeblendet), Alt-/ActualText und
   JavaScript; gemischte Seiten mit Bildanteil und binäre Anhänge gelten als
   nicht prüfbar statt als geprüft; präzisere Standardmuster mit konservativer
   Auswahl `DEFAULT_PATTERNS`. Offen bleibt OCR: Text in Bildern wird weiterhin
   weder geschwärzt noch geprüft, nur gemeldet. Siehe
   [`packages/auditcore_pdf/CHANGELOG.md`](../../packages/auditcore_pdf/CHANGELOG.md).
5. Den Checklisten-Kern erst nach Festlegung des gemeinsamen Baum-, Antwort-,
   Versions- und Austauschvertrags extrahieren; Projekt-, Persistenz- und
   Freigabelogik bleiben zunächst Hostadapter.

## Grenzen dieses Fortschritts

Es wurden keine Quellstände in Anwendungsrepositories geändert. Insbesondere hat
`audit_designer` einen bereits vorher veränderten Arbeitsbaum; dieser blieb unangetastet.
Es gab keine externe Paketveröffentlichung, APT-Auslieferung oder Gesamtfreigabe aller
Bibliotheken. Die Inventur vom 29.09. ist ein Ausgangspunkt und ersetzt keine erneute
Verhaltensprüfung der 20 Pakete.
