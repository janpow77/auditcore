# auditcore_funding_sources

## Zweck

Quellenprofile für Fördertransparenz, Beihilfen und das zentrale De-minimis-Register: Parser, stabile Identitäten, Bestandssemantik der Harvest-Modi, Registerabgleich und eine versionierte De-minimis-Kumulierung.

Für Anwendungen, die Begünstigtenlisten der Länder, EU-Transparenzdaten oder
das eAidRegister einlesen und auswerten (flowworkshop, flowsearch,
audit_designer). Die Abrufsteuerung (Seitenfolge, Wiederholungen,
Rate-Limits, Checkpoints) übernimmt `auditcore_harvest`; Datenbank, Scheduler
und die fachliche Beurteilung einer Kumulierung bleiben beim Consumer.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install auditcore_funding_sources \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.1.4 im
Release v0.4.1; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-funding-sources/`):

```text
auditcore_funding_sources @ https://github.com/janpow77/auditcore/releases/download/v0.4.1/auditcore_funding_sources-0.1.4-py3-none-any.whl#sha256=30eef49841af00ed791855d40d608d7122fc9cf0a471c428f546b300b0ece919
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)); hängt von
`python3-auditcore-harvest` und `python3-auditcore-common` ab:

```bash
sudo apt-get install python3-auditcore-funding-sources
```

Extras: `[xlsx]` – XLSX-Tabellen über openpyxl und defusedxml (CSV braucht
nur die Standardbibliothek); `[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

Betrag und Beihilfenummer nach dem flowworkshop-Profil lesen, dann die
registrierten De-minimis-Beihilfen eines Unternehmens zu einem Stichtag
kumulieren:

```python
from datetime import date
from decimal import Decimal

from auditcore_funding_sources import workshop
from auditcore_funding_sources.cumulation import calculate

assert workshop.parse_amount("1.234,56 €") == Decimal("1234.56")
reference, url = workshop.detect_sa_reference("Beihilfe SA.12345 gewährt")
assert reference == "SA.12345"

awards = [  # Feldnamen wie im eAidRegister
    {"referenceNumber": "A1", "beneficiaryReferenceNumber": "B-000123456",
     "grantingDate": "2025-03-01", "amountEur": "120000", "deMinimisType": "GENERAL"},
    {"referenceNumber": "A2", "beneficiaryReferenceNumber": "B-000123456",
     "grantingDate": "2022-01-15", "amountEur": "50000", "deMinimisType": "GENERAL"},
    {"referenceNumber": "A3", "beneficiaryReferenceNumber": "B-999",
     "grantingDate": "2025-05-01", "amountEur": "10000", "deMinimisType": "GENERAL"},
]
result = calculate(
    awards, reference_date=date(2026, 9, 1), undertaking_references=["B-000123456"]
)
assert result.decision is None  # die Beurteilung bleibt fachlich
assert result.profile_status == "REVIEW_REQUIRED"
```

```pycon
>>> [(a.reference_number, a.status) for a in result.awards]
[('A1', 'considered'), ('A2', 'excluded'), ('A3', 'excluded')]
>>> result.sum_considered_eur, result.ceiling_eur, result.exceeds_ceiling
(Decimal('120000'), Decimal('300000'), False)
```

Abruf über `auditcore_harvest` (Transport injiziert der Consumer):

```python no-run
from auditcore_harvest import AdapterRegistry, HarvestRequest
from auditcore_funding_sources import adapters

registry = AdapterRegistry()
adapters.register(registry)
engine.run(registry.create("funding.de_minimis_eaid"),
           HarvestRequest("funding.de_minimis_eaid", run_id="…"), sink, config={"country": "DE"})
```

## API-Überblick

| Modul | Inhalt |
|---|---|
| `workshop` | Profil `flowworkshop.beneficiaries`: `parse_amount`, `parse_date`, `normalize_company_name`, `detect_sa_reference`, `compute_record_hash`, Spaltenerkennung, `parse_file`, Fondsfilter, Snapshot-Validierung |
| `flowsearch` | Getrennte Variante `flowsearch.beneficiaries`: Float-Beträge, MD5-`project_id`, Mapping je Quelle, ZIP mit Größengrenze |
| `designer` | Designer-Varianten `parse_amount`, `parse_rate`, `parse_date` (alte Namen `parse_betrag`, `parse_satz`, `parse_datum` als Aliase mit `DeprecationWarning`), eigener Hash und State-Aid-Parser |
| `tables` | CSV (Standardbibliothek) und XLSX (`[xlsx]`) mit der Kopfzeilenerkennung des Originals, `typing="legacy"`/`"text"`, `header_detection="legacy"`/`"strict"`, Ressourcengrenzen |
| `snapshot` | Datenbankfreier Plan der Modi `smart`, `full-refresh`, `force`, `snapshot` |
| `deminimis` | eAidRegister: Suchkriterien, Anfragen, Antwortprüfung, Feldabbildung, Behördenebene, Satz-/Bestandshash, Vollständigkeitsregel |
| `cumulation` | De-minimis-Kumulierung mit Regelprofil, Stichtag, Unternehmenszuordnung und Begründung je Meldung; kein Urteil, keine Förderreserve |
| `adapters` | `funding.de_minimis_eaid`, `funding.eu_beneficiaries` (flowworkshop), `funding.eu_beneficiaries.flowsearch` für `auditcore_harvest` |

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
`auditcore_funding_sources` definiert kein `__all__`; die Module sind der Einstieg.

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_funding_sources.adapters` | Source adapters for ``auditcore_harvest`` (contract ``auditcore_harvest.contract/1``). |
| `auditcore_funding_sources.cumulation` | De-minimis cumulation as a separate, versioned calculation contract. |
| `auditcore_funding_sources.data` | – |
| `auditcore_funding_sources.deminimis` | Source profile ``designer.deminimis.register``: central de-minimis register (eAidRegister). |
| `auditcore_funding_sources.deminimis_inventory` | De-minimis register inventory: record identities and reconciliation of one harvest. |
| `auditcore_funding_sources.designer` | Source profile ``designer.beneficiaries`` / ``designer.state_aid``: separate variants. |
| `auditcore_funding_sources.errors` | Error contract of the package. |
| `auditcore_funding_sources.flowsearch` | Source profile ``flowsearch.beneficiaries``: a separate, not harmonised variant. |
| `auditcore_funding_sources.profiles` | Packaged, versioned data profiles; every result names the profile it used. |
| `auditcore_funding_sources.snapshot` | Inventory semantics of the four flowworkshop harvest modes, as a database-free plan. |
| `auditcore_funding_sources.tables` | Table readers for transparency lists (CSV with the standard library, XLSX optional). |
| `auditcore_funding_sources.workshop` | Source profile ``flowworkshop.beneficiaries``: parsers, identity and snapshot checks. |
| `auditcore_funding_sources.workshop_state_aid` | flowworkshop ``state_aid_service``: amount, date, names and SA references. |
<!-- api-overview:end -->

## Profile und Konfiguration

Profile (versioniert, mit Fingerprint): `flowworkshop.beneficiaries`
2026.09.1, `designer.state_aid` 2026.09.1,
`designer.deminimis.authority_levels` 2026.09.1 und
`designer.deminimis.cumulation` 2026.09.1 – letzteres `REVIEW_REQUIRED`,
keine bestätigte Rechtslage (Höchstbetrag 300 000 EUR nur bei ausschließlich
`GENERAL`, Fenster drei Kalenderjahre mit beiden Randtagen).

Wählbare Leseoptionen: `typing="legacy"` (pandas-Typinferenz wie das Original,
PLZ `01067` wird `1067`) oder `"text"`; `header_detection="legacy"` oder
`"strict"`. `calculate` verlangt einen ausdrücklichen Stichtag und optional
die Begünstigtenreferenzen, die zusammen ein Unternehmen bilden. Adapter
lesen ihre Konfiguration (etwa `country`, `url`) aus dem Harvest-Aufruf.

## Herkunft und Charakterisierung

Extrahiert aus `janpow77/flowworkshop@a05bb21`, `janpow77/flowsearch@10cb2a3`
und `janpow77/audit_designer@030a71e` (Blobs am 22.09.2026 gegen GitHub
geprüft). `tools/capture_legacy.py` hat an den Originalen 315 (flowworkshop,
zusätzlich 11 Harvest-Läufe gegen eine Wegwerf-PostgreSQL), 112 (flowsearch)
und 384 Fälle (audit_designer, darunter 7 De-minimis-Ernteläufe) aufgezeichnet,
ohne Netzwerk. Alle Profilfunktionen reproduzieren das Original exakt
(**legacy-exakt**); die Varianten der drei Anwendungen bleiben getrennt.
Anbindung der Consumer: [docs/consumer-migration.md](docs/consumer-migration.md).

## Bewusste Verhaltensabweichungen

Korrigiert werden nur Punkte, an denen das Original Daten verlor oder
Fehlschläge als Erfolg meldete, meist als wählbare Option: Titelzeilen in CSV
werden übersprungen, `header_detection="strict"`, ZIP-Grenze 64 MiB je
Tabelle, unlesbare Dateien und unerwartete Registerantworten sind Fehler
statt „0 Datensätze“, `inventory_state` meldet den neuesten Lauf, die neue
Kumulierung behandelt negative Beträge als `unclear` und verlangt Stichtag und
Unternehmen. Offene fachliche Entscheidungen (Identität mit Quellkontext,
führende Variante, Kumulierungsprofil, Datenlizenzen) sind als
`HUMAN_DECISION_REQUIRED` markiert. Vollständig:
[docs/behavior-changes.md](docs/behavior-changes.md).

## Abhängigkeiten

Python ≥ 3.11. Pflicht: `auditcore_harvest==0.1.2` (Adaptervertrag) und
`auditcore_common==0.1.1` (Hashing, Profilladen, JSON-Sicherung, optionale
Module; seit 0.1.3). Extra
`xlsx`: openpyxl und defusedxml. Keine Abhängigkeit von pandas, der Plattform
`auditcore`, Datenbanken oder HTTP-Clients.

## Sicherheit und Datenschutz

- Begünstigtenlisten und Registerdaten können Namen natürlicher Personen
  enthalten; das De-minimis-Profil maskiert natürliche Personen (`***`) wie
  das Original. Speicherung und Löschung liegen beim Consumer.
- Kein eigener Netzwerkzugriff: Abrufe laufen über den vom Consumer
  injizierten Transport von `auditcore_harvest`. Live-Abrufe wurden nicht
  ausgeführt (NOT_CONFIGURED).
- Ressourcengrenzen beim Lesen (Größe je ZIP-Mitglied, Tabellengrenzen);
  XLSX über defusedxml.
- Datenlizenzen und Nutzungsbedingungen der Quellen (Länderlisten,
  eAidRegister) sind nicht geprüft (`REVIEW_REQUIRED`), siehe
  [docs/source-catalog.json](docs/source-catalog.json). Fixtures sind synthetisch
  im Originalformat.
- Die Kumulierung ist eine arithmetische Aussage, keine Bewilligung oder
  Ablehnung.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`) für Code und Regelprofile dieses Pakets: Der Rechteinhaber hat
am 22.09.2026 entschieden, dass die nach auditcore extrahierten Bibliotheken
MIT sind, die Quellrepositories nicht (`USER_AUTHORIZED_MIT`). Quellen, Blobs
und Erklärung: `NOTICE` und `provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
