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
| Länder | 249 Codes + `XK` | ISO 3166-1 alpha-2, Debian `iso-codes` 4.16.0 | `registry.py` |

Die SWIFT-Seite war am 25.09.2026 nicht erreichbar (HTTP 403); die
Beispiel-IBANs sind deshalb zusätzlich rechnerisch (Modulo 97) und gegen
python-stdnum geprüft. `BE68539007547034` lehnt python-stdnum wegen unbekannter
Bankkennung ab (nationale Prüfung, nicht Teil von ISO 13616).

Für die USt-IdNr. aller 27 EU-Staaten prüft `test_crosscheck.py`, dass
`strict` jede von python-stdnum (Format **und** nationale Prüfziffer)
akzeptierte Nummer annimmt (8 je Land, IT 2, FR 5, LU 6).
