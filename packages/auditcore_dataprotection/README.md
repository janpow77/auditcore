# auditcore_dataprotection

## Zweck

Frameworkunabhängige Bibliothek, mit der Anwendungen eigene Verzeichnisse von Verarbeitungstätigkeiten (VVT) und Datenschutz-Folgenabschätzungen (DSFA) anlegen, berechnen, versionieren, freigeben und ausgeben.

Für Fachanwendungen der Verwaltung (Quelle: regulierung), die VVT und DSFA
mit Vier-Augen-Prinzip, Revisionen und Audit-Ereignissen führen. Datenbank,
Sitzung, HTTP und Benutzerverwaltung bleiben in der Anwendung; die
Regelprofile sind charakterisiertes Softwareverhalten, keine rechtliche
Prüfung.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install auditcore_dataprotection \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.4.3 im
Release v0.4.0; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-dataprotection/`):

```text
auditcore_dataprotection @ https://github.com/janpow77/auditcore/releases/download/v0.4.0/auditcore_dataprotection-0.4.3-py3-none-any.whl#sha256=25f5478b1007ddbfadbc0212136032af3650db0a92f77ca5f7a0d3b8136da18a
```

Debian/Ubuntu über die signierte APT-Quelle eines Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-dataprotection
```

Extras: `[excel]` – XLSX-Ausgabe (openpyxl und
`auditcore_reporting[excel]==0.2.2`); `[pdf]` – PDF-Bericht über WeasyPrint;
`[web]` – REST-Schnittstelle mit Starlette, `[fastapi]` – derselbe Vertrag als
FastAPI-Router (beide für die Oberflächen `<flowaudit-vvt>`/`<flowaudit-dsfa>`);
`[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

Eine Anwendung wählt ein Regelprofil ausdrücklich, übergibt ihre Speicher,
Rollenprüfung, Protokoll, Uhr und Kennungsvergabe als Schnittstellen und ruft
dann die Dienste auf. Das Beispiel nutzt die mitgelieferten Referenzadapter
aus `memory`; eine echte Anwendung setzt dort ihre Datenbank und ihre
Benutzerverwaltung ein. Der Test `tests/test_readme.py` führt dieses Beispiel aus.

```python
from datetime import date

from auditcore_dataprotection import (
    Actor,
    AssessmentService,
    Permission,
    RegisterService,
    load_profile,
)
from auditcore_dataprotection.export import assessment_report, render_assessment_html
from auditcore_dataprotection.memory import (
    FixedClock,
    InMemoryAssessmentRepository,
    InMemoryRegisterRepository,
    ListAuditSink,
    RoleAuthorizer,
    SequentialIds,
)

# 1. Profil ausdrücklich wählen (es gibt kein Standardprofil)
profil = load_profile("auditcore.dsgvo", "2026.10.3")

# 2. Schnittstellen der Anwendung (hier: Referenzadapter) und Dienste
rollen = RoleAuthorizer({"alle": frozenset(Permission)})
anna, bert = (Actor(n, frozenset({"behoerde"}), frozenset({"alle"})) for n in ("anna", "bert"))
vvt_db, dsfa_db = InMemoryRegisterRepository(), InMemoryAssessmentRepository()
log, uhr, ids = ListAuditSink(), FixedClock(), SequentialIds()
vvt = RegisterService(vvt_db, rollen, log, uhr, ids, profil)
dsfa_dienst = AssessmentService(dsfa_db, vvt_db, rollen, log, uhr, ids)

# 3. Verzeichnis anlegen und im Vier-Augen-Prinzip freigeben
taetigkeit = {
    "id": "t1",
    "name": "Fördermittelverwaltung",
    "referat": "Referat I",
    "zweck": "Bewilligung",
    "ermaechtigungsgrundlage": "LHO",
    "kategorien_betroffene": "Antragsteller",
    "kategorien_daten": "Stammdaten",
    "kategorien_empfaenger": "keine",
    "speicherdauer": "10 Jahre",
    "tom": "Rollenkonzept",
    "drittlandtransfer": False,
    "besondere_kategorien": False,
    "daten_art10": False,
    "anzahl_betroffene": 500,
}
entwurf = vvt.save_draft(
    "behoerde",
    anna,
    {
        "deckblatt": {"verantwortlicher": {"name": "Behörde"}, "dsb": {"name": "DSB"}},
        "referate": ["Referat I"],
        "taetigkeiten": [taetigkeit],
    },
)
vvt.release("behoerde", bert, expected_revision=entwurf.revision)

# 4. DSFA: erheben, entscheiden, Einholung des DSB-Rats dokumentieren, freigeben
d = dsfa_dienst.start("behoerde", anna, "t1", profil)
d = dsfa_dienst.update(
    "behoerde",
    anna,
    d.assessment_id,
    expected_revision=d.revision,
    answers={k: False for k in profil.question_keys} | {"art35_3_a": True},
    scenarios=[
        {
            "dimension": "vertraulichkeit",
            "description": "Unbefugter Zugriff",
            "severity": 3,
            "likelihood": 4,
            "measures": ["zugriffskontrolle"],
        }
    ],
    necessity="Erforderlich für die Bewilligung.",
    proportionality="Nur Pflichtangaben.",
    dossier={"team": "Referat I, IT", "umfang": "Bewilligungsverfahren"},
)
assert d.proposal["recommendation"] == "freigabe_mit_auflagen"
d = dsfa_dienst.decide(
    "behoerde",
    anna,
    d.assessment_id,
    expected_revision=d.revision,
    decision="freigabe_mit_auflagen",
    conditions=["Mehrfaktor-Anmeldung vor Start"],
)
d = dsfa_dienst.record_dpo_request(
    "behoerde",
    anna,
    d.assessment_id,
    expected_revision=d.revision,
    requested_from="DSB",
    requested_on=date(2026, 9, 24),
)
d = dsfa_dienst.release("behoerde", bert, d.assessment_id, expected_revision=d.revision)

# 5. Ergebnis: gesperrte Fassung mit offenen Punkten und Bericht
assert d.status.value == "freigegeben" and d.profile_version == "2026.10.3"
print(d.release_open_points)  # z. B. „Stellungnahme liegt noch nicht vor …“
html = render_assessment_html(assessment_report(d, profil))
```

Die wichtigsten Aufrufe: `load_profile`, `RegisterService.save_draft/release`,
`AssessmentService.start/update/decide/record_dpo_request/record_dpo_statement/release`,
`open_points` und `review_required` (Überprüfung nach Änderung des Verzeichnisses),
dazu `assessment_report` und `render_assessment_html` für den Bericht.

Das Verzeichnis selbst zeigt `render_register_html` als fertige Ansicht an, auf Wunsch
mit dem Stand der Folgenabschätzung je Tätigkeit:

```python
from auditcore_dataprotection.export import register_report, render_register_html

fassung = vvt.released("behoerde", anna)
ansicht = render_register_html(
    register_report(fassung, profil, overview=dsfa_dienst.overview("behoerde", anna))
)
```

Einzelne Berechnung ohne Dienste und Ablage:

```python
from auditcore_dataprotection.rules import load_profile
from auditcore_dataprotection.calculation import propose

profil = load_profile("regulierung.dsgvo", "2026.09.1")
antworten = {k: False for k in profil.question_keys} | {"art35_3_a": True}
vorschlag = propose(
    profil,
    antworten,
    [
        {
            "dimension": "vertraulichkeit",
            "description": "Unbefugter Zugriff",
            "severity": 3,
            "likelihood": 4,
            "measures": ["zugriffskontrolle"],
        },
    ],
)
assert vorschlag.recommendation == "freigabe_mit_auflagen"  # netto 3 × 2 = 6
assert vorschlag.profile["version"] == "2026.09.1"
```

Fehlt eine Antwort, lautet der Vorschlag `unvollstaendig`; eine fehlende Angabe
wird nie zu „Nein“ oder zu einer Freigabe. Der Vorschlag ist eine Empfehlung;
Entscheidung und Freigabe bleiben menschliche, zurechenbare Schritte.

## REST-Schnittstelle für die Oberfläche (0.5.0)

`auditcore_dataprotection.web` stellt Verzeichnis und Folgenabschätzung für
die Web Components `<flowaudit-vvt>` und `<flowaudit-dsfa>` bereit. Die
Handler rufen nur die Dienste der Bibliothek; Persistenz kommt über das
Protocol `Storage` (Register- und Abschätzungs-Repository plus Audit-Senke),
Mandant und Person über `identify`. Vertrag, Fehlercodes und Endpunkte:
[docs/ui/dataprotection-rest.md](../../docs/ui/dataprotection-rest.md).

```python no-run
from starlette.routing import Mount

from auditcore_dataprotection import load_profile
from auditcore_dataprotection.web import DataProtectionApi, create_backend
from auditcore_dataprotection.web.http import routes

profil = load_profile("auditcore.dsgvo", "2026.10.3")
api = DataProtectionApi(create_backend(profil, speicher, rechte))  # eigene Ports
anwendung_routes = [Mount("/api/dataprotection", routes=routes(api, identify))]
```

`identify(request)` liefert `Principal(tenant_id, Actor(...))` aus der Sitzung
der Anwendung oder `None` (401). Exporte: Druckansicht (HTML der Bibliothek),
Markdown und CSV mit Formelschutz.

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_dataprotection.__all__` (38):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `Actor` | Datenklasse | Authenticated person as established by the consumer application. | `model` |
| `Answer` | Datenklasse | Answer of the responsible department with its justification. | `answers` |
| `AnswerValue` | Aufzählung | Explicit three-valued answer; ``UNKNOWN`` is never treated as ``NO``. | `answers` |
| `Assessment` | Datenklasse | One version of a DPIA for exactly one activity version of a register. | `model` |
| `AssessmentService` | Datenklasse | Operations on DPIAs of one register; persistence and identity via ports. | `assessment` |
| `AssessmentStatus` | Aufzählung | Status of an assessment version. | `model` |
| `AuditEvent` | Datenklasse | Attributable change; persisted by the consumer's audit trail. | `model` |
| `AuthorizationError` | Ausnahme | The authorizer port denied the operation (403). | `errors` |
| `ConflictError` | Ausnahme | The requested transition is not allowed in the current state (409). | `errors` |
| `DataProtectionError` | Ausnahme | Base class; ``code`` is stable and machine readable. | `errors` |
| `FourEyesViolation` | Ausnahme | The releasing person also edited the version or gave the DPO statement (403). | `errors` |
| `LockedVersionError` | Ausnahme | A released version is immutable; a new version must be created. | `errors` |
| `NotFoundError` | Ausnahme | The entity does not exist within the given tenant (maps to 404). | `errors` |
| `Permission` | Aufzählung | Operations the authorizer port must allow for an actor and tenant. | `model` |
| `ProfileError` | Ausnahme | A rule profile is missing, malformed or does not contain a key. | `errors` |
| `Proposal` | Datenklasse | Reasoned recommendation; ``recommendation`` is one of the profile decisions or ``unvollstaendig``. | `results` |
| `RegisterService` | Datenklasse | Create, edit, version and release registers inside a tenant. | `register` |
| `RegisterStatus` | Aufzählung | Status of a register version. | `model` |
| `RegisterVersion` | Datenklasse | One version of a record of processing activities (Art. 30 GDPR). | `model` |
| `ReviewItem` | Datenklasse | A released assessment whose activity changed or disappeared (Art. 35 Abs. 11). | `model` |
| `RuleProfile` | Datenklasse | Immutable, explicitly selected rule profile. | `profile_model` |
| `Scenario` | Datenklasse | Risk scenario of one protection dimension, gross and optionally explicit net. | `answers` |
| `StaleRevisionError` | Ausnahme | Optimistic concurrency check failed; reload and retry. | `errors` |
| `TenantMismatchError` | Ausnahme | An object of another tenant was presented; treated like not found by consumers. | `errors` |
| `ValidationError` | Ausnahme | Input does not satisfy the contract (maps to 400/422). | `errors` |
| `__version__` | Wert | – | `(Paketstamm)` |
| `assess_risk` | Funktion | Gross = severity × likelihood; net after capped measure reductions or explicit values. | `risk` |
| `available_profiles` | Funktion | Packaged ``(id, version)`` pairs, sorted; no profile is a hidden default. | `profile_loader` |
| `check_activity` | Funktion | Content check of one activity against Art. 30 Abs. 1 GDPR fields. | `register_content` |
| `check_register` | Funktion | Cover sheet (Art. 30 Abs. 1 lit. a) plus every activity. | `register_content` |
| `finalize_consultation` | Funktion | Final consultation notice after the final assessment (DP-C21). | `calculation` |
| `load_profile` | Funktion | Load an explicitly named packaged profile version. | `profile_loader` |
| `normalize_content` | Funktion | Validate structure and types and persist a stable identifier per activity. | `register_content` |
| `parse_answers` | Funktion | Validate answers keyed by question. | `answers` |
| `parse_scenarios` | Funktion | Validate risk scenarios strictly against the profile scale and catalogues. | `answers` |
| `prefill_from_activity` | Funktion | Suggest answers from register data (Art. 9/10 data, number of persons, transfers). | `prefill` |
| `propose` | Funktion | Combine screening and risk into a reasoned, traceable recommendation. | `calculation` |
| `screen` | Funktion | Evaluate hard triggers, EDSA points and the FRIA marker in profile order. | `screening` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_dataprotection.answers` | Survey input of a DPIA: answers and risk scenarios, validated at the boundary. |
| `auditcore_dataprotection.assessment` | DPIA workflow: create from an activity version, edit, decide, involve the DPO, release. |
| `auditcore_dataprotection.assessment_checks` | Release checks of a DPIA version, in checking order. |
| `auditcore_dataprotection.assessment_core` | Ports, guards and read access shared by all DPIA operations. |
| `auditcore_dataprotection.assessment_html` | Self-contained, escaped HTML report of assessment report data. |
| `auditcore_dataprotection.assessment_html_outcome` | Outcome sections of the HTML assessment report: decision, notes, sources. |
| `auditcore_dataprotection.assessment_input` | Input handling of DPIA edits: omitted fields, change detection, review reset. |
| `auditcore_dataprotection.assessment_involvement` | DPO involvement and prior consultation of a DPIA version. |
| `auditcore_dataprotection.assessment_review` | Review after register changes, reassessment and the overview of a register. |
| `auditcore_dataprotection.calculation` | DSFA calculation: threshold analysis, gross/net risk and a reasoned proposal. |
| `auditcore_dataprotection.edpb` | DPIA documentation aligned with the EDPB template (2026, version 1.0). |
| `auditcore_dataprotection.errors` | Error contract. Consumers map ``code`` to their own HTTP or UI responses. |
| `auditcore_dataprotection.excel` | Optional Excel output (``pip install 'auditcore_dataprotection[excel]'``). |
| `auditcore_dataprotection.export` | Report data and dependency-free renderers (JSON, HTML). |
| `auditcore_dataprotection.hashing` | Canonical JSON digests that bind results to exact profile and register content. |
| `auditcore_dataprotection.html_common` | Escaping and styles shared by the HTML views of reports. |
| `auditcore_dataprotection.legacy` | Behavior-compatible adapter for the source application ``regulierung``. |
| `auditcore_dataprotection.legacy_admin` | Legacy-exact administration helpers of ``regulierung@a5d48ea``. |
| `auditcore_dataprotection.legacy_report` | Legacy-exact HTML report of ``regulierung@a5d48ea`` (``export.baue_bericht_html``). |
| `auditcore_dataprotection.legacy_scoring` | Legacy-exact screening, risk, proposal and prefill of ``regulierung@a5d48ea``. |
| `auditcore_dataprotection.memory` | In-memory reference adapters for tests and simple single-process consumers. |
| `auditcore_dataprotection.model` | Immutable records, actors, permissions and audit events. |
| `auditcore_dataprotection.pdf` | Optional PDF output via WeasyPrint (``pip install 'auditcore_dataprotection[pdf]'``). |
| `auditcore_dataprotection.ports` | Interfaces the consumer application implements. |
| `auditcore_dataprotection.prefill` | Suggested screening answers from register data; never stored automatically. |
| `auditcore_dataprotection.profile_loader` | Loading and validating rule profile documents (packaged JSON, schema 1 and 2). |
| `auditcore_dataprotection.profile_model` | Rule profile model: schema constants, catalogue records and :class:`RuleProfile`. |
| `auditcore_dataprotection.profile_sections` | Sections of rule profile documents: primitives and the schema 2 (EDPB) parts. |
| `auditcore_dataprotection.profiles` | – |
| `auditcore_dataprotection.register` | Records of processing activities: versions, drafts and four-eyes release. |
| `auditcore_dataprotection.register_content` | Content of a register version: structure, identifiers, content checks, changes. |
| `auditcore_dataprotection.register_html` | Self-contained, escaped HTML view of register report data. |
| `auditcore_dataprotection.report_data` | Report data of assessments and registers as JSON-compatible documents. |
| `auditcore_dataprotection.results` | Results of the DSFA calculation: issues, screening, risk and the proposal. |
| `auditcore_dataprotection.risk` | Risk assessment: gross risk, capped measure effects, explicit residual values. |
| `auditcore_dataprotection.rules` | Versioned, source-bound rule profiles for screening, risk and workflow. |
| `auditcore_dataprotection.screening` | Threshold analysis: hard triggers, EDPB points and the FRIA marker. |
| `auditcore_dataprotection.web` | REST interface of the VVT and DSFA UI (``<flowaudit-vvt>``, ``<flowaudit-dsfa>``). |
| `auditcore_dataprotection.workbook_tables` | Flat tables of register and overview workbooks (no spreadsheet dependency). |
<!-- api-overview:end -->

Bausteine:

| Modul | Aufgabe |
|---|---|
| `rules` | Versionierte, quellengebundene Regelprofile (`load_profile(id, version)`) mit Fingerprint. Kein stilles Standardprofil. |
| `calculation` | Schwellwertanalyse, Brutto-/Nettorisiko, Maßnahmenwirkung, begründeter Vorschlag mit Konsultationshinweis, Vorbelegung aus dem VVT. Strikte Eingaben: ja/nein/unbekannt. |
| `register` | VVT-Inhalt prüfen (Art. 30 Abs. 1 DSGVO), stabile Tätigkeitskennungen, Entwurf, Freigabe und Ablösung mit Vier-Augen-Prinzip und Revisionen. |
| `assessment` | DSFA aus einer konkreten Tätigkeitsfassung: Erhebung, Entscheidung mit Begründungspflicht, DSB-Stellungnahme und Folgerung, Konsultation, Freigabe, Prüfbedarf nach VVT-Änderung, Neubewertung. |
| `ports`, `memory` | Schnittstellen für Persistenz, Rechte, Audit, Zeit und Kennungen; In-Memory-Referenzadapter. |
| `export`, `excel`, `pdf` | Vollständige Berichtsdaten, HTML/JSON, optional XLSX/PDF. Die neuen tabellarischen XLSX-Exporte nutzen den Renderer von `auditcore_reporting` 0.2.1; die Legacy-Layouts mit verbundenen Zellen bleiben ein eigener openpyxl-Adapter. Tabellentexte werden immer als Literal geschrieben. |
| `web` | REST-Schnittstelle `dataprotection_ui/1` für `<flowaudit-vvt>` und `<flowaudit-dsfa>` (`@flowaudit/ui`): `DataProtectionApi` ohne Framework, `routes`/`create_app` (Extra `web`), `create_router` (Extra `fastapi`), Speicher als Protocol `Storage`. |
| `legacy` | Verhaltensgleicher Adapter der Quellanwendung `regulierung` für bestehende Consumer. |

Die Module der Tabelle sind die öffentlichen Einstiegspunkte. Seit 0.4.1 sind sie
nach Verantwortung in kleinere Module geschnitten (etwa `answers`, `screening`,
`risk`, `results`, `prefill` hinter `calculation`; `profile_model`,
`profile_loader`, `profile_sections` hinter `rules`; `register_content` hinter
`register`; `assessment_core`, `assessment_input`, `assessment_checks`,
`assessment_involvement`, `assessment_review` hinter `assessment`;
`report_data`, `assessment_html`, `assessment_html_outcome`, `register_html` hinter `export`;
`legacy_scoring`, `legacy_admin`, `legacy_report` hinter `legacy`). Alle bisher
importierbaren Namen bleiben unter ihrem alten Modulpfad erreichbar.

## Profile und Konfiguration

Profile werden immer ausdrücklich gewählt (`load_profile(id, version)`), es
gibt kein Standardprofil. Verfügbar: `regulierung.dsgvo` und
`regulierung.hdsig_ji` 2026.09.1 (Legacy-Fassung der Quelle) sowie die
Bibliotheksprofile `auditcore.dsgvo` und `auditcore.hdsig_ji` in den Fassungen
2026.10.1, 2026.10.2 und 2026.10.3 (empfohlen für neue Abschätzungen).
Rechtsregime (DSGVO, Dritter Teil HDSIG) bleiben getrennte Profile.

### Bibliotheksprofile `auditcore.dsgvo` und `auditcore.hdsig_ji` (2026.10.1)

Seit 0.2.0 hat die Bibliothek eigene, neutrale Regelprofile
`auditcore.dsgvo` und `auditcore.hdsig_ji` in der Fassung `2026.10.1`
(Schema `auditcore_dataprotection.profile/2`), ohne Textbausteine der
Ursprungsanwendung. Die Profile `regulierung.*` 2026.09.1 bleiben
unverändert zur Nachvollziehbarkeit und für den `legacy`-Vertrag.
Die neuen Profile richten die Dokumentation an
der Vorlage des Europäischen Datenschutzausschusses für
Datenschutz-Folgenabschätzungen aus (2026, Version 1.0, Konsultationsfassung)
und bildet die Risikostufen Feld für Feld aus der Matrix des
DSK-Kurzpapiers Nr. 18 (S. 5) statt aus Produktgrenzen. Die Fassungen
`2026.09.1` verhalten sich unverändert (Ausgaben byte-gleich zu 0.1.0).

| Neu in `auditcore.*` 2026.10.1 | EDSA-Vorlage |
|---|---|
| Entscheidung `verworfen` (Verarbeitung unterbleibt) | Abschnitt 6 |
| Bedingungen einer Freigabe mit Auflagen, vor der Freigabe Pflicht | Abschnitt 6 |
| Grund der Konsultation, u. a. Art. 36 Abs. 5 DSGVO | Abschnitt 6 |
| Risikostufen aus der Matrix des DSK-Kurzpapiers Nr. 18; Methode im Bericht | Abschnitt 4.1.b; KP 18, S. 5 |
| Mindeststufe `mittel` ab Schwere 4 vor Maßnahmen | Explainer Fn. 9; KP 18, S. 5 |
| Risikoquelle, Umstände, Hinnehmbarkeit vor und nach Maßnahmen | Abschnitte 3.1, 4.1.a, 4.1.c, 4.2.b |
| Maßnahmenbereiche und Umsetzungsstand | Abschnitte 2.3, 4.2.a |
| Maßnahmenplan | Abschnitt 4.2.c |
| Stammdaten der Abschätzung (Team und Umfang Pflicht, Billigung mit Datum) | Abschnitte 0.4, 0.5, 1.1.c, 1.4, 2.2.b |
| Quellenliste im Profil und im Bericht | Abschnitt 0.5 |
| Alle 17 Nummern der DSK-Muss-Liste als eigene harte Fragen (bisher 8 Nummern in 5 Fragen) | Art. 35 Abs. 4 DSGVO |

Seit 0.3.0 (Fassung `2026.10.3`) arbeiten die Profile im Dokumentationsmodus: Keine inhaltliche
Prüfung verhindert die Freigabe; offene Punkte (`open_points()`) werden mit der Freigabe
gespeichert und im Bericht ausgewiesen. Für die DSB genügt die dokumentierte Einholung
(`record_dpo_request`). Rechte und Vier-Augen-Prinzip bleiben.

`AssessmentService.hints()` liefert nicht blockierende Hinweise, wo die
Dokumentation hinter der Vorlage zurückbleibt. Der Bericht behält seine
Gliederung und ergänzt die neuen Angaben in den bestehenden Abschnitten. Die
Vorlage ist noch nicht endgültig; eine Endfassung wird eine neue Profilfassung.

### Profile 2026.10.2: Konsultationshinweis erst nach abschließender Bewertung

Die Fassung `2026.10.2` der Profile `auditcore.dsgvo` und `auditcore.hdsig_ji`
entspricht `2026.10.1` und setzt die Nutzerentscheidung
A5 vom 23.09.2026 um (DP-C21): Der Hinweis auf die vorherige Konsultation der
Aufsichtsbehörde (Art. 36 Abs. 1 DSGVO, Erwägungsgrund 94 DSGVO; im JI-Profil
§ 64 HDSIG) wird erst mit der abschließenden Bewertung (`decide`) gegeben und
nur, wenn das Nettorisiko nach Maßnahmen hoch bleibt. Vorher trägt der
Vorschlag höchstens `consultation_notice.status == "voraussichtlich_erforderlich"`
mit dem Text „Vorläufiger Hinweis: …“ und nie `consultation_required=True`.
`finalize_consultation(profil, vorschlag, entscheidung)` bildet den endgültigen
Hinweis. Empfohlen für neue Abschätzungen; ältere Fassungen bleiben unverändert.

### Verantwortung der Anwendung

Die Bibliothek enthält keine Datenbank, keine Sitzung und keine
Benutzerverwaltung; HTTP nur im optionalen Modul `web`. Die Anwendung implementiert `RegisterRepository`,
`AssessmentRepository`, `Authorizer`, `AuditSink`, `Clock` und `IdFactory`
(`ports`), ruft jede Operation innerhalb ihrer eigenen Transaktion auf und
erzwingt die Unveränderlichkeit freigegebener Fassungen zusätzlich in der
Datenbank. Die Dienste prüfen bei jeder Operation Berechtigung, Mandant und
Revision und erzeugen Audit-Ereignisse; sie ersetzen weder die serverseitige
Autorisierung noch die Oberfläche der Anwendung.

## Herkunft und Charakterisierung

Quelle: `janpow77/regulierung@a5d48ea4` (`services/dsfa/*`,
`mandant_dsgvo_service.py`). Das Verhalten des Originals wurde vor der
Extraktion tatsächlich ausgeführt und aufgezeichnet
(`tools/capture_regulierung_legacy.py`, 241 Einzelfälle, 65 Ablaufschritte,
Exporte als HTML, PDF und XLSX). `legacy` und die Profile `regulierung.*`
2026.09.1 reproduzieren es **legacy-exakt**; die Profile `auditcore.*` sind
eine eigene Weiterentwicklung nach der EDSA-Vorlage und dem DSK-Kurzpapier
Nr. 18.

## Bewusste Verhaltensabweichungen

Der neue Vertrag korrigiert begründet unter anderem unvollständige Antworten
(DP-C01), Wahrheitswerte aus Zeichenketten (DP-C03), ungeprüfte Restwerte
(DP-C06), fehlende Mandantenbindung (DP-C12), das Vier-Augen-Prinzip
(DP-C13/DP-C14), Formel-Injektion in Excel (DP-C15) und den Zeitpunkt des
Konsultationshinweises (DP-C21). Vollständige Liste und offene fachliche
Entscheidungen: [docs/behavior-changes.md](docs/behavior-changes.md).

## Abhängigkeiten

Python ≥ 3.11, zur Laufzeit `auditcore_common==0.1.1` (gemeinsame
Hilfsfunktionen, nur Standardbibliothek); die Plattform `auditcore` ist keine
Abhängigkeit. Optional über `[excel]`
`openpyxl>=3.0.9,<4` und `auditcore_reporting[excel]==0.2.2`, über `[pdf]`
`weasyprint>=60.2`, über `[web]` Starlette und über `[fastapi]` FastAPI.

## Sicherheit und Datenschutz

Die Dienste prüfen bei jeder Operation Berechtigung, Mandant und Revision und
erzeugen Audit-Ereignisse; freigegebene Fassungen sind gesperrt, die
Anwendung erzwingt das zusätzlich in ihrer Datenbank. Die Bibliothek speichert
selbst nichts und nutzt kein Netzwerk. Tabellentexte werden in XLSX immer als
Literal geschrieben (keine Formeln). Der Vorschlag ist eine Empfehlung:
Entscheidung und Freigabe bleiben menschliche, zurechenbare Schritte, und
eine fehlende Angabe wird nie zu „Nein“ oder zu einer Freigabe.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Freigabe des extrahierten Codes durch den Rechteinhaber am
22.09.2026, siehe `NOTICE` und `provenance.json`. Die BfDI-Mustervorlage
(CC-BY-SA 4.0) ist nicht enthalten.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
