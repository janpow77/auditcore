# Auftrag für Claude Code: weitere auditcore-Bibliotheken erstellen

Arbeite im Repository `janpow77/auditcore`. Setze den folgenden Auftrag selbstständig
mit deinen verfügbaren Werkzeugen und, wenn verfügbar, spezialisierten Agenten um.
Ein Plan allein, Beispielcode oder leere Paketgerüste erfüllen den Auftrag nicht.

## 1. Verbindliche Grundlage und tatsächlicher Arbeitsstand

Lies zuerst vollständig:

- `AUDITCORE_LASTENHEFT.md`
- `docs/architecture/ADR-001-multi-package-monorepo.md`
- `docs/architecture/IMPLEMENTATION_PLAN.md`
- `docs/architecture/DOMAIN_PACKAGE_PLAN.md`
- `docs/architecture/REPOSITORY_PACKAGE_COVERAGE.md`
- `docs/architecture/FUNCTION_OVERVIEW.md` und die dort verlinkten Detailberichte
- `docs/architecture/FUNCTIONS_REGULIERUNG_MIGRATION.md`
- die aktuellen Berichte unter `docs/reports/`
- die anwendbaren `AGENTS.md`-Dateien.

Ermittle Branch, Git-Status, vorhandene Pakete, Versionen, Releases, Tests und CI.
Beachte ausdrücklich die spätere Nutzerentscheidung im ADR: **ein Repository
mit mehreren fachlich abgegrenzten, eigenständig installierbaren Distributionen**.
Die historische Ein-Python-Projekt-Vorgabe des Lastenhefts ist dadurch ersetzt.

Die Plattform `auditcore` verwaltet Quality, Inventur, Konsolidierung, Refactoring
und Deployment. Neue Bibliotheken entstehen unter `packages/auditcore_<fachgebiet>/`
mit eigenem `pyproject.toml`, Importnamensraum, Tests, Lizenz und Requirements.
Sie benötigen die Plattform nicht automatisch zur Laufzeit. Die Anwendungen
behalten ihre eigenen Repositories, Oberfläche, Datenbank und Releases.

Bestehende Bibliotheken `auditcore_dummygenerator`, `auditcore_invoicegenerator`
und `auditcore_reporting` wiederverwenden. Prüfe, welche PDF-/Excel-Erweiterungen
bereits implementiert oder noch in Arbeit sind. Bestehende Releases sind
unveränderlich; Änderungen benötigen neue Versionen.

Erster konkreter Consumer nach Herstellung der benötigten Bibliotheken ist
`janpow77/regulierung`. Richte die Priorisierung an dessen belegten Verträgen aus:
VVT/DSFA einschließlich Berechnung und Lebenszyklus, Preisberechnung, Harvest-
Adapter sowie tatsächlich benötigte Dokument-/Reportingfunktionen. Nutze den
konkreten Refactoring-/Debianplan. Installiere versionierte Pakete über die
Requirements der Anwendung und stelle echte Imports um; keine bloße Parallelkopie.
Danach Regression/Integration, Policy-Reevaluation und ein natives Debian-Paket
mit vorgebautem Frontend, offline verfügbarer Runtime und getesteten Installations-,
Upgrade-, Restore- und Entfernungspfaden. Der heutige Compose-Updater ist kein
Nachweis einer bereits vorhandenen nativen App-Paketierung. Seine Signatur- und
Sicherungsgarantien erhalten. `READY_FOR_DEPLOYMENT` erst mit tatsächlichen Belegen.

Wenn ein anderer Agent arbeitet oder uncommittierte Änderungen vorhanden sind,
überschreibe sie nicht. Verwende einen eigenen Branch/Worktree auf einem
festgehaltenen Commit und dokumentiere noch nicht enthaltene parallele Arbeit.
Kein reset --hard, Force-Push, History-Rewrite oder Repository-Zusammenlegen.

## 2. Erste Priorität: auditcore_dataprotection vollständig erstellen

Die Bibliothek soll Anwendungen ermöglichen, **eigene Verarbeitungsverzeichnisse
und Datenschutz-Folgenabschätzungen anzulegen, zu bearbeiten, zu berechnen,
zu versionieren und auszugeben**. Formulare, Datenmodelle oder ein Regelkatalog
allein reichen ausdrücklich nicht.

Nutze die vorhandene Umsetzung aus `regulierung` als technische Quellbasis.
Verifiziere die Revision gegen GitHub. Im Paketplan stehen konkrete Dateien,
Symbole und Tests, insbesondere `services/mandant_dsgvo_service.py` und
`services/dsfa/{katalog,bewertung,verwaltung,export}.py`.

Implementiere einen zusammenhängenden, frameworkunabhängigen Vertrag für:

1. Verarbeitungsverzeichnis mit Tätigkeiten, stabilen Kennungen, erforderlichen
   Beschreibungen, Prüfungen, Änderungen und Fassungen.
2. Anlage einer DSFA aus einer konkreten Tätigkeitsfassung; Erfassung der Fragen,
   Antworten, Begründungen, Risiken, Maßnahmen und Stellungnahmen.
3. **Tatsächliche DSFA-Berechnung:** Schwellwertanalyse, Bruttorisiko aus Schwere
   und Eintrittswahrscheinlichkeit, Maßnahmenwirkung, Nettorisiko sowie einen
   nachvollziehbaren Bewertungsvorschlag einschließlich Konsultationshinweis,
   soweit das ausdrücklich ausgewählte Regelprofil dies vorsieht.
4. Versionierte, quellengebundene Frage-/Maßnahmen- und Bewertungsprofile.
   Rechtsregime, Schwellen und Gewichtungen nicht still vereinheitlichen.
5. Fachliche Bearbeitungs-/Prüf-/Freigabeübergänge und erneuten Prüfbedarf nach
   relevanten Änderungen. Freigegebene Fassungen dürfen nicht überschrieben werden.
6. Vollständige Berichtsdaten und nutzbare Exporte; vorhandene Reporting-Renderer
   bei geeignetem Vertrag verwenden, schwere Renderer nur als optionale Extras.

Nutze bereits vorhandene lokale Nachweise unter
`.auditcore/dataprotection-characterization/`, falls verfügbar; auf einem anderen
Checkout müssen diese aus den gebundenen Originalquellen reproduziert werden.
Es sind 19 Originaltests und 129 zusätzliche beobachtete Fälle dokumentiert.
Charakterisiere zuerst die Originalberechnung mit tatsächlich ausgeführten
Eingaben/Ausgaben. Teste unter anderem Grenzwerte, leere/unvollständige Antworten,
doppelte Kriterien, unbekannte Schlüssel, Regimewechsel, Maßnahmen und explizite
Restwerte. Fehlende Angaben dürfen im neuen Vertrag nicht unbemerkt zu einer
negativen Antwort oder Freigabe werden. Legacyverhalten und bewusst korrigiertes
Verhalten müssen unterscheidbar und begründet sein. Fachliche Konflikte als
HUMAN_DECISION_REQUIRED dokumentieren; an unabhängigen Funktionen weiterarbeiten.

Persistenz, Mandantenzugriff und Identität werden über definierte Schnittstellen
angebunden. Serverseitige Autorisierung, Mandantentrennung, Vier-Augen-Prüfung,
Audit-Trails und Versionssperren in der Anwendung müssen erhalten und in der
Integration getestet werden. Eine Pythonbibliothek ersetzt keine Benutzeroberfläche;
benötigte API-/UI-Anbindung im Consumer gehört als eigener Integrationsschritt dazu.

## 3. Danach Harvester, Analysen und weitere Werkzeuge

Arbeite die aktualisierte Priorisierung in `REPOSITORY_PACKAGE_COVERAGE.md` ab.
Sie erfasst 71 Repositories; der ältere Domain-Paketplan war keine vollständige
Liste. Erfinde keine weitere Universalbibliothek für alle Funktionen.

Implementiere für den Datenharvest den ausdrücklich gewünschten gemeinsamen
Kern `auditcore_harvest`. Quellenfamilien hängen von ihm ab; der Kern installiert
nicht alle Adapter. Gemeinsame Verträge und Ablaufsteuerung umfassen Abruf,
Pagination, Timeouts/Rate-Limits/Retry, Provenienz, Teilfehler, inkrementelle
Checkpoints sowie idempotente Übergabe an eine injizierbare Senke. Bestätige den
Vertrag anhand mindestens eines Funding- und eines Legal-Adapters. Checkpoints
nicht vor bestätigter Verarbeitung fortschreiben; keine unbelegte Exactly-once-
Behauptung. Spezifische Parser, Zugangsdaten und Snapshot-/Löschregeln bleiben
explizit. Details stehen in Abschnitt H0 der Repository-Abdeckung.

Liefere die dort festgelegte Adapteranleitung, öffentliche versionierte
Schnittstelle, ausführbare Referenzadapter und wiederverwendbare Contract-Tests
mit. Überführe die bereits verwendeten Quellen aus H0–H5 in einen versionierten
Quellenkatalog mit Herkunft, Consumer, Konfigurationsschema und tatsächlichem
Prüfstatus. Die vorgesehenen Quellen sind verbindlicher Inventur-/Planungsumfang;
ein Katalogeintrag allein bedeutet weder implementiert noch live getestet.

Konkrete Kandidatenfamilien sind:

- `auditcore_funding_sources`: Förderempfänger, State Aid und ausdrücklich das
  separate De-minimis-/eAidRegister-Profil; Kumulierungsberechnung als getrennten
  fachlichen Vertrag mit versionierten Regeln charakterisieren;
- `auditcore_procurement`: TED, HAD und weitere Vergabebekanntmachungen mit
  Online-Abruf, Dateiimport, Normalisierung und Vergabedatenmodellen sowie
  expliziten fachlichen Prüfprofilen. Quellenadapter nutzen `auditcore_harvest`;
  Netzwerkabhängigkeiten als Extras von reinen Berechnungen trennen;
- `auditcore_legal_sources`: Rechts-/Prüfquellen wie DIP und EUR-Lex;
- `auditcore_registry_sources`: fachlich abgegrenzte Register-/Sanktionsadapter;
- `auditcore_entity_matching`: nachvollziehbare Entitätsnormalisierung und Abgleich;
- `auditcore_statistics` und `auditcore_sampling`: statistische Verfahren und
  Stichproben mit expliziten methodischen Varianten;
- Datenschutzmechanik, Dokumente, Risiko und Vergabe gemäß Paketplan;
- weitere Preis-, Geo-, Immobilien- und Marktkerne nur mit den im Inventar
  belegten Quellen, Verträgen und Consumern.

Diese Namen sind Kandidaten, kein Auftrag, unabhängig vom Nutzen leere Pakete
zu erzeugen. Nur intern benötigte Hilfen bleiben in ihrer Fachbibliothek.
Technische Analyse-/Betriebswerkzeuge werden als passende Provider, Plugins oder
CLI-Funktionen in die vorhandene Plattform integriert, soweit ihr Vertrag passt.
Bestehende brauchbare Bibliotheken zuerst wiederverwenden statt neu verpacken.

Harvester müssen tatsächlich abrufen/parsen können: Transport injizierbar,
Timeouts, begrenzte Wiederholungen, Pagination, Rate-Limits, Quellenprovenienz,
inkrementeller Stand und Teilfehler explizit. Scheduler, ORM und Anwendungsrechte
bleiben beim Consumer. Snapshot-/Löschsemantik nicht still ändern. Belege Parser
mit Originalfixtures; externe Smoke-Tests nur mit vorhandener Konfiguration und
begrenzten, zulässigen Abrufen. Fehlende Konfiguration: NOT_CONFIGURED.

## 4. Nutze das vorhandene Framework für jedes Paket

Lies die CLI-Hilfen und bestehenden Implementierungen, statt Befehle zu erfinden:
`auditcore-quality`, `auditcore-consolidate`, `auditcore-refactor`, `auditcore-deploy`,
`auditcore-codegate`.

Pro Paket vollständig durchführen:

- GitHub-Revision, Symbole, Consumer und Quellrechte feststellen; Inventar aktualisieren.
- Originalverhalten tatsächlich charakterisieren, dann wiederverwendbaren Code ableiten.
- Öffentliche API, Typen, Fehlerverträge, Provenienz, Dokumentation und Tests erstellen.
- ApplicabilityContext vollständig erfassen. UNKNOWN bleibt unbekannt.
- FrameworkPolicyProvider gegen `janpow77/verwaltung-app-framework` ausführen.
  MUSS/BEDINGT/SOLL und tatsächliche Anwendbarkeit beachten; keine pauschale Maximal-Security.
- Code-Qualitätsmaßstäbe einhalten (verbindlich, per Ratchet erzwungen, siehe
  `docs/quality/code-quality.md`): McCabe ≤ 10 je Funktion, Module ≤ 400 Zeilen,
  Funktionen ≤ 60 Zeilen, `Any` nur sparsam, `mypy --strict` fehlerfrei,
  Bezeichner Englisch (Deutsch nur in Strings, Daten und festen fachlichen
  Schlüsseln); TypeScript/Vue: kein `any` ohne begründete Zeilenausnahme,
  complexity ≤ 12, strict + `noUncheckedIndexedAccess`, Dateien ≤ 400 Zeilen,
  Vue-SFC ≤ 250 Zeilen, keine dateiweiten `eslint-disable`. Ein **neues Paket**
  muss alle Maßstäbe vollständig erfüllen (Baseline 0). `auditcore-codegate check`
  muss grün sein; wer Altbestand verbessert, senkt im selben PR die Baseline mit
  `--update-baseline`. Ohne grünes Gate kein Release (`verify_domain_packages.py`
  und `prepare_library_release.py` blockieren).
- Quality Gates einschließlich konfiguriertem, tatsächlich ausgeführtem
  Regressionsbefehl, API-Stabilität, Security, Dependencies und Supply Chain ausführen.
- Wheel/sdist und SBOM bauen; Installation über Requirements in einer sauberen
  Umgebung und echte Funktionsaufrufe aus dem installierten Paket nachweisen.
- Debian-Paket und signierte APT-Quelle mit tatsächlichem Install-/Upgrade-/Remove-Test
  unterstützen. Auf dem Zielsystem keine Compiler, npm, Poetry, uv oder PyPI-Builddownloads.
- Mindestens einen realen Consumer über Requirements/Depends und Imports anbinden;
  bestehende Anwendungsfunktionen mit installierter Bibliothek prüfen. Bibliotheksbau
  allein ist keine abgeschlossene Anwendungsmigration. Bei Policyblockaden den
  konkreten getesteten Stand erhalten und andere Aufgaben fortsetzen.
- KIRA und Graphify nutzen, soweit verfügbar; Provenienz, Consumer, API-, Quality-,
  Policy- und Migrationsstatus speichern. GitHub bleibt die Quelle des Codes.

## 5. Rechte, Veröffentlichung und überprüfbarer Abschluss

Öffentliche Veröffentlichung in auditcore ist nach Rechteprüfung beauftragt.
Die bereits bestätigte MIT-Freigabe gilt nur für die bezeichneten Dummy-/Invoice-
Kerne; sie ist keine pauschale Freigabe aller privaten Repositories, Vorlagen oder
Datenquellen. Vorhandene Notices erhalten. Insbesondere bei regulierung Code-,
Vorlagen- und Datenrechte getrennt prüfen. Fehlende Freigaben konkret und
quellbezogen benennen; lokale autorisierte Implementierung und unabhängige Prüfungen
fortsetzen. Frage nur nach tatsächlich nicht aus Quellen/Tools klärbaren Entscheidungen.

Führe mindestens tatsächlich aus:

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
mypy src
auditcore-quality --help
auditcore-consolidate --help
auditcore-refactor --help
auditcore-deploy --help
```

Zusätzlich jedes neue/geänderte Paket isoliert installieren und seine Unit-,
Characterization-, Integrations-, Policy- und Pakettests ausführen. Bei VBA die
verbindliche FlowAudit-Prüfung des vollständigen betroffenen Projekts beachten;
bei erzeugten Office-Dateien vorhandene XML-/Schema-Prüfwerkzeuge verwenden.
Fehler analysieren, beheben und erneut prüfen; nichts allein für PASS unterdrücken.

Arbeite mit kleinen logischen Commits und nutze die vorhandene CI. PRs nicht
pollen, sondern sofort nach dem Öffnen zum Auto-Merge anmelden; GitHub mergt per
Squash, sobald die Required Checks (`code-quality-gate`, `ci-ok`) grün sind, und
löscht den Branch:

```bash
gh pr merge <nr> --auto --squash
# gleichwertig, falls gh pr merge nicht nutzbar ist (node_id aus gh api repos/…/pulls/<nr>):
gh api graphql -f id=<node_id> -f query='mutation($id:ID!){enablePullRequestAutoMerge(
  input:{pullRequestId:$id,mergeMethod:SQUASH}){clientMutationId}}'
```

Auto-Merge gibt es nur über GraphQL, nicht über REST. Ist das GraphQL-Kontingent
erschöpft, die Anmeldung nach dem Reset nachholen (`gh api rate_limit`).

Den Status bei Bedarf per REST lesen (`gh api repos/janpow77/auditcore/commits/<sha>/check-runs`).
Formatierung (ruff, ESLint --fix) und reine Baseline-Absenkungen erledigt der
Workflow `autofix` mit einem Commit „chore(autofix): …“; ebenso aktualisiert
`update-pr-branches` den Branch nach jedem Push auf main per Merge. Vor dem
eigenen Push daher `git pull --no-rebase`. Details:
`docs/deployment/ci-automatisierung.md`.

Liefere einen
vollständigen Bericht mit Paketnamen/Versionen, Funktionen, Quell-SHAs, Lizenzen,
Abhängigkeiten, echten Testzahlen, CI, Consumer-Migrationen, pip-/APT-Installation,
KIRA/Graphify, offenen fachlichen Entscheidungen und Blockern. Bei Veröffentlichung
anonyme Installation gegen den echten öffentlichen Paketpfad testen.

Behaupte PASS ausschließlich für ausgeführte bestandene Prüfungen. Verwende
NOT_EXECUTED, NOT_CONFIGURED, REVIEW_REQUIRED oder MIGRATION_BLOCKED, wenn zutreffend.
Beende nicht nach Planung oder Codeerzeugung: liefere nutzbare Pakete und Nachweise
oder benenne genau die verbleibenden externen Blockaden.
