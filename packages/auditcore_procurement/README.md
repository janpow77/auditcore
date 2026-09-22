# auditcore_procurement

Eigenständig installierbare Bibliothek für **Vergabebekanntmachungen und
deterministische Vergabe-Vorprüfungen**: kanonischer Datensatzvertrag für
TED- und HAD-Bekanntmachungen, verhaltensgleiche TED-Normalisierung und
Dateiimport, Abfragebau, getrennte Quellvarianten der Unternehmenssuche und ein
versioniertes Precheck-Profil. Der Kern benötigt nur die Standardbibliothek.

| Extra | Inhalt |
|---|---|
| (Kern) | `records`, `ted`, `prechecks`, `company_sources` (ohne HAD-HTML) |
| `html` | HAD-Ergebnisseiten parsen (`lxml`) |
| `sources` | Harvest-Adapter `procurement.ted_awards` und `procurement.had_search` auf `auditcore_harvest==0.1.0` |

```bash
pip install auditcore_procurement==0.1.0                     # reiner Kern
pip install 'auditcore_procurement[sources,html]==0.1.0'      # plus Online-Abruf
```

```python
from decimal import Decimal
from auditcore_procurement import load_profile, normalize_notice, run_prechecks

datensatz = normalize_notice({"publication-number": "1-2024", "winner-name": "Beispiel GmbH"})
profil = load_profile("procurement.hvtg-legacy", "2026.09.1")
bericht = run_prechecks(profil, Decimal("50000"), None, None, "Liefer-/Dienstleistungen",
                        "Oeffentliche Ausschreibung", "BELOW_EU", [], mode="strict")
```

## Verträge

- **Datensatz** `auditcore_procurement.notice/1` (`records.NOTICE_FIELDS`):
  Online-Abruf und Dateiimport liefern dieselben Felder; `validate_record`
  prüft Typen, ISO-Daten und Auftragnehmer.
- **Abdeckung:** Der Standardabruf enthält nur Zuschlagsbekanntmachungen mit
  Auftragnehmer (`award_notices_with_winner`), nicht den gesamten TED-Bestand.
  Mit eigenem `query` bzw. `require_contractor=False` sind alle Typen möglich.
- **Harvest-Adapter** holen genau eine Seite; Seitenfolge, Wiederholungen,
  Rate-Limits, Checkpoints und Senke steuert `auditcore_harvest`. Beide Adapter
  bestehen dessen Contract-Suite. Nicht auswertbare Antworten sind
  `parser_error`, Notices ohne Auftragnehmer `RecordIssue` (Status `partial`).
- **Unternehmenssuche** (`company_sources`): Flowinvoice- und Designer-Variante
  für TED (Mnemonik-Felder) und HAD bleiben getrennt. `legacy_*` reproduziert
  das Original einschließlich „Fehler = leere Liste“; `ted_company_result` und
  `had_result` liefern stattdessen `ok`/`no_hit`/`rate_limited`/`failed`.
- **Prechecks** (`prechecks`): `mode="legacy"` ist ergebnisgleich zum Original,
  `mode="strict"` korrigiert P-C01…P-C04 und nennt Profil-ID, Version und
  Fingerprint. Ein Precheck-Ergebnis ist keine Prüfentscheidung.
- **Quellenkatalog** `sources_catalog.json` im Format `auditcore_harvest.catalog/1`.

Die Anwendung behält Feature-Flag, Offline-Sperren, Zugriffsrechte, Importjobs,
Datenbank und die LLM-gestützte Vergabeanalyse.

## Herkunft, Lizenz, Grenzen

Quellen: `audit-portal@d8eefa4` (TED-Harvester, `audit_prep.ted_normalize`,
Prechecks), `flowinvoice@fb2d185` und `audit_designer@030a71e`
(`company_records.py`). `audit_prep` ist kein eigenständiges Paket, sondern
Teil des Portal-Wheels; sein reiner TED-Kern wurde deshalb verhaltensgleich
übernommen und wird im Portal künftig aus dieser Bibliothek re-exportiert.
MIT für den extrahierten Bibliothekscode laut Entscheidung des Rechteinhabers
vom 22.09.2026 (`NOTICE`); die Quell-Repositories werden nicht umlizenziert.
Nutzungsbedingungen von TED und HAD sind nicht geprüft (REVIEW_REQUIRED),
Fixtures sind synthetisch im Originalformat. Schwellenwerte des Profils sind
Quellwerte ohne bestätigte Aktualität (HUMAN_DECISION_REQUIRED). Details:
[docs/behavior-changes.md](docs/behavior-changes.md).

```bash
python -m pip install -e '.[dev]'
python -m pytest && python -m ruff check . && python -m mypy src
```

Debian-Paket: `python3-auditcore-procurement` (Suggests `python3-lxml`,
`python3-auditcore-harvest`).
