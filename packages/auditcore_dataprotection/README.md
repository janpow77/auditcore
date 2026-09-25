# auditcore_dataprotection

Eigenständig installierbare, frameworkunabhängige Bibliothek, mit der
Anwendungen **eigene Verzeichnisse von Verarbeitungstätigkeiten (VVT) und
Datenschutz-Folgenabschätzungen (DSFA) anlegen, bearbeiten, berechnen,
versionieren, freigeben und ausgeben** können. Laufzeit: nur die
Standardbibliothek. Optional: `[excel]` (openpyxl und `auditcore_reporting[excel]==0.2.0`),
`[pdf]` (WeasyPrint).
Die Plattform `auditcore` ist keine Laufzeitabhängigkeit.

```bash
pip install auditcore_dataprotection==0.4.1            # Kern
pip install 'auditcore_dataprotection[excel]==0.4.1'    # zusätzlich XLSX
```

## Schnellstart in Python

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

## Bausteine

| Modul | Aufgabe |
|---|---|
| `rules` | Versionierte, quellengebundene Regelprofile (`load_profile(id, version)`) mit Fingerprint. Kein stilles Standardprofil. |
| `calculation` | Schwellwertanalyse, Brutto-/Nettorisiko, Maßnahmenwirkung, begründeter Vorschlag mit Konsultationshinweis, Vorbelegung aus dem VVT. Strikte Eingaben: ja/nein/unbekannt. |
| `register` | VVT-Inhalt prüfen (Art. 30 Abs. 1 DSGVO), stabile Tätigkeitskennungen, Entwurf, Freigabe und Ablösung mit Vier-Augen-Prinzip und Revisionen. |
| `assessment` | DSFA aus einer konkreten Tätigkeitsfassung: Erhebung, Entscheidung mit Begründungspflicht, DSB-Stellungnahme und Folgerung, Konsultation, Freigabe, Prüfbedarf nach VVT-Änderung, Neubewertung. |
| `ports`, `memory` | Schnittstellen für Persistenz, Rechte, Audit, Zeit und Kennungen; In-Memory-Referenzadapter. |
| `export`, `excel`, `pdf` | Vollständige Berichtsdaten, HTML/JSON, optional XLSX/PDF. Die neuen tabellarischen XLSX-Exporte nutzen den Renderer von `auditcore_reporting` 0.2.0; die Legacy-Layouts mit verbundenen Zellen bleiben ein eigener openpyxl-Adapter. Tabellentexte werden immer als Literal geschrieben. |
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

## Verantwortung der Anwendung

Die Bibliothek enthält keine Datenbank, keine Sitzung, kein HTTP und keine
Benutzerverwaltung. Die Anwendung implementiert `RegisterRepository`,
`AssessmentRepository`, `Authorizer`, `AuditSink`, `Clock` und `IdFactory`
(`ports`), ruft jede Operation innerhalb ihrer eigenen Transaktion auf und
erzwingt die Unveränderlichkeit freigegebener Fassungen zusätzlich in der
Datenbank. Die Dienste prüfen bei jeder Operation Berechtigung, Mandant und
Revision und erzeugen Audit-Ereignisse; sie ersetzen weder die serverseitige
Autorisierung noch die Oberfläche der Anwendung.

## Herkunft, Lizenz, Grenzen

Quelle: `janpow77/regulierung@a5d48ea4b90a410210ec25e707781ef9e21ad743`
(`services/dsfa/*`, `mandant_dsgvo_service.py`). MIT-Freigabe durch den
Rechteinhaber am 22.09.2026, siehe `NOTICE` und `provenance.json`. Die
BfDI-Mustervorlage (CC-BY-SA 4.0) ist nicht enthalten.

Das Verhalten des Originals wurde vor der Extraktion tatsächlich ausgeführt und
aufgezeichnet (`tools/capture_regulierung_legacy.py`). `legacy` reproduziert es
exakt; der neue Vertrag korrigiert begründet unter anderem unvollständige
Antworten, Wahrheitswerte aus Zeichenketten, ungeprüfte Restwerte, fehlende
Mandantenbindung und Formel-Injektion in Excel. Vollständige Liste und offene
fachliche Entscheidungen: [docs/behavior-changes.md](docs/behavior-changes.md).

Die Regelprofile sind charakterisiertes Softwareverhalten
(`SOURCE_CHARACTERIZED`), keine rechtliche Prüfung. Rechtsregime (DSGVO,
Dritter Teil HDSIG) bleiben getrennte Profile.

### Bibliotheksprofile `auditcore.dsgvo` und `auditcore.hdsig_ji` (2026.10.1)

Seit 0.2.0 hat die Bibliothek eigene, neutrale Regelprofile
`auditcore.dsgvo` und `auditcore.hdsig_ji` in der Fassung `2026.10.1`
(Schema `auditcore_dataprotection.profile/2`), ohne Textbausteine der
Ursprungsanwendung. Die Profile `regulierung.*` 2026.09.1 bleiben
unverändert zur Nachvollziehbarkeit und für den `legacy`-Vertrag.
Die neuen Profile Sie richtet die Dokumentation an
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

```bash
python -m pip install -e '.[dev]'
python -m pytest
python -m ruff check .
python -m mypy src
```

Debian-Paket: `python3-auditcore-dataprotection`.
