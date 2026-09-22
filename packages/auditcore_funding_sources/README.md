# auditcore_funding_sources

Quellenprofile für Fördertransparenz, Beihilfen und das zentrale
De-minimis-Register: Parser, stabile Identitäten, Bestandssemantik der
Harvest-Modi, Registerabgleich und eine versionierte De-minimis-Kumulierung.
Die Abrufsteuerung (Seitenfolge, Wiederholungen, Rate-Limits, Checkpoints)
übernimmt `auditcore_harvest`; diese Bibliothek liefert die Quellenadapter.

```bash
pip install auditcore_funding_sources==0.1.0          # zieht auditcore_harvest==0.1.0
pip install 'auditcore_funding_sources[xlsx]==0.1.0'  # zusätzlich XLSX (openpyxl, defusedxml)
```

## Bausteine

| Modul | Inhalt |
|---|---|
| `workshop` | Profil `flowworkshop.beneficiaries`: `parse_amount`, `parse_date`, `normalize_company_name`, `detect_sa_reference`, `compute_record_hash`, Spaltenerkennung, `parse_file`, Fondsfilter, Snapshot-Validierung. |
| `flowsearch` | Getrennte Variante `flowsearch.beneficiaries`: Float-Beträge, MD5-`project_id`, Mapping je Quelle, ZIP mit Größengrenze. |
| `designer` | Getrennte Designer-Varianten: `parse_betrag`, `parse_satz`, `parse_datum`, eigener Hash und State-Aid-Parser. |
| `tables` | CSV (Standardbibliothek) und XLSX (optional) mit der Kopfzeilenerkennung des Originals, `typing="legacy"`/`"text"`, `header_detection="legacy"`/`"strict"`, Ressourcengrenzen. |
| `snapshot` | Datenbankfreier Plan der Modi `smart`, `full-refresh`, `force`, `snapshot` – geprüft gegen echte Läufe des Originals. |
| `deminimis` | eAidRegister: Suchkriterien, Anfragen, Antwortprüfung, Feldabbildung, Behördenebene, Satz-/Bestandshash, Vollständigkeitsregel. |
| `cumulation` | De-minimis-Kumulierung als eigener Vertrag mit Regelprofil, Stichtag, Unternehmenszuordnung und Begründung je Meldung; kein Urteil, keine Förderreserve. |
| `adapters` | `funding.de_minimis_eaid`, `funding.eu_beneficiaries` (flowworkshop), `funding.eu_beneficiaries.flowsearch` für `auditcore_harvest`. |

```python
from auditcore_harvest import AdapterRegistry, HarvestEngine, HarvestRequest, UrllibTransport
from auditcore_funding_sources import adapters

registry = AdapterRegistry()
adapters.register(registry)
# engine = HarvestEngine(UrllibTransport(), credentials, state, clock, sleeper)
# engine.run(registry.create("funding.de_minimis_eaid"),
#            HarvestRequest("funding.de_minimis_eaid", run_id="…"), sink, config={"country": "DE"})
```

Ein De-minimis-Lauf ist nur dann ein vollständiger Bestand
(`snapshot_complete`), wenn die vom Register gemeldete Gesamtzahl erreicht
wurde; sonst `partial`, und kein Satz darf als verschwunden gelten. Ein
abgewiesener Snapshot einer Begünstigtenliste bricht mit `parser_error` ab, der
Bestand des Consumers bleibt unberührt.

```python
from datetime import date
from auditcore_funding_sources.cumulation import calculate

ergebnis = calculate(meldungen, reference_date=date(2026, 9, 1),
                     undertaking_references=["B-000123456"])
ergebnis.to_dict()["decision"]   # immer None – die Beurteilung bleibt fachlich
```

## Herkunft, Lizenz, Grenzen

Quellen: `janpow77/flowworkshop@a05bb21`, `janpow77/flowsearch@10cb2a3`,
`janpow77/audit_designer@030a71e` (Blobs in `provenance.json`). Die in
auditcore extrahierten Bibliotheken sind nach Entscheidung des Rechteinhabers
vom 22.09.2026 MIT-lizenziert; die Quell-Repositories bleiben unverändert
(`NOTICE`). Datenlizenzen der abgerufenen Quellen sind nicht geprüft
(REVIEW_REQUIRED); Fixtures sind synthetisch im Originalformat.

Alle Profilfunktionen reproduzieren das Original exakt; Abweichungen,
korrigierte Optionen und offene fachliche Entscheidungen stehen in
[docs/behavior-changes.md](docs/behavior-changes.md). Das
Kumulierungsprofil ist `REVIEW_REQUIRED` und keine bestätigte Rechtslage.
Live-Abrufe wurden nicht ausgeführt (keine Konfiguration: NOT_CONFIGURED).

```bash
python -m pip install -e '.[dev]'
python -m pytest
python -m ruff check .
python -m mypy src
```

Debian-Paket: `python3-auditcore-funding-sources` (hängt von
`python3-auditcore-harvest` ab).
