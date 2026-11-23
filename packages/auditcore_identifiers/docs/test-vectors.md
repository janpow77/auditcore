# Referenzwerte und Quellen

| Art | Werte | Quelle | Test |
|---|---|---|---|
| IBAN | 36 Beispiel-IBANs (je Land eine, u. a. `DE89370400440532013000`, `GB29NWBK60161331926819`) | SWIFT IBAN Registry (Beispiel-IBAN je Land, elektronisches Format); Papierform nach ISO 13616-1 / EBS204 | `test_swift_registry_examples_are_valid`, `test_ecbs_paper_format` |
| IBAN-Aufbau | BBAN-Struktur und Länge von 89 Ländern | SWIFT IBAN Registry Release 101, übertragen in python-stdnum 2.2 `stdnum/iban.dat` | `registry.py` |
| LEI | `7LTWFZYICNSX8D621K86` (Deutsche Bank AG), `529900T8BM49AURSDO55` (Ubisecure Oy), `5493001KJTIIGC8Y1R12` (Bloomberg Finance L.P.), `529900W18LQJJN6SJ336` (Société Générale Effekten GmbH) | GLEIF, `https://api.gleif.org/api/v1/lei-records/<LEI>`, abgerufen 25.09.2026 | `test_gleif_records_are_valid` |
| USt-IdNr. DE | `DE136695976` | Verfahren ISO 7064 MOD 11,10 (BZSt); Wert aus dem Doctest von python-stdnum `stdnum.de.vat` | `test_iso_7064_mod_11_10_examples` |
| UID AT | `ATU13585627` | BMF-Verfahren; Wert aus dem Doctest von python-stdnum `stdnum.at.uid` | `test_austrian_uid_example` |
| Steuer-ID | `36574261809` gültig, `36574261890` Prüfziffer, `36554266806` Ziffernverteilung | § 139b AO, BZSt-Aufbauregeln (Regel „drei gleiche Ziffern nicht direkt hintereinander“ seit 2016); Werte aus dem Doctest von python-stdnum `stdnum.de.idnr` | `test_iso_7064_mod_11_10_examples` |
| Steuernummer | `4151081508156` (Thüringen), `4151181508156` ungültig | ELSTER-Bundesformat (13 Stellen, 5. Stelle 0); Werte aus dem Doctest von python-stdnum `stdnum.de.stnr` | `test_federal_tax_number_layout` |
| IBAN/LEI Prüfziffer 00/01/99 | `DE01370400441000000008`, `DE00370400441000000026`, `DE99370400441000000087`, `549300ABCDEFGHIAIH01` (alle Modulo 97 = 1) ungültig | ISO 7064 MOD 97-10 (Prüfziffer = 98 − Rest, also nur 02–98), verwendet von ISO 13616-1 und ISO 17442 | `test_iban_check_digits_outside_02_to_98_are_invalid`, `test_lei_check_digits_outside_02_to_98_are_invalid` |
| USt-IdNr. EU | 23 synthetische Nummern aus BG, CZ, DE, DK, EL, ES, FI, FR, HR, HU, IE, IT, LT, LU, NL, PL, PT, SE, SI (Liste in `tests/test_check_digits.py`) | zufällig erzeugt von `tools/crosscheck_stdnum.py` (`vat_valid_by_country` in `tests/fixtures/stdnum_crosscheck.json`), von python-stdnum 2.2 als prüfziffergültig angenommen; keiner Registerauskunft entnommen | `test_synthetic_valid_numbers_have_a_verified_check_digit` |
| USt-IdNr. falsche Prüfziffer | `FR16796035310`, `IT23086660670`, `BE0239792909`, `PL7539778794`, `DK54958499` (letzte Ziffer einer synthetischen Nummer geändert, `vat_mutated`) | nationale Verfahren (s. `vat_checks.py`); python-stdnum 2.2 lehnt sie ebenfalls ab | `test_wrong_national_check_digit_is_invalid` |
| Handelsregister | `HRB 0`, `HRB 012` ungültig; `Amtsgericht Frankfurt am Main HRB 12345` gültig mit Gericht | § 13 Abs. 1 HRV (fortlaufende Nummer je Abteilung, „Registerblatt“), Abs. 2 (Ortskennzeichen als Zusatz); 0 und führende Nullen sind keine fortlaufende Registerblattnummer | `test_register_number_*` |
| Länder | 249 Codes + `XK` | ISO 3166-1 alpha-2, Debian `iso-codes` 4.16.0 | `registry.py` |

Die SWIFT-Seite war am 25.09.2026 nicht erreichbar (HTTP 403); die
Beispiel-IBANs sind deshalb zusätzlich rechnerisch (Modulo 97) und gegen
python-stdnum geprüft. `BE68539007547034` lehnt python-stdnum wegen unbekannter
Bankkennung ab (nationale Prüfung, nicht Teil von ISO 13616).

Für die USt-IdNr. aller 27 EU-Staaten prüft `test_crosscheck.py`, dass
`strict` jede von python-stdnum (Format **und** nationale Prüfziffer)
akzeptierte Nummer annimmt (8 je Land, IT 2, FR 5, LU 6) und dabei die
Prüfziffer selbst rechnet (`check_digit = verified`; Ausnahmen:
französische Buchstabenschlüssel `not_checked`, tschechische Geburtsnummern
bis 1953 `none`). Für jede dieser Nummern ist zusätzlich das letzte Zeichen
verfälscht (`vat_mutated`); `strict` lehnt sie wie python-stdnum ab, außer wo
die Prüfziffer nicht prüfbar ist (dann nur `format_valid`). python-stdnum
(LGPL) dient nur als Orakel bei der Erzeugung der Testdaten; die Verfahren
sind eigenständig umgesetzt.

Nicht umgesetzt, weil nicht aus amtlicher Quelle belegbar: das Prüfverfahren
der britischen VAT-Nummer (HMRC veröffentlicht es nicht) und Zusatzregeln für
BIC-Orts- und Filialkennungen über ISO 9362 hinaus (SWIFT-Regelwerk am
23.11.2026 nicht abrufbar, HTTP 403).
