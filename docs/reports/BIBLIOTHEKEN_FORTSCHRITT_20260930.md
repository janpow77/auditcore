# Auditcore-Bibliotheken: Fortschritt und offene Arbeit

Stand: 30. September 2026. Arbeitsgrundlage: `PACKAGE_REVIEW_20260929.md`,
`ECOHESION_REVIEW_20260929.md` und die Maschinenberichte vom 29.09.2026.

## Abgeschlossen und committet

| Commit | Änderung | Nachweis |
|---|---|---|
| `a01a8b1` | Neues `@auditcore/layout`-Workspace-Paket samt Layout-Übernahmeplanung; `auditcore_account` erhält atomare Revisionsprüfung für Startpasswort, Einladung und Reset, Version 0.1.1 | Layout: Typprüfung, Build, ESLint, 5 Tests und Pack-Dry-Run bestanden (vorangehender Arbeitslauf). Account: 46 Tests, Ruff, Formatprüfung, mypy strict, Codegate und Wheel-Build bestanden. |
| `cf5f00f` | Runner-Dokumentationsprüfung unter Funktions-/Komplexitätsgrenzen gebracht und Ruff-Befunde bereinigt | 172 Tests, Ruff, Formatprüfung, mypy strict, Codegate und Wheel-Build bestanden. |

Die Account-Version 0.1.1 und das Layout-Paket liegen als Quellstand im Repository;
beide sind nicht veröffentlicht. Der Runner bleibt 0.1.0 und ist ebenfalls noch
nicht im öffentlichen Paketindex. Die Veröffentlichungsaktion wurde nicht ausgeführt.

## Bestandslage

- Der Inventurbericht weist 20 Python-Pakete mit Laufzeitdateien aus, die vom
  veröffentlichten Wheel abweichen. Byteabweichungen sind einzeln fachlich zu prüfen;
  vor einer neuen Version sind Paket- und Consumer-Tests erforderlich.
- Exakte interne Versionspins machen bei einem Release aller 20 Pakete insgesamt
  26 Pakete abhängig. Diese Kette ist noch nicht aktualisiert.
- `auditcore` 0.3.0 und `auditcore_runner` 0.1.0 fehlen im öffentlichen Index; die
  Implementierungen und ein allgemeiner GitHub-Release-Workflow sind vorhanden.
- Der globale Codegate-Bericht vom 30.09.2026 läuft auf PASS gegen die bestehende
  Baseline. Er zählt 852 dokumentierte Messbefunde über 30 Python- und 10
  JavaScript-Paketbereiche. PASS bedeutet hier Ratchet eingehalten, nicht
  Befundfreiheit. Runner und Account bestehen ihre jeweiligen Paket-Gates.
- Für `auditcore_pdf`, `auditcore_privacy` und einen gemeinsamen Checklisten-Kern
  liegen Vorhaben, Quellkandidaten oder Charakterisierungen vor; diese Pakete sind
  noch nicht implementiert.

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
5. Den Checklisten-Kern erst nach Festlegung des gemeinsamen Baum-, Antwort-,
   Versions- und Austauschvertrags extrahieren; Projekt-, Persistenz- und
   Freigabelogik bleiben zunächst Hostadapter.

## Grenzen dieses Fortschritts

Es wurden keine Quellstände in Anwendungsrepositories geändert. Insbesondere hat
`audit_designer` einen bereits vorher veränderten Arbeitsbaum; dieser blieb unangetastet.
Es gab keine externe Paketveröffentlichung, APT-Auslieferung oder Gesamtfreigabe aller
Bibliotheken. Die Inventur vom 29.09. ist ein Ausgangspunkt und ersetzt keine erneute
Verhaltensprüfung der 20 Pakete.
