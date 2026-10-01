# ECOHESION und auditcore_account: technische Bestandsprüfung

Stand: 29. September 2026. Quellstand: `janpow77/audit_designer@aa71ce1b296564fd386605b4d96f80f6cd7a61e8`.
Live geprüft: <https://ecohesion.flowaudit.de>. Keine Anwendung geändert und keine
Produktivdaten geschrieben. [Maschinenbericht](ecohesion-account-review-20260929.json).

## Ergebnis

Viele zentrale Funktionen funktionieren in den tatsächlich ausgeführten Prüfungen.
Eine Aussage „alle Funktionen vollständig funktionsfähig und abgenommen“ ist weiterhin
nicht belegt. Die 27 Funktionsgruppen der bestehenden Abnahmematrix wurden mit dem
aktuellen Code, Tests, Live-Einstiegen und den unten genannten Referenzabläufen
abgeglichen. Nicht jede Unterfunktion wurde mit produktiven Daten Ende zu Ende geprüft.

ECOHESION ist ein eigener Anwendungseinstieg im Repository `audit_designer`.
`frontend/vite.config.ts` baut `ecohesion.html`; die separate nginx-Konfiguration und
`deploy/hetzner/compose.override.yaml` ordnen die Live-Adresse diesem Einstieg zu.
`ki-pilotprogramm` gehört laut README zu `pilot.flowaudit.de`. Workshop ist eine
Quellanwendung für gemeinsame Recherchefunktionen, nicht der hier geprüfte Einstieg.
Der letzte erfolgreiche Deployment-Workflow für diesen Quellstand ist
[Lauf 36284359108](https://github.com/janpow77/audit_designer/actions/runs/36284359108).
Das ersetzt keinen unabhängigen Hashvergleich aller laufenden Backenddateien.

## Neu ausgeführte Prüfungen

| Prüfung | Ergebnis | Grenze |
|---|---|---|
| ECOHESION-Backend | **1.651 bestanden** | Synthetische SQLite-Fixtures, externe Provider teilweise ersetzt |
| Gemeinsame Notebook-Härtung und Vorlagen | **155 bestanden** | Kein neu gestarteter echter Notebook-Container |
| ECOHESION-Frontend | **59 bestanden**, neun Testdateien | Komponenten-/Servicetests |
| Gesamtes gemeinsames Frontend | **1.315 bestanden, ein Fehler**, zwei unbehandelte Fehler | Fehler im FlowStat-AutoML-Assistenten; separat reproduziert |
| TypeScript-Prüfung / Vite-Produktionsbuild | **Bestanden** | Keine pauschale Funktionsabnahme |
| Öffentliche Live-Seiten | Acht Einstiege und elf Recherchewerkzeuge ohne JavaScript-Ausnahme | Seitenaufbau; nicht jede Live-Suche und jeder Export |
| Zugang ohne Anmeldung | Projekt-API verweigert mit 401; „Mein Bereich“ führt zur Anmeldung | Kein reales Konto für schreibende Live-Abläufe verwendet |
| Browser: Prüffall → Checkliste → Antwort → DOCX | **Bestanden** | Lokaler Referenzserver, synthetisches Mitglied statt echter Anmeldung |
| Browser: Methodenvergleich → Berechnung → XLSX | **Bestanden** | 120 synthetische Vorhaben, Vergleichsanteil 0,35 |
| Reflow der beiden Referenzabläufe | **Bestanden**, 320/360/768/1.366/1.920 Pixel | Nicht sämtliche gefüllten Detailansichten |
| Exportdateien strukturell geöffnet | DOCX: 47 Absätze; XLSX: drei Tabellenblätter | Keine Sichtprüfung in Ziel-Word/-Excel |
| Axe, vier öffentliche Seiten bei zwei Breiten | Keine bestätigten automatischen Verstöße nach Ende der Animationen | Zehn unentscheidbare Regelprüfungen; kein Screenreader-Nutzertest |
| auditcore_account-Prüfprofil | Ruff, pytest, mypy, codegate: **bestanden** | Zusätzlicher Parallelitätsfehler außerhalb bisheriger Tests gefunden |

Live wurden `/`, `/research`, `/action-plan-public`, `/self-assessment`, `/documents`,
`/sign-in`, `/impressum` und der Zugang zu `/my-space` geprüft. Der erwartete 401-Aufruf
von `/api/ecohesion/me/profile` bei anonymen Besuchern ist kein Funktionsfehler.
`/api/health` wird vom getrennten Einstieg gesperrt; der nginx-Gesundheitsendpunkt
ist `/health`. Die versehentlich verkürzte Prüfadresse `/api/ecohesion/me` ist kein
Profilendpunkt und ihr 404 wird nicht als Defekt gewertet.

Die erste Axe-Messung traf auf laufende Einblendanimationen und meldete Kontrastfehler.
Nach Beruhigung der Seite und mit reduzierter Bewegung waren sie nicht reproduzierbar;
sie sind deshalb nicht als bestätigte Gestaltungsfehler gezählt.

Für ECOHESION gibt es im untersuchten Checkout **kein auditcore-runner-Profil**.
Ausgeführt wurden die vorhandenen pytest-, Vitest-, Typecheck-, Build- und
Browserprüfungen. Der historische grüne CI-Lauf vom 27.09. enthält 4.750 bestandene
Backendtests, 42 übersprungene und 13 abgewählte Tests. Die CI schließt darüber hinaus
mehrere Datenbankintegrationstests und die FlowStat-Modultests ausdrücklich aus.

## Konkrete Verbesserungen nach Priorität

1. **Zugangsdaten atomar ändern.** In `auditcore_account/workspace_access.py`,
   `AccessForms.save`, sind Lesen/Versionsprüfung und `CredentialsService.provision`
   getrennte Transaktionen. Reproduktion gegen das installierte 0.1.0-Wheel:
   Formularrevision 1 lesen, konkurrierende Änderung auf Revision 2, Startpasswort
   mit erwarteter Revision 1 speichern: akzeptiert, neue Revision 3. Erwartet wäre
   ein Konflikt ohne Passwortänderung. Erwartete Revision in der schreibenden
   Transaktion prüfen; auch Einladungs-/Reset-Ausstellung entsprechend prüfen.
   Dies ist ein Konsistenzfehler, kein nachgewiesener Rechte-Bypass. Regressionstest
   ergänzen und korrigierte Version 0.1.1 veröffentlichen; 0.1.0 nicht überschreiben.

2. **Abhängigkeiten gezielt aktualisieren.** `npm audit --omit=dev` meldet 58
   betroffene Abhängigkeitseinträge: drei kritisch, zehn hoch, 44 mittel, einen
   niedrig. Unter anderem jsPDF, Plotly/MapLibre, axios und SheetJS/xlsx prüfen.
   Transitive Einträge sind keine 58 unabhängigen ausnutzbaren App-Lücken. Insbesondere
   muss geprüft werden, welche Adapter und Funktionen tatsächlich im Browserbundle
   genutzt werden. Kein blindes `npm audit fix --force`. Der frische Python-Installationslauf
   warnt außerdem vor der zurückgezogenen Fassung `py7zr==1.1.2` („Incomplete security fix“).

3. **AutoML-Ausnahme und Testisolation korrigieren.**
   `frontend/src/modules/flowstat/components/pipeline/wizards/AutoMLWizard.vue:58`
   greift mit `capabilities.value?.ml.automl` auf ein möglicherweise fehlendes `ml`
   zu. Bei einer unvollständigen Antwort entsteht eine TypeError-Ausnahme. API-Antwort
   validieren, fehlende Fähigkeiten sichtbar behandeln und Capability-Mocks der Tests
   isolieren. Der Fehler betrifft das gemeinsame Repository; ein Aufruf dieses
   Assistenten aus einer öffentlichen ECOHESION-Seite wurde nicht nachgewiesen.

4. **BPMN erst bei Bedarf laden.** Die Live-Startseite lädt
   `vendor-bpmn-CMbcM64l.js` bereits per modulepreload: 769.738 übertragene Bytes,
   2.292.909 dekodierte Bytes in der Messung. Editorabhängigkeiten durch gezielte
   Imports und dynamische Modulgrenzen aus dem Startpfad entfernen. Danach Ladezeit
   und Übertragungsmenge unter derselben Verbindung vergleichen.

5. **Datenaktualität überwachen.** Der öffentliche De-minimis-Analysebestand meldet
   am 29.09. einen Stand vom 10.09.2026 und 70.648 Sätze. Das ist kein Beleg für
   einen aktuellen Gesamtbestand. Ernte-/Schedulerstatus, Fehleralarme und sichtbare
   Stichtage prüfen. Die gesonderte Live-Kumulierungsabfrage nicht mit dem gespeicherten
   Analysebestand verwechseln; eine fachliche Maximalalter-Regel nicht erfinden.

6. **Integrations- und Betriebsnachweise schließen.** Ein eigenes runner-Profil,
   PostgreSQL-Migration/Restore, Redis-Sitzungen, Worker-/Dateigrenzen, echte Notebook-
   Laufzeiten und kontrollierte RAG-/OCR-Providerprüfungen ergänzen. CI-Unit-Erfolg
   nicht als Ersatz für diese Abläufe verwenden. Das Backend-pyproject enthält zudem
   die ungültige PEP-440-Version `2.0.0-router`; die requirements-Installation gelang,
   Paketwerkzeuge melden aber bereits einen Parsefehler.

7. **Fachliche Abnahme aktualisieren.** Die historische Abnahme vom 12.09. ist
   ausdrücklich negativ; Nachprüfungen vom 13.09. belegen Verbesserungen, heben sie
   aber nicht automatisch auf. Authentische Action-Plan-Grundlage, Kriterien und
   Referenzchecklisten, Betreiberunterlagen, Word-/Excel-Sichtprüfung sowie die
   vorgesehenen Nutzertests bleiben gesondert nachzuweisen. Der alte NUC-Kandidat
   `ecohesion-releases/20260912-17312d79` trägt selbst eine Abnahmesperre.

## Welche auditcore-Bibliotheken eingesetzt werden sollten

| Bereich | Tatsächlicher Bestand / Empfehlung |
|---|---|
| Namen, Passwort, Nutzer, Mandant, Corporate Design, Begrüßung | `auditcore_account` nach dem Parallelitätsfix; native Vue-Komponente aus `@auditcore/ui` verwenden. Dauerhafte Datenbank-, Datei- und Versandadapter fehlen noch. |
| Anmeldung / Token | `auditcore_auth` ist bereits über `app/core/security.py` eingebunden. ECOHESION-Cookies, Redis-Widerruf und CSRF-Prüfung erhalten. |
| Rollen / Organisationen / Projekte | Mandantenrollen aus `auditcore_account`; ECOHESION-Rollen `member/expert/admin`, Projektmitgliedschaften sowie private/Organisations-/Projekt-Sichtbarkeit ausdrücklich abbilden. Keine automatische fachliche Freigabe für Plattformadmins. |
| Stichproben und Methodenlabor | Reine Berechnung aus `labs/sampling.py` und Teilen von `labs/strategy.py` mit `auditcore_sampling`, `auditcore_statistics`, `auditcore_extrapolation` vergleichen. Methoden-/Rundungsprofile und Seed-Verhalten zuerst charakterisieren. ORM und Fachworkflow bleiben in ECOHESION. |
| Synthetische Populationen / Prüffälle | `auditcore_dummygenerator` und bei passenden Rechnungsfällen `auditcore_invoicegenerator`/`auditcore_invoicesynth`; fachliche Fallprofile und Lösungsschutz erhalten. |
| De-minimis / Beihilfen | Eigene Register-/Kumulierungslogik auf `auditcore_funding_sources` und `auditcore_harvest` abgleichen; die Bibliotheken ersetzen weder Quellenabdeckung noch die Fachentscheidung. |
| Sanktionen und Entitäten | Bereits vorhandene Nutzung von `auditcore_registry_sources` und `auditcore_entity_matching` fortführen; übrige Duplikate nur nach Verhaltensvergleich entfernen. |
| Dokumentvergleich | `auditcore_documents` ist bereits teilweise angeschlossen; workerbasierte API, Dateirechte und Quellenbezug bleiben Hostaufgabe. |
| DOCX/XLSX/PDF-Berichte | `auditcore_reporting` für Format-/Renderermechanik aus `checklist/report.py` und `labs/exports.py`; Fachinhalte und Ausfertigungslogik bleiben ECOHESION. |
| Karten / Geocoding | Vorhandenen `auditcore_geo`-Anschluss weiter nutzen; Leaflet-Interaktion, Quellenstatus und Quoten bleiben Anwendungsadapter. |
| PDF-Bearbeitung / echte Dateischwärzung | Neues `auditcore_pdf` ist erst ein Vorschlag, kein vorhandenes Paket. Vorher keine Ersetzung durch eine angeblich fertige Bibliothek. |
| Pseudonymisierung | `auditcore_privacy` fehlt noch. ECOHESIONs `sanitizer/pseudonyms.py` ist neben flowinvoice/riskanalysis ein konkreter Kandidat. Fallbindung, Kollisionsfreiheit, Mapping und Freigabegrenzen erhalten. |
| Checklisten | Gemeinsamer Kern mit Designer/Workshop ist sinnvoll, aber noch nicht als eigenständige Distribution vorhanden. |
| Notebook-/KI-Betrieb | `auditcore_llm_client` als Client weiterverwenden. Sandbox, Container, Netze, RAG-Speicher und Freigaben bleiben Dienste. |

## Zusätzliche Prüfung von auditcore_account

Die bestehenden 44 Pakettests und das runner-Profil bestehen im korrekten
Entwicklungsvirtualenv. Der erste Aufruf ohne dessen PATH konnte pytest-Imports und
codegate nicht auflösen; er wird nicht als bestanden gewertet.

Geprüfte Schutzmechanik: keine fremden Mandantenrollen, keine Delegation nicht
besessener Rechte, geschützte Systemrollen, letzte Plattformadministration,
Kontosperre und Sitzungsrevision, befristete gehashte Einmallinks, externe Identitäten,
Feldrechte und atomare Profiländerungen. Der zusätzliche Revisions-Rennfall zeigt,
dass 100 % Zeilenabdeckung keine vollständige Prüfung paralleler Abläufe ist.

Für ECOHESION fehlt ein persistenter Adapter mit Datenmigration und Transaktionsschutz.
`MemoryRepository` kopiert pro Transaktion den gesamten Zustand einschließlich Bilder
und Ereignisse; es ist keine skalierbare Produktivablage. Für größere Installationen
sind gezielte Datenbankabfragen, Paginierung, Objektspeicher, Ereignisaufbewahrung und
eine transaktionale Versand-Outbox erforderlich.

`auditcore_account` kennt Mandantenmitgliedschaften, aber keine eigenen Projektrollen
oder Anwendungsgrenzen. ECOHESIONs `EcohesionProjectMember` und der feste
`Application.ECOHESION`-Kontext müssen deshalb im Adapter erhalten bleiben.
Die Fähigkeitsschalter des Mitglieds steuern nur die Oberfläche und dürfen nicht zu
serverseitigen Berechtigungen umgedeutet werden.

## Empfohlene Reihenfolge

1. Kontobibliothek 0.1.1 mit atomarem Zugangsformular und Regressionstest vorbereiten.
2. Abhängigkeiten und AutoML-Fehler beheben; ECOHESION-Prüfprofil mit den vorhandenen Tests ergänzen.
3. Nutzer/Mandanten-Oberfläche und persistente Adapter unter Erhalt aller App-/Projektgrenzen integrieren.
4. Berechnung, Berichte und Registeradapter einzeln auf veröffentlichte Bibliotheksfassungen umstellen; je Umstellung Paritäts- und Referenzabläufe wiederholen.
5. PDF, Privacy und Checklisten als getrennte Bibliotheksvorhaben mit ihren Quellenverträgen bearbeiten.

Die Veröffentlichungslücken und weiteren Paketkandidaten stehen im
[separaten Paketbericht](PACKAGE_REVIEW_20260929.md). Diese Prüfung ist ein Befundbericht,
keine bereits ausgeführte Fehlerbehebung, Migration oder neue Gesamtfreigabe.
