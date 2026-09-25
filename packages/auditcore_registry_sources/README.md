# auditcore_registry_sources

## Zweck

Register-, Sanktions- und PEP-Quellen mit quellengebundenen Profilen: Listenformate lesen, Listen über `auditcore_harvest` abrufen, Namen abgleichen, Firmendaten prüfen und Screening-Treffer nachvollziehbar entscheiden.

Für Prüf- und Rechercheanwendungen (audit_designer, flowworkshop, flowsearch,
flowinvoice, audit-portal), die Sanktionslisten, PEP-Bestände, VIES,
OffeneRegister oder Kammerverzeichnisse nutzen. Datenbank, Scheduler,
Auslistungsentscheidung und Zugangsdatenverwaltung bleiben beim Consumer. Ein
Treffer ist ein Prüfhinweis, keine Feststellung.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install auditcore_registry_sources \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.2.1 im
Release v0.4.0; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-registry-sources/`):

```text
auditcore_registry_sources @ https://github.com/janpow77/auditcore/releases/download/v0.4.0/auditcore_registry_sources-0.2.1-py3-none-any.whl#sha256=dd958343bf84ad6c58be68a1f1f41823ec047d4bf986ad64d74b176b97b2ec89
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-registry-sources
```

Extras: `[fuzzy]` – rapidfuzz für `screen` (Profile audit_designer/flowworkshop);
`[xml]` – defusedxml für die amtlichen XML-Listen (EU FSF, OFAC SDN, UN SC);
`[html]` – beautifulsoup4 für IHK- und HWK-Verzeichnisse; `[web]` – Starlette-
Adapter der Screening-Trefferprüfung (mit rapidfuzz); `[fastapi]` –
FastAPI-Router derselben Schnittstelle; `[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

Liste im OpenSanctions-Format `targets.simple.csv` lesen und mit dem
flowinvoice-Profil (`difflib`, nur Standardbibliothek) abgleichen:

```python
from auditcore_registry_sources import FormatError, load_profile, parse_targets_simple_csv
from auditcore_registry_sources.bulk_screening import local_screen

csv_bytes = (
    "id,schema,name,aliases,birth_date,countries\n"
    "NK-1,Company,Beispiel Handels GmbH,Beispiel Trading;BH GmbH,,de\n"
    "NK-2,Person,Erika Musterfrau,,1970-01-01,de\n"
).encode()
parsed = parse_targets_simple_csv(csv_bytes, list_key="eu_fsf")
assert parsed.rows_seen == 2 and not parsed.issues

profile = load_profile("flowinvoice.sanctions_local", "2026.09.1")
result = local_screen("Beispiel Trading", parsed.entries, profile, as_of="2026-09-22")
assert result.status == "HITS"
assert local_screen("Unbeteiligt AG", parsed.entries, profile).status == "NO_HITS"
# Ohne Datenbestand wird nichts geprüft – kein Scheinbefund.
assert local_screen("Unbeteiligt AG", [], profile).status == "NOT_SEARCHED"

# Eine Lieferung ohne verwertbare Zeile ist ein Fehler, keine leere Liste.
try:
    parse_targets_simple_csv(b"id,name\n,\n", list_key="eu_fsf")
except FormatError:
    pass
else:
    raise AssertionError("FormatError erwartet")
```

```pycon
>>> [(h.entry.entry_id, h.matched_name, h.via_alias, h.score) for h in result.hits]
[('NK-1', 'Beispiel Trading', True, 1.0)]
```

Mit Extra `[fuzzy]` gleicht `screen` nach dem empfohlenen Designer-Profil ab
(Befund je Liste, Geburtsjahr/Land, Indikatoren):

```python no-run
from auditcore_registry_sources import ListSnapshot, load_lists, recommended_profile, screen
from auditcore_registry_sources.lists import find_list

lists = load_lists("audit_designer.sanctions_lists", "2026.09.1")
snapshots = [ListSnapshot(find_list(lists, "eu_fsf"), parsed.entries, as_of="2026-09-22")]
result = screen("Beispiel Handels GmbH", snapshots, recommended_profile("sanctions_screening"))
result.status  # HITS / NO_HITS / INCOMPLETE / NOT_SEARCHED
```

## API-Überblick

| Modul | Inhalt |
|---|---|
| `opensanctions_csv` | `targets.simple.csv` lesen/schreiben (Kopf live bestätigt), Zeilenprobleme sichtbar |
| `sanctions_xml` | EU FSF 1.1, OFAC SDN, UN SC (Extra `xml`); Legacy- und Textdatum |
| `screening` | rapidfuzz-Abgleich (Extra `fuzzy`) nach Profil; Geburtsjahr/Land, Klassen, Befund je Liste |
| `bulk_screening` | flowinvoice-Varianten: `difflib`-Listenprüfung und PEP-Massenabgleich |
| `opensanctions_api` | `/match`-Client (`Authorization: ApiKey`), Sanktions- und PEP-Auswertung |
| `ownership` | UBO-Traversierung/-Schwelle und KMU-Einstufung als Profile |
| `company` | VIES-Prüfung, OffeneRegister-Abfrage (gebundene Parameter), Indikatoren/Score |
| `chambers` | Zuwendungsempfängerregister, IHK, Handwerkskammern (Extra `html`) |
| `adapters` | `auditcore_harvest`-Adapter: OpenSanctions-Listen, amtliche XML-Listen, ZER, IHK, HWK |
| `legacy` | verhaltensgleiche Wiedergabe der Originale (456 Fälle) |
| `web` | Screening-Trefferprüfung `ScreeningReviewService` (Vertrag `auditcore_registry_sources.screening_review/1`): Prüfläufe, Score-Aufschlüsselung, Entscheidungen mit Pflichtbegründung und Vier-Augen-Option, Protokoll; REST-Adapter für Starlette (`[web]`) und FastAPI (`[fastapi]`), Vertrag in [docs/ui/screening-rest.md](../../docs/ui/screening-rest.md) |

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_registry_sources.__all__` (54):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `CONTRACT_VERSION` | Konstante | – | `(Paketstamm)` |
| `BulkHit` | Datenklasse | A hit of a bulk variant (score 0–1). | `bulk_screening` |
| `BulkResult` | Datenklasse | Result of a bulk variant with explicit status and data state. | `bulk_screening` |
| `CompanyVerification` | Datenklasse | Indicators, score and the checks that could not be carried out. | `company` |
| `KeyCredentials` | Datenklasse | Credential provider holding one operator key for the matching API. | `_opensanctions_query` |
| `DependencyError` | Ausnahme | An optional extra (``fuzzy``, ``xml``, ``html``) is not installed. | `errors` |
| `FormatError` | Ausnahme | A delivery cannot be interpreted; never presented as an empty list. | `errors` |
| `ListEntry` | Datenklasse | One listed person or organisation, spelled as the list spells it. | `model` |
| `ListFinding` | Datenklasse | What one requested list contributed; ``searched`` is the decisive value. | `screening` |
| `ListSnapshot` | Datenklasse | The inventory of one list a screening runs against, with its state. | `model` |
| `MatchClient` | Klasse | Calls ``/match/{dataset}`` through an injected transport; the key comes from credentials. | `_opensanctions_match` |
| `MatchQuery` | Datenklasse | One entity example of a match request. | `_opensanctions_query` |
| `ParsedList` | Datenklasse | Result of parsing one delivery of one list. | `model` |
| `ProfileError` | Ausnahme | A profile is missing, incomplete or of the wrong kind. | `errors` |
| `QueryError` | Ausnahme | An input violates the rules of the chosen profile (for example a too short name). | `errors` |
| `RegisterLookup` | Datenklasse | ``FOUND``, ``NOT_FOUND`` or ``UNAVAILABLE`` — the last is never "not in register". | `_company_register` |
| `RegistryProfile` | Datenklasse | Immutable profile with identity, origin, status and fingerprint. | `profiles` |
| `RegistrySourcesError` | Ausnahme | Base error with a stable machine-readable ``code``. | `errors` |
| `RowIssue` | Datenklasse | A row of a delivery that could not become an entry; never dropped silently. | `model` |
| `SanctionsList` | Datenklasse | One list of a list catalogue profile with its provider and data licence. | `model` |
| `ScreeningHit` | Datenklasse | A hit: indication for review with the evidence needed to retrace it. | `_screening_index` |
| `ScreeningResult` | Datenklasse | Screening result contract (``auditcore_registry_sources.screening/1``). | `screening` |
| `VatCheck` | Datenklasse | VIES answer; ``status`` is ``VALID``, ``INVALID`` or ``UNAVAILABLE``. | `_company_vat` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `assess_pep` | Funktion | PEP type and risk of every candidate at or above the local threshold. | `_opensanctions_assessment` |
| `assess_sanctions` | Funktion | Candidates at or above the local threshold with a topic containing ``sanction``. | `_opensanctions_assessment` |
| `available_profiles` | Funktion | Packaged ``(id, version)`` pairs; no profile is an implicit default. | `profiles` |
| `beneficial_owners` | Funktion | Natural persons above the share threshold or with voting control, by share descending. | `ownership` |
| `check_vat` | Funktion | One VIES request through the injected transport; failures become ``UNAVAILABLE``. | `_company_vat` |
| `find_list` | Funktion | List by key; an unknown key is an error, never ``None``. | `lists` |
| `list_catalog` | Funktion | The lists of a list catalogue profile, in the order of the source. | `lists` |
| `load_lists` | Funktion | Convenience: load a list catalogue profile and return its lists. | `lists` |
| `load_profile` | Funktion | Load an explicitly named packaged profile version. | `profiles` |
| `local_screen` | Funktion | ``check_entity_local``: best ratio over name and aliases per entry, at/above the minimum. | `bulk_screening` |
| `lookup_register` | Funktion | One datasette request; transport failures become ``UNAVAILABLE``. | `_company_register` |
| `ownership_chain` | Funktion | Walk parent links to the root; stops at the first repeated node. | `ownership` |
| `parse_register_rows` | Funktion | Datasette ``_shape=objects`` answer → first company (as the source). | `_company_register` |
| `parse_response` | Funktion | Interpret a ``/match`` answer; missing required parts are parser errors. | `_opensanctions_match` |
| `parse_targets_simple_csv` | Funktion | Parse one delivery of one list; see the module contract. | `opensanctions_csv` |
| `parse_vies_response` | Funktion | Interpret a ``checkVat`` answer regardless of namespace prefixes. | `_company_vat` |
| `parse_xml_list` | Funktion | Parser dictionaries of the originals (key sets differ per list). | `sanctions_xml` |
| `pep_bulk_screen` | Funktion | PEP bulk screening of flowinvoice against parsed ``peps`` list entries. | `bulk_screening` |
| `person_query` | Funktion | flowsearch PEP request: ``Person`` with optional birth date and nationality. | `_opensanctions_query` |
| `sanctions_query` | Funktion | flowsearch sanctions request: ``LegalEntity`` with name and country. | `_opensanctions_query` |
| `screen` | Funktion | Screen a name against list snapshots under an explicitly chosen profile. | `screening` |
| `serialize_targets_simple_csv` | Funktion | Deterministic CSV (``\n``, UTF-8 without BOM, fixed columns); rows without id/name skipped. | `opensanctions_csv` |
| `sme_status` | Funktion | ``calculate_kmu_status``: thresholds of the profile, no aggregation (see decisions). | `ownership` |
| `traverse` | Funktion | Depth-first traversal with effective shares (``share / 100 * parent share``). | `ownership` |
| `verify_company` | Funktion | Combine a VIES check and a register lookup into indicators and a score. | `company` |
| `configuration_status` | Funktion | ``CONFIGURED`` or ``NOT_CONFIGURED`` without revealing the key. | `_opensanctions_query` |
| `credentials_from_environment` | Funktion | Key from ``environ[ENV_VAR]`` (pass ``os.environ``); empty values count as missing. | `_opensanctions_query` |
| `recommended_profile` | Funktion | The profile recommended for ``purpose`` after the user decisions of 23.09.2026. | `profiles` |
| `unclassified_holders` | Funktion | Holders of unknown type above a threshold: to be clarified, never silently a person. | `ownership` |
| `xml_entries` | Funktion | Library contract: list entries with all birth dates/countries, skipped names as issues. | `sanctions_xml` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_registry_sources.adapters` | Source adapters for ``auditcore_harvest`` (contract ``auditcore_harvest.contract/1``). |
| `auditcore_registry_sources.bulk_screening` | flowinvoice screening variants: local ``difflib`` list check and PEP bulk token matching. |
| `auditcore_registry_sources.chambers` | Register and chamber address sources of the OSINT map (``traeger_quellen.py``). |
| `auditcore_registry_sources.company` | Company verification: EU VIES VAT check, OffeneRegister lookup and indicator scoring. |
| `auditcore_registry_sources.errors` | Structured errors of the registry sources; transport errors come from ``auditcore_harvest``. |
| `auditcore_registry_sources.legacy` | Behavior-compatible functions of the source applications (replay of the characterization). |
| `auditcore_registry_sources.lists` | List catalogues: which lists a source variant screens, where they come from. |
| `auditcore_registry_sources.model` | Data contracts: list entries, parsed deliveries and list snapshots. |
| `auditcore_registry_sources.opensanctions_api` | OpenSanctions matching API (``/match/{dataset}``) for sanctions and PEP checks. |
| `auditcore_registry_sources.opensanctions_csv` | OpenSanctions ``targets.simple.csv``: the list format the source applications screen. |
| `auditcore_registry_sources.ownership` | Ownership traversal, beneficial-owner (UBO) and SME judgements as explicit profiles. |
| `auditcore_registry_sources.profile_data` | – |
| `auditcore_registry_sources.profiles` | Versioned, source-bound profiles of the registry sources. |
| `auditcore_registry_sources.sanctions_xml` | Official sanctions list XML: EU FSF (1.1), OFAC SDN and UN Security Council. |
| `auditcore_registry_sources.screening` | Name screening against sanctions list snapshots (optional extra ``fuzzy``). |
| `auditcore_registry_sources.web` | Screening review API (Screening-Trefferprüfung), contract ``screening_review/1``. |
<!-- api-overview:end -->

## Profile und Konfiguration

`available_profiles()` listet alle Profile, `load_profile(id, version)` lädt
eines. Listenkataloge: `audit_designer`, `flowworkshop`, `official`.
Screening: `audit_designer.sanctions_screening`,
`flowworkshop.sanctions_screening`, `flowinvoice.sanctions_local`,
`flowinvoice.pep_bulk`. API: `flowsearch.opensanctions_match`,
`flowsearch.pep_risk`, `flowinvoice.sanctions_network` (nur `LEGACY_ONLY`).
Weitere: `flowsearch.ubo`, `flowsearch.kmu`, `flowinvoice.company_verification`.

Die charakterisierten Quellprofile (2026.09.1) tragen bei widersprüchlichen
Varianten `HUMAN_DECISION_REQUIRED`. **Empfohlen** sind nach den
Nutzerentscheidungen vom 23.09.2026 die Nachfolger 2026.09.2 über
`recommended_profile(zweck)` mit `sanctions_screening`, `pep_bulk`,
`pep_risk`, `ubo` (mehr als 25 % Kapital oder Stimmrechte, mittelbar
multipliziert), `sme` (Anhang I AGVO) und `company_verification`.

OpenSanctions-API: den Schlüssel beschafft jeder Betreiber selbst
(https://www.opensanctions.org/api/) und übergibt ihn als
`MatchClient(api_key=…)` oder per `credentials_from_environment(os.environ)`
aus `OPENSANCTIONS_API_KEY`; ohne Schlüssel meldet `MatchClient.status`
`NOT_CONFIGURED`.

## Herkunft und Charakterisierung

Extrahiert aus sieben privaten Anwendungen (gepinnte Commits, Blobs am
23.09.2026 gegen GitHub geprüft): audit_designer, flowworkshop, audit-portal,
flowsearch, flowinvoice, osint; riskanalysis nur dokumentiert, kein Code
übernommen. `tools/capture_legacy.py` hat **456 Fälle** an den Originalen
ausgeführt (`tests/fixtures/legacy_observed.json`, rapidfuzz 3.10.1,
Python 3.12.3). Das Modul `legacy` gibt alle Fälle exakt wieder (ausgenommen
Zeitstempel und durchgereichte httpx-Fehlertexte); die Quellprofile 2026.09.1
sind bitgenau. Die Namensnormalisierung kommt aus `auditcore_entity_matching`
(keine eigene Kopie). Live-Prüfstand der Quellen:
[docs/live-smoke.json](docs/live-smoke.json); Anbindung der Consumer:
[docs/consumer-migration.md](docs/consumer-migration.md).

## Bewusste Verhaltensabweichungen

Der Bibliotheksvertrag korrigiert 18 beobachtete Mängel der Originale
(REG-C01 bis REG-C18), unter anderem: jede angefragte Liste erhält einen
Befund, fehlende Listen ergeben `INCOMPLETE`/`NOT_SEARCHED` statt eines
stillen Nullbefunds; Lieferungen nur UTF-8, eine defekte Lieferung ist ein
Fehler statt leerer Bestand; XML über defusedxml; VIES-Antworten unabhängig
vom Namensraumpräfix, Nichtverfügbarkeit ist nie „ungültig“; OffeneRegister
nur mit gebundenen Parametern statt SQL-Text; UBO-Ketten mit Selbstverweis
terminieren; `snapshot_complete` nur ohne Zeilenprobleme – Auslisten bleibt
Consumer-Entscheidung. Vollständig mit Begründung und den Entscheidungen
R1–R10, A2, A3: [docs/behavior-changes.md](docs/behavior-changes.md).

## Abhängigkeiten

Python ≥ 3.11. Pflicht: `auditcore_harvest==0.1.1` (Abrufvertrag der Adapter),
`auditcore_entity_matching==0.2.2` (Namensnormalisierung, Score-
Aufschlüsselung) und `auditcore_common==0.1.1` (Profile, JSON-Typen,
sicheres XML; nur Standardbibliothek). Extras: rapidfuzz ≥ 3.10.1 < 4 (`fuzzy`, `web`),
defusedxml ≥ 0.7.1 (`xml`), beautifulsoup4 ≥ 4.11.2 < 5 (`html`),
starlette ≥ 0.26.1 < 2 (`web`), fastapi ≥ 0.95.2 (`fastapi`). Keine
Abhängigkeit von der Plattform `auditcore`, Datenbanken oder HTTP-Clients –
Netzwerktransporte injiziert der Consumer über `auditcore_harvest`.

## Sicherheit und Datenschutz

- **Personenbezogene Daten:** Sanktions- und PEP-Listen sowie abgefragte Namen
  sind personenbezogen; Speicherung, Löschfristen und Rechtsgrundlage liegen
  beim Consumer. Die Trefferprüfung (`web`) protokolliert Entscheidungen
  append-only über den vom Consumer gestellten `ReviewStore`; mitgeliefert
  ist nur `InMemoryReviewStore`.
- **Aussagekraft:** Namensgleichheit ist kein Identitätsnachweis, ein
  Nullbefund belegt keine Unbedenklichkeit; kein phonetisches Verfahren,
  Transliterationen nur über Listenaliase.
- **Netzwerk:** kein eingebauter Abruf; Transport, Rate-Limits und User-Agent
  über `auditcore_harvest` (VIES-Profil: 100 Anfragen je Stunde).
- **Geheimnisse:** der OpenSanctions-Schlüssel kommt aus einem
  Credential-Provider und wird nur als `Authorization: ApiKey` gesendet.
- **Eingaben:** XML über defusedxml (keine Entity-Expansion), keine aus
  Eingaben gebauten SQL-Texte.
- **Datenlizenzen** je Quelle sind nicht die MIT-Lizenz des Codes
  (OpenSanctions CC BY-NC 4.0, Verantwortung beim Betreiber; einzelne
  Nutzungsbedingungen nicht geprüft): [docs/source-catalog.json](docs/source-catalog.json).

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`) für Code und Profile dieses Pakets: Der Rechteinhaber hat am
22.09.2026 entschieden, dass die nach auditcore extrahierten Bibliotheken MIT
sind, die Quellrepositories nicht (`USER_AUTHORIZED_MIT`). Quellen, Commits,
Blobs und Erklärung: `NOTICE` und `provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
