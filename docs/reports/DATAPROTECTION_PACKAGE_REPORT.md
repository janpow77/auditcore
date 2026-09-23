# auditcore_dataprotection 0.1.0 — Bericht

Stand: 22. September 2026. Branch `feat/auditcore-dataprotection` (Worktree,
Basis `main@aac0168`). Parallele, hier nicht enthaltene Arbeit anderer Agenten:
Branch `docs/harvest-source-and-procurement-plan` (5ca252d) im Hauptcheckout.
**Nicht veröffentlicht, nicht nach `main` gemergt.** Status je Punkt unten.

## Umfang

Eigenständige Distribution `auditcore_dataprotection` (Debian
`python3-auditcore-dataprotection`), Laufzeit nur Standardbibliothek.
Extras: `excel` (openpyxl ≥ 3.0.9, `auditcore_reporting[excel]==0.2.0`),
`pdf` (WeasyPrint). Keine Laufzeitabhängigkeit auf `auditcore`.

| Fähigkeit | Umsetzung |
|---|---|
| Verarbeitungsverzeichnis | Inhaltsprüfung nach Art. 30 Abs. 1, stabile Kennungen (UUID oder quellkompatibel), Entwurf/Revision, Vier-Augen-Freigabe über alle Bearbeiter, Ablösung, Historie |
| DSFA aus Tätigkeitsfassung | Snapshot, Antworten ja/nein/unbekannt mit Begründung, Szenarien, Maßnahmen, Notwendigkeit/Verhältnismäßigkeit, Standpunkt, DSB-Stellungnahme (zugeordnet), Folgerung, Leitungsvorlage, Konsultation |
| Berechnung | Schwellwertanalyse, Brutto = Schwere × Wahrscheinlichkeit, Maßnahmenminderung (Obergrenze/Untergrenze aus Profil), explizite Restwerte, Nettorisiko, Vorschlag mit Konsultationshinweis, Trace, Profil-ID/-Version/-Fingerprint |
| Regelprofile | `regulierung.dsgvo` und `regulierung.hdsig_ji` 2026.09.1, aus dem ausgeführten Original abgeleitet, getrennt, `SOURCE_CHARACTERIZED` |
| Ablauf | Freigabeprüfungen in Originalreihenfolge, Prüfbedarf nach VVT-Änderung, Neubewertung als Folgefassung, Zurücksetzen nach inhaltlicher Änderung |
| Ports | Repository, Authorizer, AuditSink, Clock, IdFactory; In-Memory-Referenzadapter und wiederverwendbare Vertragstests |
| Export | Berichtsdaten (JSON), HTML, XLSX über `auditcore_reporting` 0.2.0, Legacy-Workbooks (openpyxl), PDF (WeasyPrint) |
| Legacy-Adapter | reproduziert regulierung exakt für die Consumer-Umstellung |

## Quelle, Rechte

`janpow77/regulierung@a5d48ea4b90a410210ec25e707781ef9e21ad743`, GitHub-HEAD
gleich lokalem Checkout. Blobs: `bewertung.py 2a34de1d`, `katalog.py 8be23a51`,
`verwaltung.py eba4ffd8`, `export.py e2a14999`, `mandant_dsgvo_service.py
992aeadc`. Repository privat, keine Lizenzdatei; Autoren laut Git: janpow77,
Claude. MIT-Freigabe des Rechteinhabers am 22.09.2026 für diese Quellen samt
Katalogtexten; BfDI-Mustervorlage (CC-BY-SA 4.0) nicht übernommen. Später
bekräftigt: „die bibliotheken sollen mit sein, die anderen repos nicht“ –
keine Umlizenzierung der Quell-Repositories.

## Characterization

`tools/capture_regulierung_legacy.py` führt das Original tatsächlich aus
(Blob-Prüfung, isolierte In-Memory-SQLite, feste Uhr, zweimal ausgeführt
und deterministisch bis auf PDF-/ZIP-Metadaten): **241 Einzelfälle,
65 Ablaufschritte (23 erwartete Fehlerfälle), HTML-Berichte, drei
Arbeitsmappen**. Der Legacy-Adapter reproduziert alle Fälle exakt; die
Berichte sind bytegleich, die Arbeitsmappen zellgleich bis auf die korrigierte
Formelzelle. Bestätigte Befunde des Originals und korrigiertes Verhalten:
DP-C01 bis DP-C20 in `packages/auditcore_dataprotection/docs/behavior-changes.md`.

## Tests und Gates (tatsächlich ausgeführt)

| Prüfung | Ergebnis |
|---|---|
| Paket-pytest (Python 3.12) | 412 passed, 1 skipped (PDF ohne WeasyPrint in der venv); Replay 243, Berechnung 60, Register 37, Profile 27, Ablauf 21, Exporte 13, Ports 5, Policy-Fälle 3, Architektur 3 |
| Exporte mit openpyxl 3.0.10 | 13 passed, 1 skipped |
| PDF mit WeasyPrint 60.2 (regulierung-venv) | `%PDF-`, ≈ 32,9 kB, externe URL blockiert |
| Plattform-pytest | 253 passed |
| ruff / ruff format / mypy strict | PASS |
| auditcore-quality strict | Syntax, Lint, Typen, bandit, pip-audit, Tests, API, Supply Chain: PASS; 3 Komplexitätswarnungen (u. a. bytegenauer Legacy-Bericht); Gesamt REVIEW_REQUIRED wegen Policy |
| Policy (verwaltung-app-framework@15f5338) | F-01, F-02, F-03, F-04, F-06, F-07-Nachweisteil, F-09, F-15 VERIFIED und artefaktgebunden (T-01/02/03/05/06/09/10/14/20/37/38); offen: F-05, F-07, F-07.ASSESS, T-12 wegen UNKNOWN Schutzbedarf/DSFA-Pflicht der Bibliothek selbst |
| Graphify | PASS, 470 Knoten, 1338 Kanten |
| GitHub-CI Commit 40727b0 | quality und domain-packages auf Python 3.11, 3.12, 3.13 PASS (Läufe 35770729316, 35770729384) |

Die API-Baseline wurde vor der Veröffentlichung einmal neu gesetzt: Die Umstellung
auf den Reporting-Renderer macht ein vorhandenes `ValueError` direkt sichtbar.
Die Signaturen blieben unverändert.

## Installation

`scripts/verify_domain_packages.py` mit der Plattform aus `main`:
Reporting 0.2.0 und Datenschutz 0.1.0 PASS. Geprüft wurden Build, SBOM,
hashgebundene Requirements-Installation, `pip check`, Importherkunft, Smoke
aus dem installierten Wheel, selektive Installation (nur
`auditcore-dataprotection`), Entfernung, Debian-Pakete, signierte APT-Quelle
sowie Installation, Upgrade 1→2 und Entfernung im netzlosen Container.
Wheel-SHA256 `8fad9df6dc376ed03c3464912ffdee4de7e701612af3d40e889e9afe23a084ec`.
Zuvor bestand derselbe Nachweis auch gemeinsam mit Dummy, Invoice und Reporting 0.1.0.

## Consumer-Migration regulierung

Branch `feat/auditcore-dataprotection` (Commits `7f25062`, `66f895b`, lokal,
nicht gepusht). `bewertung`, `katalog`, die reinen Teile von `verwaltung`,
Kennungen, Platzhalter, Bericht und Arbeitsmappen delegieren an die installierte
Bibliothek. `requirements.txt` bindet `auditcore_dataprotection[excel]==0.1.0`.
Die Oberfläche bleibt unverändert, ebenso DB, Rechte, Audit-Log und Trigger.

- 42 bestehende Tests (bewertung, verwaltung inkl. Postgres-Abläufe,
  mandant_dsgvo über die API) vorher und nachher PASS gegen einen isolierten
  Wegwerf-Container; zusätzlich 3 neue Integrationstests, zusammen 45 PASS
  mit dem finalen Wheel.
- Capture gegen den migrierten Stand: Katalog, 241 Fälle, 65 Schritte und
  Berichte identisch. Arbeitsmappen: nur die beiden Formelzellen sind jetzt
  Text (DP-C15).
- Sicherheitskorrektur DP-C12: Fassungen werden an den Mandanten der URL
  gebunden (bisher ungeprüft).

**MIGRATION_BLOCKED für die produktive Umstellung**, solange
`auditcore_dataprotection` 0.1.0 und `auditcore_reporting` 0.2.0 nicht im
Paketfeed stehen und der Branch nicht gepusht/abgenommen ist. Die Übernahme des
korrigierten Ablaufs statt des Legacy-Adapters ist HUMAN_DECISION_REQUIRED.

## Offene Entscheidungen

1. DP-C11: Zeitpunkt der dokumentierten Konsultation im Freigabeablauf.
2. JI-Profil: DSGVO-Kriterien als „strengerer Maßstab“ bleiben ein Quellprofil.
3. Framework-Referenz-DSFA (`framework/core/dsfa.py`) weicht ab und wurde nicht zusammengeführt.
4. Wechsel von regulierung auf den korrigierten Vertrag (C01/C06/C08 ändern Ergebnisse).
5. Veröffentlichung: neuer Release mit Reporting 0.2.0 und Datenschutz 0.1.0,
   Push der Consumer-Branches und Merge nach `main` stehen aus.
6. Neutrales Profil ohne Hessen-/KPAnG-Bezüge ist möglich, aber nicht beauftragt.
