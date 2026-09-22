# AUDITCORE PLATFORM BUILD REPORT

Historischer Implementierungsbericht. Den aktuellen Mehrpaket- und Release-Stand
dokumentiert der [Fachpaketbericht](DOMAIN_PACKAGES_REPORT.md); frühere Aussagen
zur Ein-Projekt-Architektur und fehlenden Veröffentlichung unten sind zeitgebunden.

Stand: 22. September 2026. Version: 0.1.0.

Repository: `janpow77/auditcore`.
Commit des geprüften Implementierungsstands: `c44f0c4`.
Ausgangscommit: `b2f898cc0777a5d81833c8f549f61c7ab64a443e`.
Die ursprünglichen Prüfnachweise unten beziehen sich auf diesen Implementierungsstand.
Der Stand einschließlich Berichtscommit `e4e09f1` wurde inzwischen auf `origin/main`
gepusht. Die anschließend geprüfte CI-Korrektur ist Commit `26989a2`.
Ein Produktivpaket oder Release wurde weiterhin nicht veröffentlicht.

## Nachtrag: CI-Fehler und Korrektur

Der [erste GitHub-Lauf](https://github.com/janpow77/auditcore/actions/runs/35748087573)
bestand unter Python 3.12 und 3.13. Unter Python 3.11 scheiterte ausschließlich
das Dependency-Gate; die damalige Ausgabe enthielt nur `pip-audit exit=1`.

Die Ursache ließ sich in einem frischen Python-3.11.16-Container reproduzieren:
Das vorinstallierte `setuptools 79.0.1` blieb beim bisherigen Upgrade von nur
`pip` unverändert. `pip-audit` meldete dafür `PYSEC-2026-3447`
([Advisory](https://github.com/advisories/GHSA-h35f-9h28-mq5c), behoben ab 83.0.0).
Der Befund betrifft Dateiausschlüsse beim Bauen von Source-Distributionen unter
bestimmten Unicode-/Dateisystembedingungen; er belegt keinen Angriff auf auditcore.
Die exakte setuptools-Version des ursprünglichen GitHub-Runners wurde nicht
protokolliert. Nach Aktualisierung auf 84.0.0 bestand derselbe Container-Audit.

Die CI aktualisiert jetzt `pip`, `setuptools>=83` und `wheel`; auch isolierte
Builds verlangen `setuptools>=83`. Das Dependency-Gate nennt Paket, Version,
Befund-ID und korrigierte Version, ohne ungefilterte Tool-Ausgaben zu übernehmen.
Ein separater JSON-Audit wird auch nach Fehlern ausgeführt und als CI-Artefakt
gesichert. Keine Schwachstelle wurde ignoriert oder aus der Prüfung entfernt.

Erneut lokal ausgeführt: Installation mit Dev-Extras, **125 Tests bestanden**,
Ruff, Mypy (42 Quelldateien), alle CLI-Hilfen, Wheel-/sdist-Build und fünf
Self-Checks. Alle Befehle hatten Exitcode 0; die Self-Checks behalten wegen
offener Policy-Nachweise den Gesamtstatus **REVIEW_REQUIRED**. Die vier neuen
Testfälle prüfen verwertbare Dependency-Diagnosen, Geheimnisredaktion und
ungültige Tool-Antworten. Aktuelle lokale Nachweise: `.auditcore/verification/`.

Der [CI-Wiederholungslauf für 26989a2](https://github.com/janpow77/auditcore/actions/runs/35749034526)
prüft die Korrektur in allen drei Python-Versionen. Sein tatsächlicher Status
ist direkt am verlinkten Lauf nachvollziehbar. Die früher exportierten
JSON-Berichte bleiben historische Nachweise und wurden nicht nachträglich
als aktuelle Ergebnisse ausgegeben.

**Gesamtstatus: REVIEW_REQUIRED.** Die Plattform ist implementiert, installierbar
und lokal technisch geprüft. Die vollständige fachliche End-to-End-Abnahme des
Lastenhefts ist noch nicht erreicht: Es wurde keine reale Fachanwendung auf die
Bibliothek umgestellt und kein Produktivpaket freigegeben. Die konkreten
Blockaden stehen unten; Testpakete und synthetische Prüfnachweise ersetzen diese
Abnahme ausdrücklich nicht.

## auditcore

Ein Repository, ein Python-Projekt, eine Version und ein Releasezyklus.
Der Fachkern umfasst gemeinsame Prüfergebnisse, Exceptions, unveränderliche
versionierte Regeln, Provenienz und `auditcore.reporting`. Keine Runtime-
Dependencies, kein Framework-, HTTP-, Datenbank- oder Tool-Import im Fachkern.

`get_number_format` wurde aus der vorhandenen MIT-lizenzierten Flowlib-Funktion
übernommen. 34 vor der Extraktion aufgezeichnete Legacy-Fälle stimmen mit dem
Shared-Code überein. Funktionssignatur, Formatauswahl, ungenutzter optionaler
Parameter und Fehlerverhalten bleiben erhalten. Quelle:
`janpow77/flowlib`, Commit `aca2dc6aad25aea0720312dbcc6da00b0bcba330`,
`python/flowlib/excel/formats.py`. [Provenienz](../provenance/reporting.json).
Es wurden keine zusätzlichen eigenständig versionierten Python-Pakete erzeugt.
Weitere Fachdomains werden erst anhand geprüfter realer Kandidaten ergänzt.

## quality

Implementiert sind Syntax-, Framework-/Infrastrukturabhängigkeits-, Typisierungs-,
Dokumentations-, Secret-/Privacy-, Dependency-, Komplexitäts-, API-, Regressions-,
Supply-Chain- und Policy-Gates. Ruff, Mypy, Bandit, pip-audit und konfigurierte
Regressionstests werden tatsächlich aufgerufen. Fehlende Werkzeuge oder Nachweise
bleiben NOT_EXECUTED. API-Snapshots, Quellhashes, ausgeführte Befehle, ignorierte
Befunde und JSON-Berichte werden gespeichert. Python-Code und mitgelieferte Konfigurationen, Prompts und Templates werden
geprüft; der Wheel-Abgleich umfasst auch diese Ressourcen. Sensible Fundwerte
werden nicht in Klartext in Befundmeldungen ausgegeben.

Alle fünf vorgeschriebenen Self-Check-Prozesse beendeten sich mit Exitcode 0.
**Ihre fachlichen Gesamtberichte sind dennoch REVIEW_REQUIRED**, nicht PASS:
Policy-Nachweise sind offen, und die Tools enthalten neun Komplexitätswarnungen.
Im Fachkern bestehen keine technischen Warnungen. Das aktuelle Core-API erhält
den zuvor erfassten Ausgangssnapshot. Für die erstmals veröffentlichten
Tool-APIs existiert noch kein früherer Releasevergleich: NOT_EXECUTED.

Die vollständigen Ergebnisse stehen in [core-quality.json](core-quality.json),
[quality-quality.json](quality-quality.json),
[consolidator-quality.json](consolidator-quality.json),
[apprefactor-quality.json](apprefactor-quality.json) und
[deployer-quality.json](deployer-quality.json).
Exitcode und fachliche Freigabe sind in [Statussemantik](../quality-semantics.md)
getrennt definiert. Die Privacy-Prüfung ist ein technischer Indikator und keine
vollständige datenschutz- oder lizenzrechtliche Freigabe.

## Framework Policy Integration

Verbindliche Quelle: `janpow77/verwaltung-app-framework`, Commit
`15f5338f783f2c7d5760a9bb299be06d27326be0`.
AGENTS, Anforderungen, Verbindlichkeitsmatrix, Prüfkatalog, Security-Dokumente,
Standards und Register wurden gelesen. Ein separater frischer Checkout ließ
vorhandene lokale Framework-Änderungen unberührt.

Der GitFrameworkPolicyProvider lädt quellgebundene Anforderungen, prüft die
Aktualität gegen Git und dokumentiert Quellpfade und Digests. Der ausführbare
Adapter referenziert die Quelle über Hashes; Quelländerungen führen zu
REVIEW_REQUIRED. Offline-Caches gelten als POLICY_SOURCE_STALE. MUSS verlangt
Klärung, BEDINGT eine Auslöserprüfung, SOLL bleibt Empfehlung. F-07 trennt
die Schutzbedarfsklärung von zusätzlichen Kontrollen: Diese greifen erst bei
Authentifizierung, Uploads, externen Schnittstellen, KI oder erhöhtem Schutzbedarf. Eine menschliche
Abweichungsentscheidung erfordert Zuständigkeit, Referenz, Begründung,
Auswirkungen, Kompensation und passenden Framework-Commit. Der Agent hat keine
solchen Entscheidungen erzeugt.

## Applicability Evaluation

Alle verlangten Kontextfelder sowie zusätzliche Framework-Auslöser sind
modelliert. Fehlende Werte bleiben UNKNOWN. Die Profile LIBRARY, PROTOTYPE,
INTERNAL_APP, PROCEDURAL_APP, AI_ENABLED und HIGH_PROTECTION werden ausschließlich
aus Kontextfakten abgeleitet. Kein Profil ersetzt die Quellanforderungen.

`contexts/*.json` unterscheidet Fachkern und vier Werkzeuge. Der Schutzbedarf
nicht freigegebener Werkzeug-/Anwendungseinsätze sowie die konkrete KI-Nutzung
des Consolidators bleiben offen. Nicht anwendbare Anforderungen und Tests
bekommen NOT_APPLICABLE_WITH_REASON; unbekannte Auslöser REVIEW_REQUIRED.

| Artefakt | Abgeleitetes Profil | Nicht anwendbare Framework-Tests | Anwendbar, noch nicht als vollständiger Framework-Test ausgeführt | Anwendbarkeit offen |
|---|---|---:|---:|---:|
| Core | LIBRARY | 32 | 6 | 0 |
| Quality | INTERNAL_APP | 26 | 11 | 1 |
| Consolidator | INTERNAL_APP | 24 | 11 | 3 |
| AppRefactor | INTERNAL_APP | 26 | 11 | 1 |
| Deployer | INTERNAL_APP | 26 | 11 | 1 |

Diese Tabelle bezeichnet die vollständigen Prüffälle T-01 bis T-38 des externen
Frameworks. Bestandene Plattform-Unit-Tests werden nicht als vollständige
Erfüllung eines breiteren organisatorischen Prüffalls ausgegeben.

## consolidator und GitHub Inventory

DISCOVER, INVENTORY, COMPARE, CLASSIFY und PLAN sind implementiert: authentifizierte
GitHub-Inventur, AST-Symbole und Abhängigkeiten, revisionierte persistente
Kataloge, Consumer, strukturelle Duplikate, Kandidaten, Konflikte und Pläne.
Provider-Protocols trennen GitHub, KIRA und Graphify von der Fachbibliothek.
Prompts und Policies sind versioniert und mit Hashes referenziert. Der
Consolidator verändert keine Anwendung durch seine Planerstellung.

GLOBAL INITIAL INVENTORY wurde für den authentifizierten Benutzer `janpow77`
ausgeführt und anschließend inkrementell aktualisiert. GitHub blieb Codequelle.

| Erfasster Umfang | Ergebnis |
|---|---:|
| Repositories found | 71 |
| Strukturell vollständig im Python-/Manifest-Prüfumfang | 63 |
| Teilinventare wegen vorhandener Python-Syntaxfehler | 2 |
| Leere Repositories mit begründeter Nichtanwendbarkeit | 6 |
| Symbole | 84.752 |
| Dependency-/Call-Beziehungen | 549.649 |
| Repositories mit internen Python-Packages | 42 |
| Consumer-Beziehungen | 126.041 |
| Bibliothekskandidaten | 2.438 |
| Pläne aus vollständig analysierten Repositories | 2.420 |
| Wiederverwendete unveränderte Revisionen beim Update | 65 |

Die zwei Parsefehler liegen in `flowstat/backend/tests/fix_tests.py` und
`llm-rag-audit-presentation/update_app.py`. Diese Quellen wurden nicht verändert.
Der Gesamtinventarstatus ist PARTIAL; Repository-Ermittlung und Analyseversuch
sind abgeschlossen. Nicht-Python-Projekte haben Metadaten-/Manifestabdeckung;
daraus wird keine vollständige sprachübergreifende Symbolabdeckung behauptet.

Persistenz: `.auditcore/inventory/{repositories,symbols,dependencies,libraries,
consumers,candidates,plans,migrations,inventory_metadata}.json` sowie atomar
publizierte Kataloggenerationen und `current.json`. Dateimodus 0600 schützt
lokale Inventardateien. Große Quellinventare und private Checkout-Inhalte sind
nicht in Git aufgenommen. [Inventarzusammenfassung mit Digests](inventory-summary.json).

## KIRA

KIRA ist tatsächlich konfiguriert und wurde verwendet; NOT_CONFIGURED wäre hier
falsch. Der Adapter verwendet den vorhandenen Memory-API-Vertrag, prüft Inhalte
vorab, speichert Provenienz und revisionsgebundene Bestätigungen, verweigert
Credential-Redirects und prüft die zurückgegebenen Dokumentbytes.

- Repository-Katalog: alle 71 Einträge behandelt, 70 bestätigt oder unverändert
  bestätigt; ein Eintrag durch den serverseitigen Inhaltsfilter zurückgewiesen.
- Detaillierte Symbolbatches: PARTIAL. In den 55 abgeschlossenen Repository-
  Batches wurden 188 Dokumente gespeichert, 57 unverändert bestätigt,
  21 lokal zurückgehalten und 32 Requests fehlgeschlagen. Mindestens 15 weitere
  Dokumente wurden durch lokale Circuit Breaker zurückgestellt; weitere
  Repositories waren beim Abbruch noch nicht vollständig verarbeitet.
- Nach wiederholten Timeouts wurde der umfangreiche Detailimport unterbrochen.
  Bei abgebrochenen Requests ist eine nachträgliche serverseitige Speicherung
  unbekannt. Bestätigungsjournale und das vollständige lokale Inventar bleiben
  erhalten. Es wird kein vollständiger Symbolsync behauptet.
- Abschließende Policy-/Quality-/Provenienz-/Migrations-/API-Dokumente: neun
  bestätigt und durch Rücklesen bytegenau geprüft; vier wegen abweichender
  API-Rückgabe nicht bestätigt. Die vorhandene serverseitige Deduplizierung
  ist für diese getrennten Dokumente noch nicht als verlustfreier Sync geeignet.
- Ein weiterer Build-/Paketprüfstatus wurde bestätigt, ausdrücklich mit
  LOCAL_UNPUBLISHED, synthetischem Paketumfang und null produktiven Migrationen.
- Semantische Suche: ausgeführt, 20 Treffer mit strukturierter Provenienz.
  Das bestätigt weder fachliche Gleichheit noch aktuelle GitHub-Revisionen.

Die Integration verwendet die vorhandene lokale graphify-kira-Konfiguration.
Auditcore wurde dafür zusätzlich ohne Dependency-Änderungen editable in deren
vorhandene virtuelle Umgebung installiert; Credentials wurden nicht übernommen.

Kein Inhaltsfilter wurde umgangen. Details und Ledger liegen unter
`.auditcore/kira-*`; aggregierte Ergebnisse in [integrations.json](integrations.json).

## Graphify

Graphify lief tatsächlich im Code-Modus. Ergebnisse:

| Repository/Quellumfang | Knoten | Kanten | Status |
|---|---:|---:|---|
| auditcore, abschließender src-Stand | 503 | 994 | PASS |
| flowlib | 151 | 199 | PASS |
| auswertungjkb | 1.056 | 1.918 | PASS |
| regulierung | 9.543 | 23.413 | PASS |
| audit_designer | 59.023 | 128.353 | PASS |

Graphen liegen unter `.auditcore/graphify`. Die AST-Inventur liefert unabhängig
davon Import-, Call- und Kopplungsindikatoren. Dynamische Aufrufe sind dadurch
nicht vollständig auflösbar. Fehlendes Graphify würde explizit NOT_EXECUTED
und einen getrennten lokalen Fallback liefern.

## Library Candidates und Libraries / Modules created

2.264 Kandidaten benötigen Review; 70 erfordern HUMAN_DECISION_REQUIRED und
104 SECURITY_OR_POLICY_REVIEW_REQUIRED. Das sind konservative Strukturindikatoren,
keine abschließend festgestellten rechtlichen Konflikte. Insbesondere verwendet
die gleichnamige Zahlenformatfunktion in auswertungjkb andere Regeln als Flowlib;
diese wurden nicht harmonisiert.

Real neu verwendbares Fachmodul: `auditcore.reporting` mit einer aus dem
Bestand übernommenen Funktion und 34 Legacy-Vergleichen. Die Kandidaten enthalten
Domain-Ziele innerhalb von auditcore; neue Pakete werden nicht automatisch erzeugt.

## apprefactor, Applications migrated und Applications optimized

Implementiert: konkrete quellengebundene Pläne, Dry Run mit Diffs, Importersetzung,
signaturerhaltende Wrapper, Characterization in getrennten Prozessen, exakte
Regression, Dependency-Änderungen, Typannotationen, explizite Review-Patches,
Baseline-/Nachher-Prüfung, Benchmarking, abgesicherte Legacy-Bereinigung und
Rollback bei Fehlern. Erkannte Security-/Audit-Grenzen blockieren automatische Entfernung. Die
statischen Musterprüfungen ersetzen weder vollständige Anwendungstests noch
einen erforderlichen fachlichen oder sicherheitsbezogenen Review.

Eine reale Flowlib-Consumer-Umstellung wurde in einem isolierten Worktree
vorbereitet und als [Patch](../migrations/flowlib-reporting.patch) konkretisiert.
Der tatsächliche Apply-Versuch lieferte MIGRATION_BLOCKED: anwendbare
Policy-Nachweise fehlen; zusätzlich ist keine vollständige Consumer-Prüfsuite
konfiguriert. Es wurden keine Änderungen am realen Consumer angewandt.
[Maschinenlesbarer Status](../migrations/flowlib-status.json).

**Applications migrated: 0. Applications optimized: 0.**
Die Engine führt reale Dateitransformationen in den synthetischen
Integrationstests aus; daraus wird keine erfolgte Fachanwendungsmigration abgeleitet.
READY_FOR_DEPLOYMENT erfordert eine aktuelle Verifikation, Policy und vollständige
Deployment-Nachweise. Die CLI schreibt erst danach den Handoff.

## Tests, Regression und Integration

| Tatsächlich ausgeführte Prüfung | Ergebnis |
|---|---|
| `python -m pip install -e ".[dev]"` | PASS in lokaler .venv |
| pytest | 121 PASS, keine übersprungenen Tests |
| Gemessene Statement-Coverage | 72,22 % |
| `ruff check .` | PASS |
| `mypy src` | PASS, 42 Quelldateien |
| Vier Tool-CLIs und BibQuality-Alias, `--help` | PASS |
| Fünf Lastenheft-Self-Checks | Exitcode 0; Berichte REVIEW_REQUIRED |
| Bandit, über Quality ausgeführt | PASS für konfigurierte Mindestschwere |
| pip-audit, über Quality ausgeführt | PASS, keine gemeldeten bekannten Schwachstellen |
| Wheel und sdist | gebaut |
| Wheel in separater Umgebung ohne Dependencies installiert | PASS |
| Installierte Prompts, Policies, Debian-Templates und CLIs | PASS |
| Wheel-SBOM mit CycloneDX-1.6-Schema und Artifact-Digest | PASS |
| Legacy-Regression Reporting | 34 beobachtete Fälle PASS |
| Anwendungsmigration/Rollback/Policy-Grenzen | synthetische Integrationstests PASS |
| Vollständige Regression/Integration einer real migrierten Fachanwendung | NOT_EXECUTED |
| Vollständige anwendbare externe Framework-Prüffälle | siehe Anwendbarkeit; keine pauschale Freigabe |
| GitHub Actions | inzwischen ausgeführt; Erstlauf Python 3.11 FAIL, 3.12/3.13 PASS; Korrektur und Wiederholung siehe Nachtrag oben |

[Ausführungsnachweise und Output-Digests](verification.json).
Reproduzierbarer lokaler Prüfeinstieg: `python scripts/verify_platform.py` in der
installierten Entwicklungsumgebung. Keine native Office-Kompilierung oder
Office-Tests; es wurde kein VBA-Code bearbeitet.

## deployer und Debian Package Support

Implementiert: ApplicationInspection, versioniertes DeploymentProfile,
DeploymentPlan, vorgezogener Frontend-Build, Offline-Wheelhouse, gebündelte
isolierte Python-Laufzeit, Debian-native Dependencies, Build Manifest, gehashte
Templates, SBOM, Prüfsummen und reproduzierbares dpkg-deb-Build.

Die Pakete enthalten systemd-Konfiguration, ein dediziertes Servicekonto,
Konfigurationsdateien unter `/etc`, schreibbare Daten unter `/var/lib` und
Programmdateien unter `/opt`. Kein npm, Compiler, uv, Poetry oder PyPI-Zugriff
wird im Zielsystem vorausgesetzt; Debian-Laufzeitabhängigkeiten bleiben explizit.
Maintainerskripte laden keine Dependencies aus dem Netz. Daten und Konfiguration
bleiben bei Remove/Upgrade erhalten. Paketbau und Paketfreigabe sind getrennt.

## Package Installation Tests und APT

Zwei echte **synthetische Testpakete** wurden gebaut:
`.auditcore/package-lifecycle/auditcore-fixture_1.0.0_all.deb` und Version 1.1.0.
Die Gate-Eingaben hierfür sind explizit Testfixtures, keine Produktivnachweise.

Isolierte Debian-Container ohne Netzwerk während des Pakettests bestätigten
Installation, Upgrade, Remove, Daten-/Konfigurationserhalt, systemd-Unit-Syntax
und HTTP-Healthcheck unter dem dedizierten Servicebenutzer. Reproduzierte Builds
waren bytegleich. Beide Offline-Runtime-Strategien wurden mit gehashten lokalen
Wheels installiert und durch tatsächliche Imports geprüft.

**Echter systemd-PID-1-Dienststart: NOT_EXECUTED.** Der Versuch scheiterte am
schreibgeschützten cgroup-Dateisystem (`Failed to create /init.scope control group`).
Der direkt gestartete Healthcheck ersetzt diesen Test nicht. Deshalb bleibt
die Paketvalidierung REVIEW_REQUIRED.

APT-Packages/Release wurden erzeugt, mit einem ausschließlich hierfür erzeugten
Testschlüssel signiert und Signaturen, Index- und Paketdigests tatsächlich
geprüft: PASS im Fixture-Umfang. Kein öffentliches APT-Repository wurde publiziert.
Kein Produktiv-/Pilotpaket erhielt eine Freigabe.

## Beurteilung der verbleibenden technischen Warnungen

Keine Warnung wurde ausgeblendet. Alle neun folgenden Befunde haben die Regel
AC-COMP-001 und bleiben bewusst sichtbar:

| Modul und Zeile | Begründung der Beibehaltung |
|---|---|
| quality/engine.py:87 | Die Gate-Orchestrierung bündelt die getrennte Status- und Fehlerbehandlung; einzelne Gates sind bereits extrahiert und durch gezielte Tests abgedeckt. |
| consolidator/analysis.py:63 | Der AST-Einstieg behandelt mehrere Symbol- und Abhängigkeitsarten; eine weitere Aufteilung wird erst mit zusätzlichen Charakterisierungsfällen vorgenommen. |
| consolidator/analysis.py:102 | Der rekursive Visitor führt Gültigkeitsbereich, Symbolart und Kopplungen zusammen; die konservative Auflösung ist im Bericht offengelegt. |
| consolidator/inventory.py:128 | Der Inventurlauf koordiniert inkrementelle Wiederverwendung, Fehlerpfade und atomare Veröffentlichung; diese Eigenschaften werden getestet. |
| consolidator/providers/knowledge.py:63 | Screening, Rückgabeprüfung, Idempotenz und Circuit Breaker bleiben explizite Sicherheitsprüfungen innerhalb einer Sync-Transaktion. |
| apprefactor/engine.py:182 | Planvorbereitung prüft jede konkrete Transformationsart und ihre Sicherheitsgrenzen vor Schreibzugriffen. |
| apprefactor/engine.py:255 | Die Migration hält Vorprüfung, Transformation, Nachprüfung und Rollback in einer nachvollziehbaren Transaktionsgrenze. |
| apprefactor/optimization.py:38 | Die Manifestbearbeitung erhält vorhandene TOML-Struktur und berücksichtigt Quotes, Kommentare und Extras; die komplexen Fälle sind getestet. |
| deployer/validation.py:40 | Der Containerprüflauf enthält mehrere reale Lifecycle- und Health-Prüfungen; deren Einzelergebnisse bleiben getrennt sichtbar. |

AC-OSS-001 in `consolidator/providers/knowledge.py:49` bezeichnet die explizite
Loopback-Adresse der HTTP-Ausnahme. Es handelt sich um eine technische
Loopback-Konstante, nicht um einen gefundenen Personenbezug oder eine interne
Produktivadresse. Die Adresse bleibt erhalten, damit Remote-Credentials HTTPS
benötigen; der Scannerbefund bleibt für die Prüfung sichtbar.

## Policy Review Required, Human Decisions Required und Open Blockers

1. **Fachanwendungsmigration:** projektbezogene Anwendbarkeit, Schutzbedarf,
   F-07-/F-09-Nachweise und vollständige Consumer-Tests fehlen. Ohne diese
   Tatsachen wird die Flowlib-Umstellung nicht angewandt. Der fertige Patch und
   Legacy-Nachweis liegen vor.
2. **Policy-Nachweise:** Core F-09/F-15 sowie weitere werkzeugspezifische
   Anforderungen sind offen. Insbesondere Datenarten/DSFA, Schutzbedarf,
   konkrete KI-Provider, Artefaktreview, Import- und Run-Nachweise benötigen
   einen prüfbaren projektspezifischen Nachweis. UNKNOWN ist keine Ablehnung.
3. **Fachliche Konflikte:** abweichende Zahlenformate sowie 70 Strukturkandidaten
   mit Regelabweichungen benötigen eine fachliche Entscheidung; 104 Kandidaten
   mit Sicherheitsbezug eine entsprechende Prüfung. Keine automatische
   Harmonisierung und keine erfundenen Entscheidungsträger.
4. **KIRA:** Filterablehnungen, wiederholte Timeouts und nicht identische
   Rückgaben verhindern die Bestätigung eines vollständigen Detail-/Policy-
   Syncs. Die lokalen Originale bleiben maßgeblich und wiederaufnehmbar.
5. **Reale Betriebsfreigabe:** keine migrierte READY_FOR_DEPLOYMENT-Anwendung;
   deshalb kein erstes Produktivpaket. Zusätzlich fehlt ein geeigneter
   systemd-Testhost für die vollständige Dienstprüfung.
6. **Externe Quellqualität und Nutzungsrechte:** zwei vorhandene Syntaxfehler
   begrenzen die Inventur; bei Kandidaten ohne festgestellte Lizenz bleibt die
   Wiederverwendung prüfpflichtig. Die tatsächlich übernommene Flowlib-Funktion
   hat einen dokumentierten MIT-Nachweis.

Die technische Basis und unabhängigen Prüfungen sind ausgeführt. Die oben
benannten Punkte bleiben offen; dieser Bericht erklärt die Gesamtaufgabe
nicht fälschlich für vollständig abgenommen.
