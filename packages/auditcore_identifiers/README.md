# auditcore_identifiers

Prüfen und Normalisieren von Kennungen: **IBAN, BIC, USt-IdNr. (alle
EU-Staaten), Steuer-ID, Steuernummer, LEI und Handelsregisternummer**. Nur
Standardbibliothek; jede Prüfung liefert ein `CheckResult` und wirft für
ungültige Eingaben keine Exception.

```bash
pip install auditcore_identifiers==0.1.0
```

```python
import auditcore_identifiers as ai

r = ai.check_iban("IBAN DE89 3704 0044 0532 0130 00")
r.valid, r.normalized, r.country        # True, 'DE89370400440532013000', 'DE'
ai.check_iban("DE89370400440532013001").reason   # Reason.INVALID_CHECKSUM
ai.check_vat_id("136695976", country="DE").normalized   # 'DE136695976'
ai.check_tax_id("36 574 261 809").valid          # True
ai.check_lei("7LTWFZYICNSX8D621K86").details     # {'lou_prefix': '7LTW'}
ai.check_iban("DE89370400440532013001", profile="flowinvoice.legacy").valid  # True (ohne Mod 97)
```

## Ergebnis

`CheckResult(kind, status, raw, normalized, reason, message, country, profile, details)`

- `status`: `VALID`, `INVALID`, `MISSING` (wie `ValidationStatus` in flowinvoice).
- `reason`: `missing`, `invalid_type`, `invalid_characters`, `invalid_length`,
  `invalid_format`, `unknown_country`, `country_mismatch`, `invalid_checksum`.
- `message`: deutsch (Profil `strict`) bzw. Originalwortlaut (Legacy-Profile).
- `details`: z. B. `bban`, `expected_length`, `test_bic`, `checksum`
  (`verified`/`not_checked`), `land`, `format`. `to_dict()` liefert JSON.

## Prüfungen (Profil `strict`)

| Funktion | Prüfung |
|---|---|
| `check_iban` | Zeichen A–Z/0–9, Land im SWIFT-IBAN-Register (Release 101, 89 Länder), Länge, BBAN-Aufbau, ISO 7064 MOD 97-10; Papierform mit Leerzeichen, Bindestrichen und Präfix `IBAN` wird angenommen. Nationale Kontoprüfziffern werden nicht geprüft. |
| `check_bic` | 8 oder 11 Zeichen, ISO 9362:2014 (Institutskennung alphanumerisch), Land nach ISO 3166-1 (+XK); `details["test_bic"]` |
| `check_vat_id` | Formate aller 27 EU-Staaten (`EL` für Griechenland), `XI`, `GB`; Prüfziffer DE (ISO 7064 MOD 11,10) und AT (BMF); andere Länder `checksum: not_checked`. `country=` schränkt ein und ergänzt ein fehlendes Präfix. |
| `check_tax_id` | Steuer-ID: 11 Ziffern, erste ≠ 0, genau eine Ziffer zwei- oder dreimal (nicht drei direkt hintereinander), MOD 11,10 |
| `check_tax_number` | Steuernummer grob: 10/11 Ziffern (Landesformat) oder 13 Ziffern (Bundesformat, Länderpräfix, 5. Stelle 0); keine Länderprüfziffer |
| `check_lei` | 20 Zeichen, zwei Prüfziffern, ISO 7064 MOD 97-10; `extract_lei` für Freitext |
| `check_register_number` | HRA/HRB/GnR/GsR/PR/VR + Nummer + optionaler Buchstabenzusatz (nur Format) |

Hilfen: `format_iban`, `iban_check_digits`, `lei_check_digits`,
`de_vat_check_digit`, `at_uid_check_digit`, `normalize_vat_id`, `format_tax_id`.

## Profile

`check(kind, value, profile=..., country=...)` oder `profile=` an jeder
Funktion. `strict` ist Standard; die Legacy-Profile geben die Anwendungen
ergebnisgleich wieder und sind in [`docs/profiles.md`](docs/profiles.md) mit
Begründung beschrieben. Unbekanntes Profil → `UnknownProfileError`, Art im
Profil nicht vorhanden → `UnsupportedKindError` (Programmierfehler, keine
Eingabefehler).

## Nachweise

- `tests/test_replay.py`: 33 055 ausgeführte Originalaufrufe (flowinvoice,
  audit-portal, auditcore-interne Kopien, flowworkshop) werden von den
  Legacy-Profilen exakt wiedergegeben; erzeugt mit `tools/capture_originals.py`.
- `docs/differences.md`: Differenztabelle Original ↔ `strict`
  (`tools/difference_report.py`, im Test auf Aktualität geprüft).
- `tests/test_vectors.py` und [`docs/test-vectors.md`](docs/test-vectors.md):
  Referenzwerte mit Quellen (SWIFT-IBAN-Register, GLEIF, BZSt-Verfahren).
- `tests/test_crosscheck.py`: Gegenprüfung mit python-stdnum 2.2
  (`tools/crosscheck_stdnum.py`, offline; nur Daten im Repository).

Umstellung der Anwendungen und der auditcore-internen Kopien:
[`docs/consumer-integration.md`](docs/consumer-integration.md).
