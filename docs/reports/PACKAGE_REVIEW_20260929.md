# Fehlende Veröffentlichungen und neue Paketkandidaten

Stand: 29. September 2026. [Maschinenbericht](package-inventory-20260929.json).

## Ergebnis

Im Repository existieren 29 eigenständige Python-Pakete plus die Plattform `auditcore` und neun npm-Pakete. 28 Fach-/Querschnittspakete sind mit ihrer aktuellen Versionsnummer im öffentlichen auditcore-Python-Index auffindbar. `auditcore_runner` 0.1.0 und die Plattform `auditcore` 0.3.0 sind dort nicht vorhanden. Ihre Implementierung existiert; es fehlt dieser Veröffentlichungsweg, nicht der gesamte Code.

Alle neun npm-Pakete sind inzwischen auf npmjs veröffentlicht. Die Anmeldung war bereits als `NPM_TOKEN` in der GitHub-Umgebung `npm` vorhanden. Die frühere Aussage, npm sei nicht eingerichtet, war falsch. [Veröffentlichungslauf](https://github.com/janpow77/auditcore/actions/runs/36616720646). Frische Installation direkt aus der Registry sowie Vue-/React-/Controller-Smoke bestanden; die Registry-Integritäten aller neun Versionen entsprechen den signierten Release-Dateien.

## Vorhandene Python-Pakete mit unveröffentlichten Quellständen

Die tatsächlich heruntergeladenen Wheels aus v0.4.2 wurden gegen `packages/*/src` verglichen, nicht nur Versionsnummern oder Git-Tags. Bei 20 Paketen unterscheiden sich Code-/Laufzeitdateien vom veröffentlichten Wheel, obwohl die Versionsnummer unverändert ist. Reine Provenienzdateien wurden bei dieser Zählung ausgeschlossen. Byteabweichungen sind nicht automatisch fachliche Verhaltensänderungen; eine neue Veröffentlichung dieser Inhalte braucht dennoch eine neue Version.

| Paket | Aktuelle/veröffentlichte Nummer | Abweichende Laufzeitdateien |
|---|---|---|
| `auditcore_auth` | 0.1.1 | 7 |
| `auditcore_bpmn` | 0.1.2 | 3 |
| `auditcore_common` | 0.2.0 | 1 |
| `auditcore_documents` | 0.4.0 | 15 |
| `auditcore_entity_matching` | 0.2.4 | 4 |
| `auditcore_extrapolation` | 0.1.0 | 21 |
| `auditcore_funding_sources` | 0.1.5 | 4 |
| `auditcore_geo` | 0.3.1 | 3 |
| `auditcore_harvest` | 0.1.3 | 1 |
| `auditcore_identifiers` | 0.2.0 | 9 |
| `auditcore_invoicesynth` | 0.2.0 | 4 |
| `auditcore_kanban` | 0.1.2 | 11 |
| `auditcore_legal_sources` | 0.1.5 | 7 |
| `auditcore_llm_client` | 0.1.2 | 11 |
| `auditcore_price_analysis` | 0.1.3 | 5 |
| `auditcore_procurement` | 0.2.4 | 1 |
| `auditcore_reporting` | 0.3.0 | 35 |
| `auditcore_risk` | 0.3.4 | 14 |
| `auditcore_sampling` | 0.2.3 | 16 |
| `auditcore_statistics` | 0.3.4 | 4 |

Exakte interne Pins erzeugen weitere Releaseabhängigkeiten. Wenn alle 20 geänderten Pakete neu versioniert und die Pins auf diese Fassungen angehoben werden, sind zusätzlich `auditcore_account`, `auditcore_dataprotection`, `auditcore_market_indicators`, `auditcore_price_sources`, `auditcore_property_sources` und `auditcore_registry_sources` betroffen: insgesamt 26 Pakete. Das ist eine ermittelte Abhängigkeitsfolge, kein Auftrag, blind alle Pakete sofort neu zu veröffentlichen.

`auditcore_account` benötigt unabhängig davon eine Korrektur des im [ECOHESION-/Kontobericht](ECOHESION_REVIEW_20260929.md) reproduzierten Parallelitätsfehlers. Das signierte Ergänzungsrelease v0.5.0 enthält account und die UI-Dateien, aber keine neuen APT-Pakete. Für account fehlt deshalb noch die Debian-/APT-Auslieferung, sofern diese Installationsart genutzt werden soll. Alte veröffentlichte Versionen und ihre Dateien unverändert lassen.

## Tatsächlich neue Bibliotheksvorhaben

| Priorität | Paket/Fähigkeit | Belegte Quelle und nächster Schritt |
|---|---|---|
| Hoch | `auditcore_pdf` | Voruntersuchung zu `pdf-editor` vorhanden: Seitenoperationen, Anzeige, Formulare und Schwärzung. Noch kein Paket. Mit Viewer und Seitenoperationen beginnen; Schwärzung einschließlich Metadaten, Anlagen, OCR und unabhängiger Nachprüfung separat abnehmen. UI in bestehenden Vue-/React-Paketen ergänzen. |
| Hoch | `auditcore_privacy` | Bereits im Paketplan vorgesehen; Pseudonymisierung in flowinvoice/riskanalysis, zusätzlich ECOHESION `sanitizer/pseudonyms.py`. Fall-/Mandantenbindung, Kollisionsbehandlung, Mapping-Lebensdauer und Freigaben charakterisieren. Nicht mit VVT/DSFA aus `auditcore_dataprotection` verwechseln. |
| Mittel | Gemeinsamer Checklisten-Kern, Name noch festzulegen | Workshop unterstützt eigene und Designer-Paketformate; ECOHESION hat Vorlagen, Ausfertigungen, Antworten und Zusammenarbeit. Ein gemeinsamer Baum-/Antwort-/Versions-/Austauschvertrag ist belegt. Persistenz, Projekte und Freigaben bleiben Adapter. |
| Bedarf prüfen | Nachrichten-/Feedquellen | OSINT enthält Feedparser und Lesetextaufbereitung. Gemeinsamen Vertrag auf `auditcore_harvest` prüfen; eigener Paketname noch nicht beschlossen. |
| Zuerst Adapter | Dauerhafte Kontoablage, Dateiablage, Versand | Für `auditcore_account` erforderlich, aber nicht automatisch drei weitere Distributionen. Zunächst einen realen Consumer integrieren; einen gemeinsamen SQLAlchemy-/Outbox-Adapter erst bei übereinstimmendem Bedarf ausgliedern. |

PDF-Berichte aus Vorlagen gehören bereits zu `auditcore_reporting`; Dokumentvergleich zu `auditcore_documents`; Kennungen zu `auditcore_identifiers`; Konto/Mandant zu `auditcore_account`. Dafür keine parallelen neuen Bibliotheken anlegen. Fachliche Felder wie das Operationelle Programm über registrierte Erweiterungen im Account-Paket und den jeweiligen Anwendungsvalidator abbilden.

## Neu hinzugekommene Repositories und Grenzen der Inventur

Die authentifizierte Abfrage zeigt jetzt 77 eigene Repositories statt 71 im gespeicherten Funktionsinventar. Bei 19 der zuvor inventarisierten Repositories hat sich der Default-Branch-Commit geändert. Die frühere AST-Inventur ist damit kein vollständiger Nachweis des heutigen Quellstands.

| Neu im Vergleich zur alten Inventur | Einordnung der aktuellen Erstprüfung |
|---|---|
| `dsgvo` | Bereits auditcore nutzende Schulungsanwendung. Gemeinsame Konten-/Mandantenintegration prüfen; adaptive Szenariologik erst nach Abgleich weiterer Schulungsconsumer ausgliedern. |
| `flowpic`, `flowpic-medic` | Bildwerkzeuge/ComfyUI-Anwendung; kein belegter Bedarf für je ein auditcore-Fachpaket. `flowpic-medic` wurde über Dateibaum eingeordnet, nicht vollständig funktional geprüft. |
| `flowpic-template` | Bereits vorhandene Vue-/FastAPI-Vorlage; Design-/Theme-/Toastmechanik mit bestehenden UI-Kernen abgleichen, keine doppelte Komponentenbibliothek. |
| `graphify` | Bestehendes Analysewerkzeug mit eigener Distribution; Integration verwenden statt unter neuem Namen nachzubauen. |
| `simex` | Eigenständige 3D-/Resilienzanwendung. Allgemeine Konten-/UI-Bausteine nutzen; Solver und Bewertungsmodelle erst bei konkretem wiederverwendbarem Vertrag ausgliedern. |

Grundlage: vorhandene Paket- und Funktionspläne, Maschinenberichte, alle aktuellen Paketmanifeste, öffentliche Indizes/Registry, aktuelle Repository-Namen und Default-Branch-SHAs sowie gezielte README-/Dateibaumprüfung der sechs Ergänzungen. Die FlowAudit-Wissenssuche lieferte keine passende zusätzliche Bibliotheksplanung. Es wurde keine neue vollständige AST-/Fachprüfung sämtlicher 77 Repositories behauptet. ECOHESION wurde separat vertieft getestet.

## Empfohlene Reihenfolge

1. Account-Parallelitätsfehler korrigieren und als neue Version prüfen.
2. Release-Matrix für die 20 Quellabweichungen und die exakten abhängigen Pins erstellen; tatsächliche Wheel-/Consumer-Tests ausführen.
3. Runner-/Plattform-Auslieferung und bei Bedarf Account-APT ergänzen.
4. ECOHESION mit den vorhandenen Bibliotheken gezielt integrieren, zuerst Konten und Rollen unter Erhalt der Projekt-/Anwendungsgrenzen.
5. PDF und Privacy extrahieren; danach den gemeinsamen Checklistenvertrag umsetzen.

Diese Prüfung erstellt keine neuen Fachpakete und veröffentlicht keine zusätzlichen Python-Versionen. Anwendungsrepositories und Produktion blieben unverändert.
