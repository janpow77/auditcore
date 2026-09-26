# Doppelte Hilfsfunktionen der Fachpakete – Inventur und Entscheidungen

Stand: `main` @ `40ce8f7` (25.09.2026), 2 631 Funktionen in 20 Paketen unter
`packages/*/src`. Maschinenlesbares Ergebnis:
[`duplikate-inventur.json`](duplikate-inventur.json), reproduzierbar mit

```bash
python scripts/inventory_duplicate_functions.py --output duplikate-inventur.json
```

## Verfahren

1. **Normalisierung je Funktion (AST):** Docstring, Dekoratoren, Annotationen
   und Funktionsname entfallen; alle lokal gebundenen Bezeichner (Parameter,
   Zuweisungs-, Schleifen-, Comprehension- und Ausnahmenamen) werden in
   Reihenfolge ihres Auftretens zu `v0, v1, …` umbenannt. Freie Namen (Importe,
   Modulglobale, Builtins), Attributnamen und Konstanten bleiben, weil sie das
   Verhalten tragen.
2. **Exakte Duplikate:** gleicher SHA-256 der Normalform in mindestens zwei
   Paketen, Rumpf ab 12 AST-Knoten.
3. **Nahe Duplikate:** paketübergreifende Paare mit Token-Ähnlichkeit
   (`difflib`, ohne Autojunk) **≥ 0,85**, vorgefiltert über 5-Gramm-Jaccard ≥ 0,4.
   Paare werden zu Gruppen verbunden.
4. **Gleichnamige Funktionen** (Liste `same_name`) als Prüfhilfe, damit
   Namensgleichheit ohne Strukturgleichheit (z. B. `_plain`, `parse_amount`)
   nicht übersehen wird.
5. **Handprüfung jeder Gruppe:** Die Unterschiede unten sind aus dem Code
   abgelesen. Zusammengeführt wird nur, was ein Differenztest alt gegen neu
   bestätigt (`packages/auditcore_common/tests`, wörtliche Kopien in
   `tests/legacy_reference.py`).

Ergebnis: 69 Gruppen. **17 fachliche Duplikatgruppen** (davon 13 nach
`auditcore_common` zusammengeführt, 4 wartend/außerhalb), **7 Gruppen
belassen** mit Begründung, der Rest sind **strukturelle Scheintreffer**
(gleiche Form, andere Bedeutung, z. B. `to_dict`-Methoden, Dataclass-
`__init__`, Listen-Comprehensions über Profilfelder).

## A. Zusammengeführt in `auditcore_common` 0.1.0

„Identisch“ heißt: gleiche Normalform. „Variante“ heißt: echter
Verhaltensunterschied, der als benannter Parameter abgebildet ist.

| # | Gruppe | Fundstellen | Befund | Ziel in `auditcore_common` |
|---|---|---|---|---|
| A1 | Kanonisches JSON + SHA-256 (Profil-Fingerprint) | dataprotection `hashing.canonical_sha256`; `fingerprint` in entity_matching, funding_sources, legal_sources (`profile.py`), market_indicators, registry_sources, risk; price_analysis `profiles._fingerprint`; harvest `model.canonical_hash` | **9× identisch** (`sort_keys`, `ensure_ascii=False`, `(",", ":")`, UTF-8) | `hashing.canonical_sha256(value)` |
| A1a | Variante documents-Profile | documents `profiles.fingerprint`, `pipeline/profiles.fingerprint` | Standardtrenner `", "`/`": "`; zusätzlich paketeigenes Weglassen von Altvorgaben vor dem Hash (bleibt im Paket) | `canonical_sha256(data, compact=False)` |
| A1b | Variante documents-Pipeline | documents `pipeline/hashing.hash_json` | `ensure_ascii=True`, `default=str` | `canonical_sha256(obj, ensure_ascii=True, default=str)` |
| A1c | Variante price_sources | price_sources `snapshots.canonical_json_bytes` | Standardtrenner, `ensure_ascii=True`, Bytes statt Hash | `canonical_json(json.loads(body), compact=False, ensure_ascii=True).encode()` |
| A2 | Datei-SHA-256 | documents `compare.sha256_file` (1 MiB), `pipeline/donut.sha256_file` (1 MiB), `pipeline/hashing.hash_file` (8 KiB, nimmt `str`); invoicesynth `fonts.sha256_file` (64 KiB), `train/checkpoint._sha256`, `train/torch_backend.sha256_file` (1 MiB), `dataset._sha256` (`read_bytes`) | 3× identisch, 4 Varianten nur in Blockgröße bzw. Einlesen; Digest blockgrößenunabhängig (getestet an Blockgrenzen 8 KiB/64 KiB/1 MiB ± 1) | `hashing.sha256_file(path, chunk_size=1 << 20)` |
| A3 | Text-SHA-256 | documents `pipeline/hashing.hash_string` | einzige Kopie im Hashing-Dienst, gehört thematisch zu A1/A2 | `hashing.sha256_text` |
| A4 | Profile auflisten | `available_profiles` in dataprotection, entity_matching, funding_sources, legal_sources, market_indicators, registry_sources; risk `profiles._packaged`, `fraud._packaged` | 6× identisch bis auf den Ressourcenpaketnamen; risk als Variante `dict[(id, version)] → Datei` (bei doppelter Identität gewinnt die letzte Datei) | `profiles.packaged_profile_ids(pkg)`, `profiles.packaged_profile_entries(pkg)` |
| A5 | Profil laden | `load_profile` in dataprotection, entity_matching, funding_sources, legal_sources, market_indicators, procurement (`precheck_profile`), registry_sources | 7 Varianten in drei Achsen: (1) Typprüfung „Profilkennung und Version sind als Text anzugeben.“ ja (dataprotection, entity_matching, market, registry) / nein; (2) Dateiname mit `/` oder `\` → „nicht vorhanden“ (dataprotection, entity_matching, procurement) oder „Ungültige Profilkennung.“ (market, registry), zusätzlich führender Punkt (funding, legal); (3) Identitätsprüfung am geparsten Profil bzw. bei funding am Rohdokument mit angehängtem Fingerprint | `profiles.load_packaged_profile(pkg, id, version, parse=…, identity=…, error=…, require_text=…, invalid_name="missing"\|"invalid"\|"invalid_or_hidden")` |
| A6 | Empfohlenes Profil | entity_matching, registry_sources `recommended_profile` | identisch bis auf Ressourcenpaket | `profiles.recommended_profile_id(pkg, purpose, error)` |
| A7 | Einfrieren/Auftauen | `_freeze` in documents (`pipeline/audit`), registry_sources, risk; documents `thaw` (lokal) | 3× identisch | `frozen.freeze`, `frozen.thaw` |
| A8 | JSON-taugliche Kopie | risk `results.plain`; dataprotection `report_data.plain`; funding `_jsonsafe.json_safe`/`json_safe_mapping` | 3 Varianten: risk nur Mapping/Liste/Tupel/Datum; dataprotection zusätzlich `Enum.value`, Dataclass über `asdict`, `set`/`frozenset` sortiert; funding zusätzlich `Decimal` → Text, `NaN` → `None` | `json_values.jsonable(value, enums=, dataclasses=, sets=, decimals=, nan_as_none=)` |
| A9 | JSON-Antwort dekodieren | legal `_adapter_support._json`, registry `chambers._json` | Varianten nur in Fehlerklasse und Meldung („Antwort ist kein JSON.“ bzw. „keine gültige JSON-Antwort ({exc}).“) | `json_values.decode_json(data, error_factory)` |
| A10 | JSON-Typen | registry `_types.JsonValue`/`JsonObject` | rekursiver Typ mit lesenden Containern | `json_values.JsonValue`, `JsonObject` |
| A11 | Sicheres XML-Laden | registry `_xml_support._fromstring`, `_company_vat.parse_vies_response` (Import); reporting `_ooxml` (`forbid_dtd=True`) | registry 2× gleich bis auf Meldung; VIES trennt fehlendes Extra von Parserfehlern | `safe_xml.parse_xml`, `safe_xml.defused_fromstring` |
| A12 | HTML-Links und HTML-Erkennung | legal `feeds._Links`; property `adapters` 3× `"<html"/"<!doctype" in body[:4096].lower()`; legal `adapters` `"<a"/"<html" in text.lower()` | Linksammler einmal; Erkennung property identisch (3×), legal Variante mit anderen Markern und ohne Fenster | `html_text.LinkCollector`, `anchor_links`, `has_html_marker(text, markers=, window=)` |
| A13 | NumPy-kompatible Numerik | statistics `numeric.numpy_pairwise_sum`, market_indicators `_numeric.numpy_pairwise_sum` (identisch), sampling `_numeric.pairwise_sum`; `numpy_round` statistics = sampling; geo `koordinaten._endlich` / market `indicators._finite`; documents `donut_values.rate` = invoicesynth `formats.parse_rate` | Summe und Rundung bitgleich (auch gegen NumPy 2.4 geprüft); Endlichkeitsprüfung nur Meldungen verschieden | `numeric.numpy_pairwise_sum`, `numpy_round`, `require_finite(value, not_number=, not_finite=)`, `parse_percent_rate` |
| A14 | Zeit/IDs/Text/Extras | documents `utc_now` (2×), `new_id`; harvest `model.iso` / property `zvg_lifecycle._aware`; dataprotection `prefill._number` = registry `_legacy_osint._count`; documents `compact` = invoicesynth `normalize_identifier`; verzögerte Importe `_openpyxl` (dataprotection, funding), `_rapidfuzz` (entity_matching, registry), `_pandas` (risk), `_pl` (market), `_pil`/`_modules` (invoicesynth), `_etree` (documents) | identisch bzw. nur Fehlerklasse/Meldung verschieden | `clock.utc_now`, `clock.require_aware`, `ids.new_uuid`, `text.group_thousands_de`, `text.compact_upper`, `optional.require_module` |
| A15 | REST-Schicht, rahmenwerkfreier Teil (vormals B1) | sampling/statistics `ContractError` (identisch), `Reply` (sampling mit Kopfzeilen, statistics ohne), `_json`, `decode` (statistics mit `parse_float=Decimal`, Grenzen 32/64 MiB), Fehlerabbildung in `handle`/`handle_analyse`, `choice`/`_field`, Listenprüfung `parse_items`/`_values` | Meldungen und Statuscodes gleich; Unterschiede nur Fehlerklasse, `parse_float`, Feldname, Obergrenze und Nomen | `rest.ContractError` (Unterklasse je Paket), `Reply`, `json_reply`, `decode_body(raw, limit, error=, parse_float=)`, `guarded(action, error=)`, `choice(…, error=)`, `bounded_list(raw, name, maximum, noun, error=)`; Differenztests `tests/legacy_rest.py`, Hypothesis `tests/test_properties.py` |
| A16 | JSON-Objekt-Prüfung der REST-Verträge | identifiers `web.contract._object`, reporting `web.contract._object` (identisch); dazu beide `ContractError` (identisch mit `rest.ContractError`) | nur Fehlerklasse verschieden, Meldung „'<Pfad>' muss ein JSON-Objekt sein.“ gleich | `rest.json_object(value, path, error=)`, `ContractError` als Unterklasse von `rest.ContractError`; Differenztest `tests/test_rest.py`. Ähnlich, aber nicht umgestellt: sampling `as_object` (Vorgabe „Anfrage“), geo `_contract` |

## B. Wartet auf andere Arbeit (Kandidat, noch nicht zusammengeführt)

| # | Gruppe | Fundstellen | Befund | Warum wartend |
|---|---|---|---|---|
| B1 | REST-Schicht Stichprobe/Statistik | sampling/statistics `create_app` (identisch), `create_router`, `response`, `run`/`_analyse`, `get_profiles` | nach A15 verbleiben nur die Starlette-/FastAPI-Adapter (je eine Anweisung bzw. Routentabelle, unter der Gate-Schwelle) | bleibt im Paket: gebunden an Starlette/FastAPI, `auditcore_common` bleibt reine Standardbibliothek. Folgekandidat für dieselbe Umstellung: geo `web.decode`/`create_app` |
| B2 | Donut-Tokenformat | documents `donut._decode`, `parse_donut_sequence`; invoicesynth `schema._decode`, `from_sequence`; Prüfziffern `de_vat_check_digit`/`at_uid_check_digit` (0,72/0,79: invoicesynth prüft zusätzlich die Eingabe) | fachlich Donut/Rechnung, nicht allgemein | invoicesynth-PR #58 offen; Frage, ob invoicesynth von documents abhängen darf (E1: eigene Distribution) |
| B3 | Seitenergebnis bauen | legal `_adapter_support._page`, property `adapters._page` | `PageResult`-Aufbau, legal kopiert den Cursor (`dict(next_cursor)`), property nicht | gehört zu **harvest** (Paging-Vertrag), nicht nach `auditcore_common`; harvest-PR #73 („Hilfen für Quellenpakete“) abwarten |
| B4 | harvest `JSON = Any`, unsicheres XML | harvest `model.JSON`, `reference.py` (`xml.etree.ElementTree.fromstring`, `nosec B314`) | Befund: harvest parst XML ohne `defusedxml` | harvest-PR #73 offen; danach auf `JsonValue` und `safe_xml` umstellen |

## C. Belassen (mit Begründung)

| Gruppe | Fundstellen | Grund |
|---|---|---|
| `_plain`/`plain` | property `kleinanzeigen._plain` (HTML → Text mit ` \| `), risk/dataprotection `plain` (→ A8) | nur Namensgleichheit; die property-Funktion ist einmalig |
| `parse_amount` | documents `postprocess.parse_amount` → `(float\|None, Währung)`, funding `flowsearch.parse_amount` → `float`, funding `workshop_state_aid.parse_amount` → `Decimal\|None` | drei verschiedene Verträge (Ähnlichkeit 0,08–0,42) mit charakterisiertem Altverhalten |
| `reference`-Methoden | 11 Profilklassen | ein Dictionary-Ausdruck mit paketeigenen Schlüsseln (`id`/`profile_id`, mit/ohne `status`); ein Aufruf wäre nicht kürzer |
| Rechtsformtoken entfernen | entity_matching `_drop_tokens`, funding `_parsing.drop_legal_tokens` (0,86) | fachlich Entitätsnormalisierung; entity_matching kennt den Schalter `compact_tokens`, funding nicht; funding hängt nicht von entity_matching ab |
| Anker mit Verschachtelung | property `zvg._anchor_texts.Anchors` | andere Semantik als A12 (überspringt `script/style/template`, verschachtelte Anker, leeres `href` zählt) |
| Zahlprüfung | documents `float_is_nan_or_inf`, geo `nominatim._zahl` (0,88) | gegensätzliche Ergebnisse (Wahrheitswert „nicht endlich“ bzw. endliche Zahl oder `None`) |
| Datumsparser | legal `_since` (`value[:10]`), price_analysis `_day` (`str(value)`), dataprotection `edpb._iso_date` | Kürzung, Rückgabetyp und Fehlerklasse verschieden |
| `_require_docx` | documents `render_docx` | `from docx import Document` importiert ein Attribut; `require_module` liefert Module |
| dataprotection `to_json_bytes` | `report_data` | einmalig (`indent=1`, Zeilenende) |

## D. Strukturelle Scheintreffer

Gleiche AST-Form, aber verschiedene Bedeutung; keine Maßnahme:
Dataclass-`__init__`/`__post_init__` (documents, geo, reporting, invoicesynth,
registry, legal, price_analysis), `to_dict`/`identity`-Methoden (30 Stellen),
Listen-Comprehensions über Profilfelder (`_checks`, `actions`,
`question_keys`, `codes`, `hinweise`, `validate_config` …), Getter-Paare
(`get_draft`/`get_released`/`find_tier`), `require_ema`…`require_adx`,
`render_overview_xlsx`/`provider`/`grosskreis_km`, `harvest_timestamp`/`number`,
`legacy_preview`/`historical_volatility`, `yes_no`/`vat_note_kind`,
`ring_vereinfachen`/`compute_red_flags`, `sparql_form`/`_check_query`/
`require_parameters`, `_blank`/`is_missing`, `_strings`/`as_object`,
`_apply_fold_map`/`register` und ähnliche (vollständige Liste im JSON).

## E. App-Hilfen (Inventur `docs/reports/app-helfer-python.md`)

Übernommen in `auditcore_common` (Nachtrag zu 0.1.0, Differenztests gegen die
wörtlichen App-Kopien in `packages/auditcore_common/tests/legacy_apps.py`):

| Gruppe | App-Fundstellen | Ziel | Varianten |
|---|---|---|---|
| Anteil in Prozent (Top 19) | audit_designer `_anteil`, flowinvoice `_anteil`, riskanalysis `_anteil`, regulierung `_quote_pct` | `numeric.share_percent` | audit_designer: 1 Nachkommastelle und `teil*100/ganzes` (`digits=1, multiply_first=True`); übrige 2 Stellen, `teil/ganzes*100` – die Reihenfolge ändert Ergebnisse (z. B. 1953/240) |
| Tolerante Zahl-Koerzierung (Top 10) | audit_designer `_als_float`, `_als_zahl`, `_float`, beneficiaries `_als_float`; audit-portal `_to_float`; flowinvoice `_zahl`; regulierung `_safe_float`; versteigerung `_money_float`, `_to_float` | `numeric.as_float`, `numeric.as_float_comma` | `""` → `None` (`blank_as_none`), nur `ValueError` abfangen (regulierung, `catch_type_error=False`); beneficiaries: Zahlen mit NaN → `None`, Text mit Komma → eigene Funktion |
| Dateinamen (Top 13) | audit_designer document_comparisons/jupyter/presentation, audit-portal vvt_templates/help_export, regulierung vollzug | `filenames.*` (sechs benannte Varianten) | Zeichensatz, Länge und Fallback je Variante |
| Coroutine synchron (Top 15) | flowinvoice `run_async` (tasks, pipeline_tasks), audit_designer `_run_async_in_thread`, flowaudit `run_async` | `aio.ThreadLoopRunner`/`run_sync`, `aio.run_on_current_loop` | flowinvoice: Loop je Thread und Modul, fork-sicher – je Modul ein eigener Runner hält die Trennung |

Nicht übernommen (Begründung):

- `numbers_de`/`format_de` (Top 4/5, Klasse c): viele fachlich abweichende
  Varianten (Mehrdeutigkeit „11.047“, US-Format, Fehlwertdarstellung) –
  eigener Folge-PR mit Profilen, nicht nebenbei.
- `web` (`client_ip`, `get_or_404`, begrenztes Upload-Lesen): an
  FastAPI/Starlette und die App-Datenbank gebunden; gehört nicht in das
  stdlib-only-Paket, ggf. später als Extra.
- audit_designer `sanitize_filename` (vp_ai): nur eine App, mit eigener
  Mojibake-Reparatur.
- Übrige Klasse-b-Gruppen (Sitzungen, Admin-Abhängigkeiten, Demo-Nutzer,
  RouterHealth …): App-/Framework-Infrastruktur, keine Bibliotheksfunktion.

Die App-Migrationen selbst (App-Code auf `auditcore_common` umstellen) macht
der Hauptagent je App mit Deploy und Pflicht-Rauchtest.

## Migration

Reihenfolge und Stand stehen im PR-Verlauf; Grundsätze:

- Pakete hängen mit exaktem Pin von `auditcore_common` ab
  (`auditcore_common==0.1.0`, APT `python3-auditcore-common`).
- Interne Namen entfallen; öffentliche Hilfsnamen bleiben als Alias mit
  `DeprecationWarning`. Fachliche Einstiegspunkte (`load_profile`,
  `fingerprint`, `available_profiles`, `recommended_profile`) bleiben als
  dünne, nicht veraltete Funktionen, weil sie das Ressourcenpaket und die
  Fehlerklasse des Pakets binden.
- Pakete in laufender Refaktorierung werden erst nach deren Merge migriert.

Stand v0.4.2 (Teil B, 26.09.2026): `auditcore_price_sources` (A1c,
Paketbytes bytegleich, SHA-256 fester Fixtures festgeschrieben),
`auditcore_geo` (A13 `_endlich`), `auditcore_property_sources` (A12
HTML-Erkennung 3×, A14 `_aware`) und `auditcore_invoicesynth` (A2
Datei-SHA-256 4×, A13 `parse_rate`, A14 `normalize_identifier`, dazu
Text-SHA-256 und kanonisches JSON für Datensatz-, Plan- und Konfigurations-Hash)
nutzen `auditcore_common`. Die Prüfziffern `de_vat_check_digit`/
`at_uid_check_digit` von `auditcore_documents` (Code-Gate: 2 Paare mit
`auditcore_identifiers`) sind jetzt die Funktionen aus `auditcore_identifiers`
(Pflichtabhängigkeit `auditcore_identifiers==0.1.0`). Paritätstests je Paket
(`tests/test_common_parity.py`, documents `tests/test_identifiers_parity.py`);
`duplicate_functions` documents und identifiers 2 → 0. Offen aus B2 bleiben die
Prüfziffern von `auditcore_invoicesynth` (prüfen zusätzlich die Eingabe, keine
gleiche Normalform).

Stand Teil A (v0.4.2): `auditcore_statistics` (A13, A15),
`auditcore_sampling` (A13, A15) und `auditcore_market_indicators` (A1, A4, A5,
A13, A14 `_pl`) sind umgestellt; Nachweis zusätzlich durch einen
Differenzlauf der Pakete alt gegen neu (30 000 REST-Aufrufe mit zufälligen
Rümpfen, alle Endpunkte über Starlette und FastAPI byte- und kopfzeilengleich).

## Dauerhafte Absicherung

Das Code-Gate zählt paketübergreifende Duplikate als Metrik
`duplicate_functions` (siehe [code-quality.md](code-quality.md)).
