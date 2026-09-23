# auditcore_price_analysis 0.1.0 und auditcore_price_sources 0.1.0 — Bericht

Stand: 23. September 2026. Branch `feat/auditcore-price` (Worktree
`auditcore-wt-price`, Basis `main@886a53a`). Parallel arbeiten andere Agenten
an weiteren Paketen; gemeinsame Dateien wurden nur additiv geändert
(`scripts/prepare_library_release.py`, Abschnitt H4 der Repository-Abdeckung).

## Entscheidung: zwei Distributionen

Belegt aus der Quelle: `services/calculator.py` und `services/preisauswahl.py`
(HPP-Preisvergleich Wasser/Nahwärme) teilen kein Symbol mit
`services/external_apis/` (Marktbeobachtung KPAnG, Stammdaten). Die Berechnung
braucht nur die Standardbibliothek; die Quellen hängen von
`auditcore_harvest`, Zugangsdaten und Datenrechten der Dienste ab. Daher
getrennt, wie im Plan: Berechnung ohne Netzwerkabhängigkeit.

## Umfang

| Paket | Funktionen |
|---|---|
| `auditcore_price_analysis` (Laufzeit: nur Standardbibliothek) | `calculate` (Jahreskosten Nahwärme/Wasser, Decimal, Zeilen mit Einheit/Menge/Faktor/exaktem und gerundetem Betrag), Staffeln (`parse_tiers`, `tiered_amount`), `select_tariff` (Freigabe, Gültigkeit, Q3, Standardvariante, Ausschlussgründe), `delta_pct`, `traffic_light`, `group_statistics`; versionierte Profile `regulierung.hpp.nahwaerme`, `.wasser`, `.vergleich` @2026.09.1 mit Quellbindung und Fingerprint; `legacy` = exakte Nachbildung für die Umstellung |
| `auditcore_price_sources` (Laufzeit: `auditcore_harvest==0.1.0`) | Adapter `price.bundesbank` (SDMX-JSON), `price.destatis_genesis` (aus regulierung verschoben), `price.eia_brent` (Offset-Paging), `price.tankerkoenig` (Vorprüfung, kein Änderungszeitpunkt), `price.overpass_fuel_stations` (ODbL), `price.eu_oil_bulletin` (Seiten-Snapshot); `RecordingTransport` (Quellen-Snapshots), `parse_ffcsv`, Brücken zur bestehenden Speicherung; versionierter Katalog |

Keine automatische Preisfreigabe: der Freigabestatus wird nur gelesen.
LLM-Extraktion, Plausibilisierung, Reviewqueue, Scheduler, ORM,
Laufprotokolle und Geheimnisse bleiben in regulierung.

## Quelle, Rechte

`janpow77/regulierung@853676d2b1ab792395d63c62c9f96d5edcca8c2d` = GitHub-HEAD
`main` am 23.09.2026 (Blobs in den `provenance.json`; `calculator.py`
`1d40c9ef`, `preisauswahl.py` `89b5cec4`). Lizenz MIT nach
Nutzerentscheidung vom 22.09.2026 (`USER_AUTHORIZED_MIT`), keine
Umlizenzierung der Quelle. Fixtures ausschließlich synthetisch; Datenrechte
der Dienste `REVIEW_REQUIRED` je Quelle.

## Characterization (tatsächlich ausgeführt)

- Rechner/Auswahl: `tools/capture_regulierung_calculator.py`, **274 Fälle**
  (Grenzwerte, Stichtag 01.07.2025, Staffelgrenzen und -formen, Rundung,
  fehlende und ungültige Werte, Gleitkomma-Grenzfälle, Auswahl). Legacy-Modul:
  **274/274 exakt**. Neuer Vertrag: in allen beiderseits rechnenden Fällen
  gleiche Beträge und Vergleichbarkeit; Abweichungen PA-L01 bis PA-L17
  fallgenau festgeschrieben.
- Connectoren: `tools/capture_regulierung_connectors.py`, **30 Szenarien**
  (Mock-Transport, In-Memory-SQLite, aufzeichnende Sitzung). Anfragen,
  gespeicherte Zeilen und Paket-Hashes gegen die Adapter verglichen;
  Abweichungen PS-C01 bis PS-C13.

## Tests und Gates

| Prüfung | Ergebnis |
|---|---|
| pytest `auditcore_price_analysis` | 616 passed (Replay 276, Vertrag vs. Legacy 184, Vergleich 56, Berechnung 44, Auswahl 31, Profile 19, Architektur 3, Policy 3) |
| pytest `auditcore_price_sources` | 115 passed (Consumer-Vergleich 61, Parser 21, Characterization 17, Contract-Suite 7 für 6 Adapter, Policy 4, Katalog 3, Architektur 2) |
| ruff, mypy strict, bandit (beide) | PASS |
| auditcore-quality strict (src) | Syntax, Lint, Typen, bandit, pip-audit, Tests, Supply Chain PASS; API-Vergleich NOT_EXECUTED (erste Baseline); Gesamt REVIEW_REQUIRED wegen Policy |
| Policy verwaltung-app-framework@15f5338 | analysis: F-04, F-07-Nachweisteil, F-09, F-15 VERIFIED; sources: zusätzlich F-16. Offen: F-05 (sources: Personenbezug möglich), F-07.ASSESS, T-12 (Schutzbedarf/DSFA UNKNOWN) |
| Plattform: pytest / ruff / mypy / CLI-Hilfen | 282 passed / PASS / PASS / 4× ok |
| Graphify (Laufzeitmodule) | analysis 176 Knoten / 480 Kanten, sources 137 / 217 PASS |

## Installation

`scripts/verify_domain_packages.py` (harvest, price_analysis, price_sources,
installierte Plattform, `--apt`): **35/35 PASS** – Build mit SBOM,
hashgebundene Requirements-Installation, `pip check`, Importherkunft, Smoke aus
dem installierten Wheel, selektive Installation (price_analysis ohne
Abhängigkeit; price_sources zieht genau harvest), Entfernung, Debian-Pakete
Revision 1/2, signierte APT-Quelle, Installation/Upgrade/Entfernung im
netzlosen Container. Wheel-SHA256: price_analysis `a04bfdea…c6c47d9`,
price_sources `c6b79837…a633b3642`; harvest reproduziert den
veröffentlichten Hash `bc6cf59f…b378d880`.

## Live-Smoke (je eine Abfrage, 23.09.2026)

Bundesbank PASS (5 Beobachtungen, 2 Fehlwerte), EIA PASS (16 Handelstage,
Schlüssel vorhanden), Tankerkönig PASS (11 Stationen, Schlüssel vorhanden),
EU-Seite PASS, Overpass PASS (Gebiet DE-HB, 120 Stationen). Destatis
**NOT_CONFIGURED** (GENESIS-Kennung nicht in der Prüfumgebung). Schlüssel nie
ausgegeben; Bericht ohne Datenwerte.

## Consumer regulierung (getestete Integrationsvariante)

Lokaler Branch `feat/auditcore-price-analysis-sources` (40bfa82, nicht
gepusht), Patch `docs/migrations/regulierung-price.patch`. `calculator.py`
und die reinen Teile von `preisauswahl.py` binden den Legacy-Vertrag; die
Connectoren Bundesbank, EIA, Overpass, EU-Seite laufen über die Adapter,
Destatis über den verschobenen Adapter, Tankerkönig-Health über
`check_list_response`. Isolierte venv mit den gebauten und den
veröffentlichten, hashgleichen Wheels; Wegwerf-Postgres-Container.

- Gesamte regulierung-Suite: vorher **1682 passed, 1 skipped**, nachher
  **1685 passed, 1 skipped** (3 neue Bindungstests).
- 30 Connector-Szenarien am migrierten Stand erneut erfasst: gespeicherte
  Fachzeilen in allen Szenarien identisch; Unterschiede nur dokumentiert
  (Status `teilweise`, Zähler, Fehlertexte, begrenzte Wiederholung).
- Umstellung der Requirements erst mit Release v0.3.0
  (`MIGRATION_BLOCKED` bis dahin). Anleitungen:
  `packages/*/docs/consumer-migration.md`.

Weitere Consumer (Clustering, Flagging, Indexreihen, `genesis_sync.py`,
andere Repositories): **geplant**, nicht belegt.

## Entscheidungen (DECIDED 23.09.2026, Zitat „alle empfehlungen … p3 180“)

Umgesetzt im Folge-PR (Versionen bleiben 0.1.0, noch nicht veröffentlicht):

1. PA-H01: fehlende optionale Bestandteile bleiben vergleichbar, Ergebnis `unvollstaendig` markiert.
2. PA-H02: Abweichung/Ampel/Statistik mit exakter Dezimalrundung.
3. PA-H03: Wasser-Standardverbrauch 180 m³, einzige Quelle `wasser_standard_m3`.
4. PA-H04: `valid_to` der Preiszeile wird bei der Tarifauswahl beachtet.
5. PS-H01: Status `teilweise` bei Antworten mit Hinweisen.
6. PS-H02: Tankerkönig `list.php` wird nicht gespeichert.

Die Entscheidungen stecken in den empfohlenen Profilen @2026.09.2; die
charakterisierten Profile @2026.09.1 und das Legacy-Modul bleiben bitgenau.

## REVIEW_REQUIRED

- Umlagenstichtag 01.07.2025: keine belastbare Rechtsgrundlage für einen
  „Wärmeumlagenpreis“ gefunden (01.07.2025 nur Höhenänderung der
  Gasspeicherumlage nach § 35e EnWG; Wegfall zum 01.01.2026); Wert bleibt,
  Rechercheergebnis mit Quellen im Profil.
- Datenrechte der Dienste.

## Offene Punkte

- Der Quellenkatalog von `auditcore_harvest` 0.1.0 führt die Preisquellen noch
  als `PLANNED`; Aktualisierung erst mit einer neuen harvest-Version.
- Destatis live: NOT_CONFIGURED.
