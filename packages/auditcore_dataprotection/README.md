# auditcore_dataprotection

Eigenständig installierbare, frameworkunabhängige Bibliothek, mit der
Anwendungen **eigene Verzeichnisse von Verarbeitungstätigkeiten (VVT) und
Datenschutz-Folgenabschätzungen (DSFA) anlegen, bearbeiten, berechnen,
versionieren, freigeben und ausgeben** können. Laufzeit: nur die
Standardbibliothek. Optional: `[excel]` (openpyxl), `[pdf]` (WeasyPrint).
Die Plattform `auditcore` ist keine Laufzeitabhängigkeit.

```bash
pip install auditcore_dataprotection==0.1.0            # Kern
pip install 'auditcore_dataprotection[excel]==0.1.0'    # zusätzlich XLSX
```

## Bausteine

| Modul | Aufgabe |
|---|---|
| `rules` | Versionierte, quellengebundene Regelprofile (`load_profile(id, version)`) mit Fingerprint. Kein stilles Standardprofil. |
| `calculation` | Schwellwertanalyse, Brutto-/Nettorisiko, Maßnahmenwirkung, begründeter Vorschlag mit Konsultationshinweis, Vorbelegung aus dem VVT. Strikte Eingaben: ja/nein/unbekannt. |
| `register` | VVT-Inhalt prüfen (Art. 30 Abs. 1 DSGVO), stabile Tätigkeitskennungen, Entwurf, Freigabe und Ablösung mit Vier-Augen-Prinzip und Revisionen. |
| `assessment` | DSFA aus einer konkreten Tätigkeitsfassung: Erhebung, Entscheidung mit Begründungspflicht, DSB-Stellungnahme und Folgerung, Konsultation, Freigabe, Prüfbedarf nach VVT-Änderung, Neubewertung. |
| `ports`, `memory` | Schnittstellen für Persistenz, Rechte, Audit, Zeit und Kennungen; In-Memory-Referenzadapter. |
| `export`, `excel`, `pdf` | Vollständige Berichtsdaten, HTML/JSON, optional XLSX/PDF; Tabellentexte werden immer als Literal geschrieben. |
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

```bash
python -m pip install -e '.[dev]'
python -m pytest
python -m ruff check .
python -m mypy src
```

Debian-Paket: `python3-auditcore-dataprotection`.
