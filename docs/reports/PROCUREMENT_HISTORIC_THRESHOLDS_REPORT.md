# auditcore_procurement 0.2.0 / auditcore_risk 0.2.0 — historische EU-Schwellen

Stand: 23. September 2026. Nutzerentscheidung vom 23.09.2026: „c2. ja“
(historische EU-Vergabeschwellen je Jahr nachtragen; zuvor: „vergabeschwellen
sollen pro jahr hinterlegt sein“). `auditcore_procurement` 0.1.0 und
`auditcore_risk` 0.1.0 sind in v0.2.0/v0.3.0 veröffentlicht und bleiben
unverändert; die Änderung erscheint als Version 0.2.0 beider Pakete.

## Ergebnis

| Paket | Neu | Unverändert |
|---|---|---|
| `auditcore_procurement` 0.2.0 | Profil `procurement.hvtg 2026.09.3` (EU-Schwellen 2014–2027), `CURRENT_PROFILE` = 2026.09.3, `profile_from_ruleset(..., eu_version=...)` | `procurement.hvtg 2026.09.2` byte-gleich zum Tag v0.3.0 (SHA-256 `ac28af97a936319218029fe3dbc70f859ac08a75ca790f13622c3c38d8aa30fd`, Fingerprint `fbb7f26e…`); `procurement.hvtg-legacy 2026.09.1` |
| `auditcore_risk` 0.2.0 | `riskanalysis.year_bound 2026.09.4` (RF02), `flowinvoice.risk_checker 2026.09.3` (SPLIT_INVOICE) mit Verweis auf `procurement.hvtg 2026.09.3`; Extra `procurement` = `auditcore_procurement==0.2.0` | alle bisherigen Profile bitgleich (Generator neu ausgeführt, keine Diffs) |

`auditcore_risk` nutzt das neue Procurement-Profil **nicht automatisch**: jedes
Risikoprofil fixiert `procurement_eu.version`. Deshalb waren neue
Risikoprofilversionen nötig (Entscheidung C2 im Profil, `derived_from` auf die
abgelöste Fassung).

## EU-Schwellenwerte und Primärquellen

Gelesen im amtlichen deutschen Text (Cellar des Amts für Veröffentlichungen,
`http://publications.europa.eu/resource/celex/<CELEX>`; eur-lex.europa.eu
beantwortet automatisierte Abrufe mit einer WAF-Challenge). Das Profil hält je
Zeitraum Verordnung, geänderte Norm, ABl.-Fundstelle, CELEX, EUR-Lex-URL und
SHA-256 des gelesenen Dokuments.

| Zeitraum | Bau | L/D zentral | L/D subzentral | Quelle |
|---|---:|---:|---:|---|
| 2014–2015 | 5.186.000 | 134.000 | 207.000 | VO (EU) Nr. 1336/2013, ABl. L 335 vom 14.12.2013, S. 17 (Art. 7 RL 2004/18/EG) |
| 2016–2017 | 5.225.000 | 135.000 | 209.000 | Delegierte VO (EU) 2015/2170, ABl. L 307 vom 25.11.2015, S. 5; zugleich VO (EU) 2015/2342, ABl. L 330 vom 16.12.2015, S. 18 (RL 2004/18/EG bis 17.04.2016) |
| 2018–2019 | 5.548.000 | 144.000 | 221.000 | Delegierte VO (EU) 2017/2365, ABl. L 337 vom 19.12.2017, S. 19 |
| 2020–2021 | 5.350.000 | 139.000 | 214.000 | Delegierte VO (EU) 2019/1828, ABl. L 279 vom 31.10.2019, S. 25 |
| 2022–2023 | 5.382.000 | 140.000 | 215.000 | Delegierte VO (EU) 2021/1952, ABl. L 398 vom 11.11.2021, S. 23 |
| 2024–2025 | 5.538.000 | 143.000 | 221.000 | Delegierte VO (EU) 2023/2495 (erneut geprüft, unverändert) |
| 2026–2027 | 5.404.000 | 140.000 | 216.000 | Delegierte VO (EU) 2025/2152 (erneut geprüft, unverändert) |

Richtlinienwechsel 2016: RL 2004/18/EG galt bis 17.04.2016 (Art. 91 RL
2014/24/EU); VO (EU) 2015/2342 setzt dort ab 01.01.2016 dieselben Werte wie
2015/2170 in RL 2014/24/EU. Deshalb ist 2016–2017 ein durchgehender Zeitraum,
keine offene Entscheidung.

Nicht eingetragen (weiter „unbestimmt“): vor 2014, ab 2028; Konzessionen
(RL 2014/23/EU), Sektoren (RL 2014/25/EU), soziale Dienstleistungen (Art. 4
lit. d) und Wettbewerbe, weil das Profilschema diese Kategorien nicht kennt.
Nationale Stufen (HVTG) unverändert `REVIEW_REQUIRED`.

## Nachweise (lokal ausgeführt)

| Nachweis | Ergebnis |
|---|---|
| `auditcore_procurement` pytest | 241 PASS (neu: `tests/test_historic_thresholds.py` mit Wert-/Fundstellenabgleich je Zeitraum, lückenlose Zeiträume 2014–2027, Grenzfälle je Zeitraum, Byte-/Fingerprint-Prüfung von 2026.09.2) |
| `auditcore_risk` pytest | 2.368 PASS (neu: C2-Tests; RF02 2019 mit 7.000 € netto → `False` statt `None`; 200.000 € 2019 → RF02 gegen 221.000 €; 2013/2028 bleiben `None`; Splitting 2019) |
| ruff, mypy (strict, `src`) | beide Pakete PASS |
| `check_extracted_authorization` (EXPECTED_SOURCES) | beide Pakete, beide provenance.json PASS (keine neuen Quell-Commits) |
| `scripts/verify_domain_packages.py --apt` (harvest, entity_matching, procurement, statistics, risk) | alle 49 Prüfungen PASS: Wheel/sdist-Build, isolierte pip-Installation mit Smoke-Tests aus dem installierten Paket, Entfernen, selektive Installation, Debian-Pakete, signierte APT-Quelle mit Install/Upgrade/Remove |
