# auditcore_registry_sources 0.1.0 (und auditcore_entity_matching 0.2.0) — Bericht

Stand: 23. September 2026. Branch `feat/auditcore-registry-sources`
(Worktree `auditcore-wt-registry`, Basis `main@886a53a`, danach `main@c1f436c` zusammengeführt). PR #22.

## Umfang

Neue Distribution `auditcore_registry_sources` (Debian
`python3-auditcore-registry-sources`), Laufzeit: Standardbibliothek,
`auditcore_harvest==0.1.0`, `auditcore_entity_matching==0.2.0`. Extras:
`fuzzy` (rapidfuzz), `xml` (defusedxml), `html` (BeautifulSoup). Keine
Laufzeitabhängigkeit auf `auditcore`, kein DB-/Netzwerkzugriff im Paket.

| Fähigkeit | Umsetzung |
|---|---|
| Listenformate | OpenSanctions `targets.simple.csv` (Kopf live bestätigt), EU FSF 1.1, OFAC SDN, UN SC (XML über defusedxml); Legacy- und Textdatum |
| Namensabgleich | Profile `audit_designer.sanctions_screening` und `flowworkshop.sanctions_screening`; Befund je Liste mit Stand, Status `HITS`/`NO_HITS`/`INCOMPLETE`/`NOT_SEARCHED`, Rohwert, Anpassungen, Unsicherheitsindikatoren |
| flowinvoice-Varianten | `difflib`-Listenprüfung (`flowinvoice.sanctions_local`), PEP-Massenabgleich (`flowinvoice.pep_bulk`) |
| Abgleichs-API | OpenSanctions `/match` mit `ApiKey` aus dem Credential-Provider, Sanktions-/PEP-Auswertung (`flowsearch.*`) |
| Eigentum/KMU | UBO-Traversierung und KMU-Einstufung als Profile mit `HUMAN_DECISION_REQUIRED` |
| Firmenprüfung | VIES (präfixunabhängig), OffeneRegister (gebundene Parameter), Indikatoren/Score (`flowinvoice.company_verification`) |
| Register-/Kammerquellen | Zuwendungsempfängerregister, IHK, Handwerkskammern |
| Harvest-Adapter | OpenSanctions-Listen, amtliche XML-Listen, ZER, IHK, HWK; Vollbestand nur bei `snapshot_complete` |
| Quellenkatalog | 13 Quellen mit Herkunft, Consumer, Datenlizenz, Konfigurationsschema, Live-Status |
| Legacy | gibt alle 456 Originalfälle wieder |

`auditcore_entity_matching` 0.2.0 (bestehende Profile unverändert): neue
Profilversionen `audit_designer.sanctions` und `flowworkshop.sanctions`
2026.09.2 für die Umschrift-Entscheidung vom 23.09.2026 (Designer PR #380,
Merge `1254591`; flowworkshop PR #49, Merge `3d1cb40`), Algorithmus
`casefold_nfc_fold_nfkd` (NFC wie im Designer), `flowinvoice.pep`
(`lower_nfkd_ascii`), `audit_portal.name[_folded]`. Kein vorhandenes Profil
entsprach der Designer-Entscheidung (`flowworkshop.state_aid` lässt ø/ł/É
stehen, andere Rechtsformlisten).

## Quellen, Rechte

GitHub-verifiziert (Blobs am 23.09.2026): audit_designer `1254591`,
flowworkshop `3d1cb40`, audit-portal `ac1ccc7`, flowsearch `10cb2a3`,
flowinvoice `fb2d185`, osint `d361ddb`, riskanalysis `b5c523b` (nur
dokumentiert). Code MIT nach Nutzerentscheidung vom 22.09.2026, keine
Umlizenzierung der Quell-Repositories. **Datenlizenzen getrennt**:
OpenSanctions-Daten und API CC BY-NC 4.0 (geprüft), amtliche Listen, VIES,
OffeneRegister, BZSt, DIHK, ZDH `REVIEW_REQUIRED`. Fixtures synthetisch im
Originalformat (Ausnahme: öffentliche VIES-Antwort zu `DE000000000`).

## Characterization und Befunde

`tools/capture_legacy.py` führt die Originale tatsächlich aus: 456 Fälle
(Designer 74, flowworkshop 55, audit-portal 38, flowsearch 173, flowinvoice
103 inkl. der beiden Originaltests, osint 7, riskanalysis 6). entity_matching:
220 + 73 + 140 weitere Fälle. Wichtige Befunde (Details
`packages/auditcore_registry_sources/docs/behavior-changes.md`, REG-C01…C18):
flowsearch findet mit der dokumentierten API-Antwort nie einen Treffer und
sendet keinen gültigen Schlüssel; der OpenRegister-Endpunkt existiert nicht
(404); flowinvoice meldet jede USt-IdNr. als ungültig (VIES-Präfixe),
`check_entity` scheitert immer (`UnboundLocalError`), sanctions.network ist
nicht auflösbar; `build_ownership_chain` terminiert bei Selbstverweis nicht.

## Tests und Gates (tatsächlich ausgeführt)

| Prüfung | Ergebnis |
|---|---|
| Paket-pytest registry_sources (Python 3.12) | 505 passed (Replay 452 in vier Dateien, Adapter/Harvest-Vertrag 10, Verträge Screening/Formate/Firma/API/Eigentum 30, Profile/Katalog/Architektur/Policy 13) |
| Paket-pytest entity_matching 0.2.0 (nach Zusammenführung mit `riskanalysis.payee` aus #17) | 981 passed; auditcore_risk gegen die zusammengeführte Version 573 passed |
| Plattform-pytest / ruff / mypy | 281 passed / PASS / PASS |
| ruff, ruff format, mypy strict, bandit -ll (beide Pakete) | PASS |
| auditcore-quality strict | Syntax, Lint, Typen, bandit, pip-audit, Tests, Supply Chain PASS; 2 Komplexitätswarnungen (XML-Parser in Originalstruktur); API-Vergleich NOT_EXECUTED (erste Version); Gesamt REVIEW_REQUIRED wegen Policy |
| Policy (verwaltung-app-framework@15f5338, GitHub-HEAD) | F-04, F-07, F-09, F-15, F-16 VERIFIED (T-09/14/30/37/38, Profile); offen F-05, F-07.ASSESS, T-12 (Personenbezug der Listen, Schutzbedarf/DSFA-Pflicht UNKNOWN) |
| `scripts/verify_domain_packages.py` (harvest, entity_matching, registry_sources) mit `--apt`, vor und nach dem Merge von `main` | je 35/35 PASS: Build, SBOM, hashgebundene Installation, `pip check`, Importherkunft, Smoke aus Wheel, selektive Installation, Entfernung, Debian-Pakete, signierte APT-Quelle, Installation/Upgrade 1→2/Entfernung im netzlosen Container |
| Wheel-SHA256 | registry_sources `49dada43a67ca891c0afe8e6dbb9c3511ffc8e9d94be6195308a07bbd937e7b2`, entity_matching 0.2.0 (zusammengeführt) `40d83815a15d7bf686b981f6116a0e7b0ba512a0cafc0d88ad9a74bc7acc5d73`, harvest unverändert `bc6cf59f…` |
| Graphify (Laufzeitmodule) | PASS, 471 Knoten, 1121 Kanten |

## Live-Prüfung (wenige zulässige Abrufe, keine Daten gespeichert)

`docs/live-smoke.json`: OpenSanctions `eu_fsf` PASS (6135 Einträge, Stand
23.09.2026 10:58 GMT), UN SC XML PASS (1011), IHK PASS (79), Handwerkskammern
PASS (53), ZER-Status PASS (529.437; Volldump bewusst nicht), VIES PASS
(Antwort mit `ns2:`), OffeneRegister FAIL (HTTP 502), OpenSanctions-API
NOT_CONFIGURED (kein Schlüssel; ohne Schlüssel HTTP 401).

## Consumer

In lokalen Kopien auf den gebundenen Commits umgestellt und mit den gebauten
Wheels geprüft (nicht gepusht, Requirements-Umstellung erst nach v0.3.0):
audit_designer (35 → 35 Sanktions-Tests, 341 → 341 Register/Recherche),
flowworkshop (29 → 29 inkl. 7 gegen Wegwerf-PostgreSQL), flowinvoice
(47 → 47, 32/32 Originalfälle gleich). Anleitung:
`packages/auditcore_registry_sources/docs/consumer-migration.md`. flowsearch
und osint: geplant.

## Entscheidungen vom 23.09.2026 (DECIDED, Folge-PR)

Nutzer: „alle empfehlungen, ... A2 abgedeckt durch nutzung, A3 sollte jeder dann
selber holen können“. Umgesetzt als neue empfohlene Profile (`recommended_profile`),
Quellprofile und Replays bitgenau:

- entity_matching: `audit_designer.sanctions` 2026.09.3 (R1), NFC überall über
  `compose` (R2: `flowworkshop.sanctions` 2026.09.3, `flowworkshop.state_aid`
  2026.09.2), `flowinvoice.pep` 2026.09.2 (R3), **`riskanalysis.payee` 2026.09.2**
  (K4, `Müller → mueller`) für auditcore_risk.
- registry_sources 2026.09.2: `audit_designer.sanctions_screening` (R1/R2/R8),
  `flowworkshop.sanctions_screening` (R2), `flowinvoice.pep_bulk` (R3),
  `flowsearch.ubo` nach § 3 Abs. 2 GwG (R4), `flowsearch.kmu` nach Anhang I AGVO
  (R5), `flowsearch.pep_risk` (R6) und `flowinvoice.company_verification` (R7)
  unverändert als entschieden; R9/R10 in der Consumer-Anleitung; A2 im Katalog;
  A3 `MatchClient(api_key=…)`/`credentials_from_environment` mit `NOT_CONFIGURED`.
- Nachweise: registry 524, entity_matching 989, risk 2356, Plattform 288 passed;
  `verify_domain_packages.py --apt` 35/35 PASS (Wheel registry `c7006dbe…`,
  entity_matching `60c6ebec…`).

## Ursprünglich offene Entscheidungen (inzwischen DECIDED, siehe oben)

Maßgebliches Screening-Profil und Schwellen, NFC bei zerlegten Umlauten,
flowinvoice-Varianten, UBO-Stimmrechtsschwelle/mittelbare Beteiligung, KMU
nach Anhang I AGVO, PEP-Risikostufen, Gewichte der Firmenprüfung, Auslisten
trotz Zeilenproblemen, OpenSanctions-Lizenz für Behördennutzung, Methodentext
des Designer-Werkzeugeintrags, flowinvoice-PEP-Normalisierung (entity_matching).
