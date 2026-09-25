# auditcore_identifiers 0.1.0 – Paketbericht

Stand 25.09.2026, Branch `feat/auditcore-identifiers`, Basis `99788a1`.
Grundlage: Inventur `docs/reports/app-helfer-python.md`, Gruppe 3
(IBAN/BIC/USt-IdNr./Steuer-ID, Klasse c).

| Prüfung | Ergebnis |
|---|---|
| `pytest` (Paket, Python 3.11 / 3.12 / 3.13) | PASS, 98 Tests (davon Replay von 33 055 Originalaufrufen) |
| `ruff check .`, `mypy --strict src`, `bandit -ll -r src` | PASS |
| `auditcore-codegate check --compare-ref origin/main` | PASS, `auditcore_identifiers` alle Metriken 0 (Baseline 0) |
| `scripts/verify_domain_packages.py --apt` (Build, Hash-Index, Installation, Isolation, Rauchtest, selektive Installation, Entfernen; Debian-Paket 1 → 2, signierte Quelle, Install/Upgrade/Remove) | PASS, 22 Prüfungen |
| Plattform-Tests (`tests/`, u. a. `test_release_preparation.py`) | PASS, 343 Tests |

Charakterisierung (`tools/capture_originals.py`, Blobs gepinnt und geprüft):

- flowinvoice `fb2d1856` und audit-portal `d8eefa42`: `services/validators.py`
  (Blob-gleich `d3c09fbd`), `pipeline/stages/validation.py`
  (`IbanChecksumRule._validate_iban`, `VatIdFormatRule.evaluate`),
  `risk_checker.RiskChecker._normalize_vat_id` – je 10 273 Aufrufe.
- auditcore `99788a1`: `auditcore_invoicesynth.identifiers`,
  `auditcore_documents` (`validation_base`, `donut_values`),
  `auditcore_entity_matching.lei`; flowworkshop `a05bb214`
  `entity_resolution` (LEI) – zusammen 12 509 Aufrufe.
- Differenzbericht Original ↔ `strict`: `packages/auditcore_identifiers/docs/differences.md`.
- Gegenprüfung python-stdnum 2.2 (offline, nur Daten); Referenzwerte mit
  Quellen: `packages/auditcore_identifiers/docs/test-vectors.md`.

Nicht ausgeführt: Veröffentlichung/Release (Hauptagent), Umstellung der
Anwendungen (Auftrag: App-Repositories nur lesen) und der auditcore-internen
Kopien (an den Refaktorierungsprozess gemeldet, siehe
`packages/auditcore_identifiers/docs/consumer-integration.md`).
