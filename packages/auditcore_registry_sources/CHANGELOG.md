# Changelog auditcore_registry_sources

## 0.2.2 – 2026-09-26 – Paketstand für Release v0.4.1

Keine Verhaltensänderung. Pins `auditcore_common==0.1.1`, `auditcore_harvest==0.1.2` und `auditcore_entity_matching==0.2.3`; README-Installationshinweis auf v0.4.0.

## 0.2.1 – Hilfsfunktionen aus auditcore_common

Keine fachliche Änderung. Neue Laufzeitabhängigkeit `auditcore_common==0.1.0`
(APT `python3-auditcore-common`); `auditcore_entity_matching==0.2.2`.

- Profile: `fingerprint` → `hashing.canonical_sha256`, `_freeze` →
  `frozen.freeze`, `available_profiles`/`load_profile`
  (`require_text=True, invalid_name="invalid"`)/`recommended_profile` →
  `auditcore_common.profiles`.
- `_types.JsonValue`/`JsonObject` kommen aus `auditcore_common.json_values`.
- XML nur über `auditcore_common.safe_xml` (`parse_xml` für die Listen,
  `defused_fromstring` für VIES, damit ein fehlendes Extra weiter von
  Parserfehlern getrennt bleibt); `chambers._json` → `decode_json`;
  rapidfuzz über `optional.require_module`; Tausendertrennung der
  osint-Konsolenausgabe → `text.group_thousands_de`.
- Meldungen, Fehlerklassen und Ergebnisse unverändert; alle Tests grün.

## 0.2.0 – REST-Schnittstelle Screening-Trefferprüfung

- Neues Unterpaket `auditcore_registry_sources.web` (Vertrag
  `auditcore_registry_sources.screening_review/1`): Prüfläufe für Sanktionen und
  PEP, Score-Aufschlüsselung aus `auditcore_entity_matching`, Quellenstand mit
  Aktualität, Entscheidungen mit Pflichtbegründung und Vier-Augen-Option,
  append-only Protokoll über das `ReviewStore`-Protocol.
- Adapter: Starlette (Extra `web`), FastAPI-Router (Extra `fastapi`).
- Bestehende Module und Ergebnisse unverändert. Vertrag:
  `docs/ui/screening-rest.md`.

## 0.1.1 – Refaktorierung ohne Verhaltensänderung

Keine fachliche Änderung: Profile, Regeln, Ergebnisse und alle öffentlichen
Importpfade bleiben gleich; die 524 bestehenden Tests (Charakterisierung,
Replay, Verträge) laufen unverändert.

- `legacy.py` (1229 Zeilen) ist eine Fassade; die Nachbildungen liegen je
  Quellanwendung in `_legacy_designer`, `_legacy_workshop`, `_legacy_portal`,
  `_legacy_flowsearch`, `_legacy_osint`, `_legacy_flowinvoice_screening`,
  `_legacy_flowinvoice_company` (gemeinsam: `_legacy_shared`, Ergebnisformen
  als `TypedDict` in `_legacy_types`).
- `sanctions_xml.py`: je Listenformat ein Parser (`_xml_eu`, `_xml_ofac`,
  `_xml_un`) auf gemeinsamen Lesehilfen (`_xml_support`); die zusätzlich
  gelesenen Werte laufen als `RecordExtra` neben den Originalwörterbüchern statt
  unter dem Schlüssel `__extra` (die Konstante `EXTRA` bleibt erhalten).
- `screening.py`: Profileinstellungen und Punktanpassung (`_screening_rules`),
  Listenindex (`_screening_index`, `search_detailed` in kurze Schritte
  zerlegt), Ergebnisvertrag und `screen` bleiben in `screening`.
- `opensanctions_api.py`: Anfrage/Schlüssel (`_opensanctions_query`),
  Antwort/Client (`_opensanctions_match`), Bewertung (`_opensanctions_assessment`).
- `company.py`: VIES (`_company_vat`) und Register (`_company_register`)
  ausgelagert; `verify_company` wertet VIES und Register in eigenen Schritten aus.
- Typen: `to_dict`-Sichten liefern `JsonObject` (`_types.JsonValue`) statt
  `dict[str, Any]`; Positionen, Kammeradressen (`ChamberRecord`) und die
  Rückgaben der Legacy-Nachbildungen sind `TypedDict`s. `Any` bleibt nur an
  echten Rohdatengrenzen (Profil-JSON, API-/CSV-Rohdaten, Adapterprotokoll von
  `auditcore_harvest`, vom Aufrufer durchgereichte KMU-Werte, jetzt als
  Alias `ownership.CompanyData`).
- Funktionen über 60 Zeilen zerlegt: `flowinvoice_pep_check`
  (`_best_pep_form`, `_pep_match`), `parse_targets_simple_csv` (`_decode`,
  `_checked_columns`, `_read_rows`), AGVO-Prüfung (`_aggregated`,
  `_agvo_category`).

| Messung (src) | 0.1.0 | 0.1.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 4 | 0 |
| Funktionen > 60 Zeilen (Code-Gate) | 8 | 0 |
| Module > 400 Zeilen | 4 | 0 |
| `Any`-Vorkommen (Text) | 143 | 58 |
| `Any`-Verwendungen (Code-Gate) | 132 | 45 |
| mypy --strict | sauber | sauber |
| Testabdeckung | 96,1 % | 96,9 % |

Keine Umbenennung öffentlicher Namen, daher keine Aliase.
