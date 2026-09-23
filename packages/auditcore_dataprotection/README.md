# auditcore_dataprotection

Eigenständig installierbare, frameworkunabhängige Bibliothek, mit der
Anwendungen **eigene Verzeichnisse von Verarbeitungstätigkeiten (VVT) und
Datenschutz-Folgenabschätzungen (DSFA) anlegen, bearbeiten, berechnen,
versionieren, freigeben und ausgeben** können. Laufzeit: nur die
Standardbibliothek. Optional: `[excel]` (openpyxl und `auditcore_reporting[excel]==0.2.0`),
`[pdf]` (WeasyPrint).
Die Plattform `auditcore` ist keine Laufzeitabhängigkeit.

```bash
pip install auditcore_dataprotection==0.2.0            # Kern
pip install 'auditcore_dataprotection[excel]==0.2.0'    # zusätzlich XLSX
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

```python
from auditcore_dataprotection.rules import load_profile
from auditcore_dataprotection.calculation import propose

profil = load_profile("regulierung.dsgvo", "2026.09.1")
antworten = {k: False for k in profil.question_keys} | {"art35_3_a": True}
vorschlag = propose(profil, antworten, [
    {"dimension": "vertraulichkeit", "description": "Unbefugter Zugriff",
     "severity": 3, "likelihood": 4, "measures": ["zugriffskontrolle"]},
])
assert vorschlag.recommendation == "freigabe_mit_auflagen"   # netto 3 × 2 = 6
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

### Profile 2026.10.1: EDSA-Vorlage 2026

Seit 0.2.0 gibt es zu beiden Regimen die Profilfassung `2026.10.1`
(Schema `auditcore_dataprotection.profile/2`). Sie richtet die Dokumentation an
der Vorlage des Europäischen Datenschutzausschusses für
Datenschutz-Folgenabschätzungen aus (2026, Version 1.0, Konsultationsfassung)
und bildet die Risikostufen Feld für Feld aus der Matrix des
DSK-Kurzpapiers Nr. 18 (S. 5) statt aus Produktgrenzen. Die Fassungen
`2026.09.1` verhalten sich unverändert (Ausgaben byte-gleich zu 0.1.0).

| Neu in 2026.10.1 | EDSA-Vorlage |
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

`AssessmentService.hints()` liefert nicht blockierende Hinweise, wo die
Dokumentation hinter der Vorlage zurückbleibt. Der Bericht behält seine
Gliederung und ergänzt die neuen Angaben in den bestehenden Abschnitten. Die
Vorlage ist noch nicht endgültig; eine Endfassung wird eine neue Profilfassung.

```bash
python -m pip install -e '.[dev]'
python -m pytest
python -m ruff check .
python -m mypy src
```

Debian-Paket: `python3-auditcore-dataprotection`.
