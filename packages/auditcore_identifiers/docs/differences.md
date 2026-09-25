# Abweichungen: Originale gegenüber dem Profil `strict`

Erzeugt mit `tools/difference_report.py` aus den ausgeführten Originalen
(`tests/fixtures/*_observed.json`). Gezählt sind nur Fälle, in denen sich das
Urteil ändert (gültig ↔ ungültig/fehlend); unterschiedliche Meldungen bei
gleichem Urteil sind nicht aufgeführt. Die Legacy-Profile geben die linke Spalte
exakt wieder (`tests/test_replay.py`). audit-portal ist hier nicht getrennt
aufgeführt, weil seine Dateien dieselben Urteile liefern (Blob-gleich bzw.
gleicher Regelteil, geprüft in `test_replay.py`).

| Vergleich | Original | strict (Grund) | Fälle | Beispiel |
|---|---|---|---:|---|
| Pipeline IbanChecksumRule | EXCEPTION:AttributeError | MISSING:missing | 1 | `{"value": null}` |
| Pipeline IbanChecksumRule | INVALID | MISSING:missing | 2 | `{"value": ""}` |
| Pipeline IbanChecksumRule | INVALID | VALID | 639 | `{"value": "DE89-3704-0044-0532-0130-00"}` |
| Pipeline IbanChecksumRule | VALID | INVALID:invalid_characters | 4 | `{"value": "CZ650800000019200014539@"}` |
| Pipeline IbanChecksumRule | VALID | INVALID:invalid_length | 7 | `{"value": "FI211234560000078"}` |
| Pipeline VatIdFormatRule | INVALID | MISSING:missing | 1 | `{"value": " "}` |
| Pipeline VatIdFormatRule | INVALID | VALID | 46 | `{"value": "de136695976"}` |
| Pipeline VatIdFormatRule | VALID | INVALID:invalid_characters | 1 | `{"value": "DE\u0661\u0663\u0666\u0666\u0669\u0665\u0669\u0667\u0666"}` |
| Pipeline VatIdFormatRule | VALID | INVALID:invalid_checksum | 27 | `{"value": "DE940317595"}` |
| Pipeline VatIdFormatRule | VALID | INVALID:invalid_format | 4 | `{"value": "BE903955048"}` |
| documents validate_iban (Donut) | EXCEPTION:AttributeError | MISSING:missing | 1 | `{"value": null}` |
| documents validate_iban (Donut) | INVALID | MISSING:missing | 2 | `{"value": ""}` |
| documents validate_iban (Donut) | INVALID | VALID | 425 | `{"value": "DE89-3704-0044-0532-0130-00"}` |
| documents validate_iban (Donut) | VALID | INVALID:invalid_characters | 4 | `{"value": "CZ650800000019200014539@"}` |
| documents validate_iban (Donut) | VALID | INVALID:invalid_length | 7 | `{"value": "FI211234560000078"}` |
| documents vat_id_check (Donut) | EXCEPTION:AttributeError | MISSING:missing | 1 | `{"value": null}` |
| documents vat_id_check (Donut) | INVALID | MISSING:missing | 2 | `{"value": ""}` |
| documents vat_id_check (Donut) | INVALID | VALID | 44 | `{"value": "DE136.695.976"}` |
| documents vat_id_check (Donut) | VALID | INVALID:invalid_characters | 1 | `{"value": "DE\u0661\u0663\u0666\u0666\u0669\u0665\u0669\u0667\u0666"}` |
| documents vat_id_check (Donut) | VALID | INVALID:invalid_format | 4 | `{"value": "BE903955048"}` |
| entity_matching check_lei | INVALID | MISSING:missing | 3 | `{"value": null}` |
| entity_matching check_lei | INVALID | VALID | 44 | `{"value": "7LTW FZYI CNSX 8D62 1K86"}` |
| flowinvoice validate_bic | INVALID | MISSING:missing | 1 | `{"value": " "}` |
| flowinvoice validate_bic | INVALID | VALID | 11 | `{"value": "1234DEFF"}` |
| flowinvoice validate_bic | VALID | INVALID:unknown_country | 4 | `{"value": "DEUTXXFF"}` |
| flowinvoice validate_eu_vat_id | INVALID | MISSING:missing | 1 | `{"country_code": null, "value": " "}` |
| flowinvoice validate_eu_vat_id | INVALID | VALID | 17 | `{"country_code": null, "value": "DE136.695.976"}` |
| flowinvoice validate_eu_vat_id | VALID | INVALID:invalid_characters | 1 | `{"country_code": null, "value": "DE\u0661\u0663\u0666\u0666\u0669\u0665\u0669\u0667\u0666"}` |
| flowinvoice validate_eu_vat_id | VALID | INVALID:invalid_checksum | 40 | `{"country_code": null, "value": "DE940317595"}` |
| flowinvoice validate_eu_vat_id | VALID | INVALID:invalid_format | 7 | `{"country_code": null, "value": "BE903955048"}` |
| flowinvoice validate_german_tax_id | INVALID | MISSING:missing | 1 | `{"value": " "}` |
| flowinvoice validate_german_tax_id | INVALID | VALID | 13 | `{"value": "2893081508152"}` |
| flowinvoice validate_german_tax_id | VALID | INVALID:invalid_characters | 1 | `{"value": "\u0661\u0662/\u0663\u0664\u0665/\u0666\u0667\u0668\u0669\u0660"}` |
| flowinvoice validate_german_vat_id | INVALID | MISSING:missing | 1 | `{"value": " "}` |
| flowinvoice validate_german_vat_id | INVALID | VALID | 3 | `{"value": "DE136.695.976"}` |
| flowinvoice validate_german_vat_id | VALID | INVALID:invalid_characters | 1 | `{"value": "DE\u0661\u0663\u0666\u0666\u0669\u0665\u0669\u0667\u0666"}` |
| flowinvoice validate_german_vat_id | VALID | INVALID:invalid_checksum | 14 | `{"value": "DE940317595"}` |
| flowinvoice validate_iban | INVALID | MISSING:missing | 1 | `{"value": " "}` |
| flowinvoice validate_iban | INVALID | VALID | 428 | `{"value": "DE89-3704-0044-0532-0130-00"}` |
| flowinvoice validate_iban | VALID | INVALID:invalid_characters | 14 | `{"value": "CY170020012800000012005276\u00df0"}` |
| flowinvoice validate_iban | VALID | INVALID:invalid_checksum | 599 | `{"value": "DE90370400440532013000"}` |
| flowinvoice validate_iban | VALID | INVALID:invalid_format | 20 | `{"value": "GB29N7BK60161331926819"}` |
| flowinvoice validate_iban | VALID | INVALID:invalid_length | 369 | `{"value": "LU28001940064475000"}` |
| flowinvoice validate_iban | VALID | INVALID:unknown_country | 7 | `{"value": "XX89370400440532013000"}` |
| flowinvoice validate_uk_vat_id | INVALID | MISSING:missing | 1 | `{"value": " "}` |
| flowinvoice validate_uk_vat_id | INVALID | VALID | 4 | `{"value": "GBGD001"}` |
| flowworkshop is_valid_lei | INVALID | MISSING:missing | 3 | `{"value": null}` |
| flowworkshop is_valid_lei | INVALID | VALID | 44 | `{"value": "7LTW FZYI CNSX 8D62 1K86"}` |
| flowworkshop is_valid_lei | VALID | INVALID:invalid_checksum | 128 | `{"value": "7LTWFZYICNSX8D621K87"}` |
| invoicesynth iban_valid | EXCEPTION:AttributeError | MISSING:missing | 1 | `{"value": null}` |
| invoicesynth iban_valid | EXCEPTION:ValueError | INVALID:invalid_characters | 50 | `{"value": "AT61190430023457320\u00b2"}` |
| invoicesynth iban_valid | INVALID | MISSING:missing | 2 | `{"value": ""}` |
| invoicesynth iban_valid | INVALID | VALID | 642 | `{"value": "DE89-3704-0044-0532-0130-00"}` |
| invoicesynth iban_valid | VALID | INVALID:invalid_characters | 1 | `{"value": "BE20409\u066314200164"}` |
| invoicesynth iban_valid | VALID | INVALID:invalid_length | 7 | `{"value": "FI211234560000078"}` |
| invoicesynth vat_id_valid | EXCEPTION:AttributeError | MISSING:missing | 1 | `{"value": null}` |
| invoicesynth vat_id_valid | INVALID | MISSING:missing | 2 | `{"value": ""}` |
| invoicesynth vat_id_valid | INVALID | VALID | 65 | `{"value": "DE136.695.976"}` |
| invoicesynth vat_id_valid | VALID | INVALID:invalid_characters | 1 | `{"value": "DE\u0661\u0663\u0666\u0666\u0669\u0665\u0669\u0667\u0666"}` |
