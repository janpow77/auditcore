# Umstellung der Consumer (offen)

Stand 25.09.2026: Die Bibliothek ist gebaut und charakterisiert. **Keine**
Anwendung und kein auditcore-Paket ist umgestellt: App-Repositories wurden nur
gelesen (Auftrag), die auditcore-internen Kopien liegen in Paketen, an denen
parallel Refaktorierungs-Agenten arbeiten. Die Umstellung ist deshalb an den
common-/Refaktorierungsprozess gemeldet (Status `MIGRATION_PENDING`).

## Anwendungen

| Anwendung | Fundstelle | Ersatz | Hinweis |
|---|---|---|---|
| flowinvoice | `backend/app/services/validators.py`: `validate_german_tax_id`, `validate_german_vat_id`, `validate_eu_vat_id`, `validate_uk_vat_id`, `validate_iban`, `validate_bic` | Profil `flowinvoice.legacy` bzw. `legacy_flowinvoice.*` | `ValidationResult(status, field, value, message, details)` aus `CheckResult` bilden: `status`, `normalized` (VALID) bzw. `raw`, `message`, `details`. `field` bleibt App-seitig. Danach fachlich entscheiden, ob `strict` (IBAN mit Modulo 97) gilt. |
| flowinvoice | `backend/app/services/risk_checker.py`: `RiskChecker._normalize_vat_id` | `legacy_flowinvoice.normalize_vat_id` (gleich) oder `normalize_vat_id` | `normalize_vat_id` entfernt zusätzlich jeden Unicode-Leerraum. |
| audit-portal | `backend/app/services/validators.py` (Blob-gleich zu flowinvoice) | Profil `audit_portal.legacy` | wie flowinvoice |
| audit-portal | `backend/app/pipeline/stages/validation.py`: `IbanChecksumRule._validate_iban`, `VatIdFormatRule` | Profil `audit_portal.pipeline.legacy` | oder die Stufe aus `auditcore_documents` übernehmen (dort Umstellung s. u.) |
| audit-portal | `backend/app/services/risk_checker.py`: `_normalize_vat_id` | `legacy_flowinvoice.normalize_vat_id` | gleiches Verhalten, charakterisiert |

## auditcore-interne Kopien (an Refaktorierungsprozess gemeldet)

| Paket | Symbole | Ersatz | Verhalten |
|---|---|---|---|
| auditcore_invoicesynth | `identifiers.iban_valid`, `vat_id_valid`, `de_vat_check_digit`, `at_uid_check_digit`, `iban_check_digits` | Profil `invoicesynth.legacy` bzw. `iban_check_digits`, `de_vat_check_digit`, `at_uid_check_digit` | Gleich; Unterschied nur: `ValueError` des Originals bei Zeichen wie `²`/`ä` wird zu `INVALID`. `iban_check_digits` wirft wie das Original `ValueError` für ungültige Argumente. |
| auditcore_documents | `pipeline/stages/validation_base.validate_iban`, `IBAN_COUNTRY_LENGTHS`, `VAT_ID_PATTERNS`; `validation_rules.VatIdFormatRule` | Profil `flowinvoice.pipeline.legacy` | Meldungen und Entscheidungen gleich (`details["outcome"]`). `None` → `MISSING` statt `AttributeError`. |
| auditcore_documents | `pipeline/stages/donut_values.de_vat_check_digit`, `at_uid_check_digit`, `vat_id_check`, `compact` (für Kennungen) | Profil `documents.donut` | gleich; leerer Wert → `MISSING` (die Stufe überspringt ihn ohnehin). |
| auditcore_entity_matching | `lei.check_lei`, `lei_checksum_ok`, `lei_check_digits`, `extract_lei`, `is_lei_format`; `legacy.flowworkshop_is_valid_lei`, `flowworkshop_extract_lei_from_text` | `check_lei`, `lei_check_digits`, `extract_lei`; Profil `flowworkshop.legacy`, `legacy_pipeline.flowworkshop_extract_lei_from_text` | `strict` entfernt jeden Leerraum (auch innen, 44 Stichproben: `7LTW FZYI …` gültig), `entity_matching.check_lei` nur am Rand. `LeiCheck.format_ok/checksum_ok` entsprechen `reason` `invalid_format`/`invalid_checksum`. Öffentliche API von entity_matching als Deprecation-Alias erhalten. |

Nicht umzustellen (andere Aufgabe):

- `auditcore_dummygenerator.generator.generate_iban/generate_bic/generate_ustid`
  erzeugen bewusst prüfziffernlose Platzhalter (Charakterisierung dort); eine
  Umstellung auf `iban_check_digits` wäre eine Verhaltensänderung.
- `auditcore_registry_sources._legacy_flowinvoice_company.flowinvoice_validate_vat`
  ist die VIES-Onlineabfrage (Register), keine Formatprüfung.
