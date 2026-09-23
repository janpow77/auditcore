# auditcore_registry_sources

Eigenständig installierbare Bibliothek für **Register-, Sanktions- und
PEP-Quellen** mit ausdrücklich gewählten, quellengebundenen Profilen:
Listenformate lesen, Listen über `auditcore_harvest` abrufen, Namen gegen
Listenbestände abgleichen, Abgleichs-API auswerten, Firmendaten prüfen.
Namensnormalisierung kommt aus `auditcore_entity_matching` (keine eigene
Kopie). Keine Datenbank, kein Scheduler, keine eingebauten Netzwerkzugriffe.

```python
from auditcore_registry_sources import (
    ListSnapshot,
    load_lists,
    load_profile,
    parse_targets_simple_csv,
    screen,
)
from auditcore_registry_sources.lists import find_list

eu = parse_targets_simple_csv(csv_bytes, list_key="eu_fsf")  # Fehler statt leerer Liste
lists = load_lists("audit_designer.sanctions_lists", "2026.09.1")
snapshots = [ListSnapshot(find_list(lists, "eu_fsf"), eu.entries, as_of="2026-09-22")]
result = screen(
    "Müller-Lüdenscheidt GmbH",
    snapshots,
    load_profile("audit_designer.sanctions_screening", "2026.09.1"),
)
result.status  # HITS / NO_HITS / INCOMPLETE / NOT_SEARCHED
result.findings  # je Liste: abgefragt?, Bestand, Stand
result.hits[0].indicators  # z. B. token_subset, alias_match, date_of_birth_not_compared
```

| Modul | Inhalt |
|---|---|
| `opensanctions_csv` | `targets.simple.csv` lesen/schreiben (Kopf live bestätigt), Zeilenprobleme sichtbar |
| `sanctions_xml` | EU FSF 1.1, OFAC SDN, UN SC (Extra `xml`, defusedxml); Legacy- und Textdatum |
| `screening` | rapidfuzz-Abgleich (Extra `fuzzy`) nach Profil `audit_designer.sanctions_screening` bzw. `flowworkshop.sanctions_screening`; Geburtsjahr/Land, Klassen, Befund je Liste |
| `bulk_screening` | flowinvoice-Varianten: `difflib`-Listenprüfung und PEP-Massenabgleich |
| `opensanctions_api` | `/match`-Client (Schlüssel über Credential-Provider, `Authorization: ApiKey`), Sanktions- und PEP-Auswertung (`flowsearch.*`) |
| `ownership` | UBO-Traversierung/-Schwelle und KMU-Einstufung als Profile mit offenen Entscheidungen |
| `company` | VIES-Prüfung, OffeneRegister-Abfrage (gebundene Parameter), Indikatoren/Score |
| `chambers` | Zuwendungsempfängerregister, IHK, Handwerkskammern (Extra `html`) |
| `adapters` | `auditcore_harvest`-Adapter: OpenSanctions-Listen, amtliche XML-Listen, ZER, IHK, HWK |
| `legacy` | verhaltensgleiche Wiedergabe der Originale (456 Fälle) |

Profile (`available_profiles()`): Listenkataloge `audit_designer`, `flowworkshop`,
`official`; Screening `audit_designer`, `flowworkshop`, `flowinvoice.sanctions_local`,
`flowinvoice.pep_bulk`; API `flowsearch.opensanctions_match`, `flowsearch.pep_risk`,
`flowinvoice.sanctions_network` (LEGACY_ONLY); `flowsearch.ubo`, `flowsearch.kmu`,
`flowinvoice.company_verification`. Widersprüchliche Varianten tragen
`HUMAN_DECISION_REQUIRED` im Profil und in jedem Ergebnis. **Empfohlen** nach den
Nutzerentscheidungen vom 23.09.2026 sind die Nachfolger 2026.09.2 über
`recommended_profile(zweck)` (`sanctions_screening`, `pep_bulk`, `pep_risk`,
`ubo`, `sme`, `company_verification`).

OpenSanctions-API: Den Schlüssel beschafft jeder Betreiber selbst
(https://www.opensanctions.org/api/) und übergibt ihn als `MatchClient(api_key=…)`
oder per `credentials_from_environment(os.environ)` aus `OPENSANCTIONS_API_KEY`;
ohne Schlüssel meldet `MatchClient.status` `NOT_CONFIGURED`.

Datenlizenzen je Quelle (≠ MIT des Codes) und Live-Prüfstatus:
[docs/source-catalog.json](docs/source-catalog.json),
[docs/live-smoke.json](docs/live-smoke.json). Unterschiede zu den Originalen:
[docs/behavior-changes.md](docs/behavior-changes.md). Consumer:
[docs/consumer-migration.md](docs/consumer-migration.md). Debian-Paket:
`python3-auditcore-registry-sources`.
