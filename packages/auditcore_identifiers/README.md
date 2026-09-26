# auditcore_identifiers

## Zweck

Prüfen und Normalisieren von Kennungen – IBAN, BIC, USt-IdNr. (alle EU-Staaten), Steuer-ID, Steuernummer, LEI und Handelsregisternummer – mit einheitlichem Ergebnisobjekt und benannten Profilen.

Für Anwendungen und Fachpakete, die Kennungen aus Rechnungen, Registern oder
Anträgen prüfen (flowinvoice, audit-portal, flowworkshop, die
auditcore-internen Kopien). Jede Prüfung liefert ein `CheckResult` und wirft
für ungültige Eingaben keine Exception. Nicht enthalten: Abfragen externer
Register (VIES, GLEIF, BZSt) und nationale Kontoprüfziffern.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install auditcore_identifiers \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.1.0 im
Release v0.4.1; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-identifiers/`):

```text
auditcore_identifiers @ https://github.com/janpow77/auditcore/releases/download/v0.4.1/auditcore_identifiers-0.1.0-py3-none-any.whl#sha256=fb4f0217fd80f7290f799dc1ac12e0717eb770a99d34644082e0b71e084693bb
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-identifiers
```

Extras: `[web]` (Starlette) und `[fastapi]` für den REST-Vertrag
`identifiers_ui/1` der Oberfläche „Kennung prüfen“, `[dev]` (Test- und
Prüfwerkzeuge). Ohne Extras nur Standardbibliothek und `auditcore_common`.

## Schnellstart

```python
import auditcore_identifiers as ai

r = ai.check_iban("IBAN DE89 3704 0044 0532 0130 00")
assert (r.valid, r.normalized, r.country) == (True, "DE89370400440532013000", "DE")
assert ai.check_iban("DE89370400440532013001").reason is ai.Reason.INVALID_CHECKSUM
assert ai.check_vat_id("136695976", country="DE").normalized == "DE136695976"
assert ai.check_tax_id("36 574 261 809").valid
```

```pycon
>>> ai.check_iban("DE89370400440532013001").message
'IBAN-Prüfziffer ist falsch'
>>> dict(ai.check_lei("7LTWFZYICNSX8D621K86").details)
{'lou_prefix': '7LTW'}
>>> ai.check_iban("DE89370400440532013001", profile="flowinvoice.legacy").valid
True
```

Das Legacy-Profil von flowinvoice prüft die IBAN-Prüfziffer nicht (Modulo 97
fehlt im Original) – deshalb ist dieselbe IBAN dort gültig.

## API-Überblick

### Ergebnis

`CheckResult(kind, status, raw, normalized, reason, message, country, profile, details)`

- `status`: `VALID`, `INVALID`, `MISSING` (wie `ValidationStatus` in flowinvoice).
- `reason`: `missing`, `invalid_type`, `invalid_characters`, `invalid_length`,
  `invalid_format`, `unknown_country`, `country_mismatch`, `invalid_checksum`.
- `message`: deutsch (Profil `strict`) bzw. Originalwortlaut (Legacy-Profile).
- `details`: z. B. `bban`, `expected_length`, `test_bic`, `checksum`
  (`verified`/`not_checked`), `land`, `format`. `to_dict()` liefert JSON.

### Prüfungen (Profil `strict`)

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

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_identifiers.__all__` (28):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `PROFILES` | Konstante | – | `profiles` |
| `STRICT` | Konstante | – | `profiles` |
| `CheckResult` | Datenklasse | Outcome of one identifier check. | `result` |
| `IdentifierKind` | Aufzählung | Kinds of identifiers the library checks. | `result` |
| `Profile` | Datenklasse | A named set of check functions with its origin and reason for existence. | `profiles` |
| `Reason` | Aufzählung | Why a value is not valid; ``None`` on :attr:`Status.VALID`. | `result` |
| `Status` | Aufzählung | Outcome of a check (same three values as the flowinvoice ``ValidationStatus``). | `result` |
| `UnknownProfileError` | Ausnahme | The profile name is not registered (a programming error, not a bad value). | `profiles` |
| `UnsupportedKindError` | Ausnahme | The profile has no check for this identifier kind. | `profiles` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `at_uid_check_digit` | Funktion | Check digit of the Austrian UID (``ATU`` + 8 digits, BMF procedure). | `vat` |
| `check` | Funktion | Check ``value`` as identifier ``kind`` under ``profile``. | `(Paketstamm)` |
| `check_bic` | Funktion | BIC (ISO 9362): 8/11 characters, ISO 3166 country code (strict). | `(Paketstamm)` |
| `check_iban` | Funktion | IBAN (ISO 13616): register length, BBAN structure, MOD 97-10 (strict). | `(Paketstamm)` |
| `check_lei` | Funktion | LEI (ISO 17442): 20 characters, MOD 97-10 (strict). | `(Paketstamm)` |
| `check_register_number` | Funktion | Handelsregisternummer (format only). | `(Paketstamm)` |
| `check_tax_id` | Funktion | Steuerliche Identifikationsnummer (11 digits, MOD 11,10). | `(Paketstamm)` |
| `check_tax_number` | Funktion | Steuernummer (coarse: Land format 10/11 digits, federal format 13 digits). | `(Paketstamm)` |
| `check_vat_id` | Funktion | USt-IdNr./VAT ID: EU formats, check digits DE and AT (strict). | `(Paketstamm)` |
| `de_vat_check_digit` | Funktion | Check digit of the German USt-IdNr. (ISO 7064 MOD 11,10). | `vat` |
| `extract_lei` | Funktion | First LEI with correct check digits in a free-text field (e.g. ``"LEI: …"``). | `lei` |
| `format_iban` | Funktion | Paper form in groups of four (``grouped``) or the electronic form. | `iban` |
| `format_tax_id` | Funktion | Presentation form ``12 345 678 901``. | `tax_de` |
| `get_profile` | Funktion | Profile by name; raises :class:`UnknownProfileError` for unknown names. | `profiles` |
| `iban_check_digits` | Funktion | Two ISO 13616 check digits for ``country`` + ``bban`` (for test data). | `iban` |
| `lei_check_digits` | Funktion | Two check digits for an 18-character LEI prefix (for test data). | `lei` |
| `normalize_vat_id` | Funktion | Upper case without whitespace and separators ``. - / \`` (no validation). | `vat` |
| `profile_names` | Funktion | All registered profile names, ``strict`` first. | `profiles` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_identifiers.checksums` | Check digit algorithms (ISO 7064) and input preparation shared by all checks. |
| `auditcore_identifiers.iban` | IBAN (ISO 13616) and BIC (ISO 9362) – strict checks. |
| `auditcore_identifiers.legacy_flowinvoice` | Legacy profile ``flowinvoice.legacy`` (= ``audit_portal.legacy``). |
| `auditcore_identifiers.legacy_pipeline` | Legacy profiles of the document pipeline and the auditcore-internal copies. |
| `auditcore_identifiers.lei` | Legal Entity Identifier (ISO 17442): 18 alphanumerics, two check digits, MOD 97-10. |
| `auditcore_identifiers.profiles` | Named profiles: ``strict`` (default) and legacy profiles reproducing each application. |
| `auditcore_identifiers.registry` | Reference tables: IBAN registry structures and ISO 3166-1 country codes. |
| `auditcore_identifiers.result` | Result objects: every check returns a :class:`CheckResult`, never raises for bad input. |
| `auditcore_identifiers.tax_de` | German tax identifiers: Steuer-IdNr. (§ 139b AO), Steuernummer, Handelsregisternummer. |
| `auditcore_identifiers.vat` | VAT identification numbers (USt-IdNr.): formats of all EU member states. |
| `auditcore_identifiers.web` | REST contract ``identifiers_ui/1`` for "Kennung prüfen" (extras ``web``, ``fastapi``). |
<!-- api-overview:end -->

### REST-Vertrag für Oberflächen (`auditcore_identifiers.web`)

`catalogue()`, `check_one(body)` und `check_batch(body)` bilden den Vertrag
`identifiers_ui/1` framework-frei ab; `create_app`/`routes` (Extra `web`)
und `create_router` (Extra `fastapi`) hängen ihn unter `GET /catalogue`,
`POST /check` und `POST /check/batch` ein. Das Profil ist in jeder Anfrage
Pflicht; ungültige Kennungen sind Ergebnisse, keine Fehler. Die Oberfläche
ist `<flowaudit-identifier-check>` aus `@auditcore/ui` (React:
`FlowauditIdentifierCheck`). Vertrag:
[`docs/ui/identifiers-rest.md`](../../docs/ui/identifiers-rest.md).

```python
from auditcore_identifiers.web import check_one

answer = check_one({"kind": "iban", "value": "DE89370400440532013001", "profile": "strict"})
assert answer["result"]["reason_label"] == "Prüfziffer falsch"
```

## Profile und Konfiguration

`check(kind, value, profile=..., country=...)` oder `profile=` an jeder
Funktion. `strict` ist Standard; sieben Legacy-Profile
(`flowinvoice.legacy`, `audit_portal.legacy`, `flowinvoice.pipeline.legacy`,
`audit_portal.pipeline.legacy`, `documents.donut`, `invoicesynth.legacy`,
`flowworkshop.legacy`) geben die Anwendungen ergebnisgleich wieder und sind in
[`docs/profiles.md`](docs/profiles.md) mit Begründung beschrieben. Unbekanntes
Profil → `UnknownProfileError`, Art im Profil nicht vorhanden →
`UnsupportedKindError` (Programmierfehler, keine Eingabefehler). Keine
Umgebungsvariablen, keine Konfigurationsdateien.

## Herkunft und Charakterisierung

Neuimplementierung gegen charakterisierte Verträge: Muster und Meldungen
stammen aus flowinvoice und audit-portal (`services/validators.py`,
`pipeline/stages/validation.py`, `services/risk_checker.py`), flowworkshop
(`entity_resolution.py`) und den auditcore-internen Kopien
(invoicesynth, documents, entity_matching); der Code wurde neu geschrieben.
Commits und Blob-SHAs stehen in `provenance.json`.

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

## Bewusste Verhaltensabweichungen

Die Legacy-Profile sind **legacy-exakt** (33 055 wiedergegebene
Originalaufrufe). Abweichungen gibt es nur im Profil `strict`; sie stehen
vollständig in [`docs/differences.md`](docs/differences.md) (Differenztabelle
Original ↔ `strict`, im Test auf Aktualität geprüft). Der Wechsel einer
Anwendung auf `strict` ist eine eigene fachliche Entscheidung.

## Abhängigkeiten

Python ≥ 3.11 und `auditcore_common==0.1.1` (selbst nur Standardbibliothek;
rahmenwerkfreier Teil der REST-Schicht für `web`, APT
`python3-auditcore-common`), sonst nur die Standardbibliothek. python-stdnum dient
nur der Gegenprüfung (offline, als Daten im Repository) und ist keine
Abhängigkeit.

## Sicherheit und Datenschutz

Rein lokale Berechnung ohne Netzwerk, Dateien oder Zustand. Steuer-ID,
Steuernummer und IBAN können personenbezogen sein: Das Paket speichert und
protokolliert nichts, das `CheckResult` enthält aber den Rohwert (`raw`) und
die Normalform – beim Loggen oder Serialisieren (`to_dict()`) entscheidet der
Consumer über Maskierung. Eine gültige Prüfziffer belegt nicht, dass Konto,
Unternehmen oder Steuerpflichtiger existieren.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Der Rechteinhaber hat am 22.09.2026 entschieden, dass die
Bibliotheken unter MIT stehen, die Anwendungen nicht (`USER_AUTHORIZED_MIT`
nur für diese Bibliothek). Quellen und Erklärung: `NOTICE` und
`provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
