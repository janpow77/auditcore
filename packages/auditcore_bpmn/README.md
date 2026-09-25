# auditcore_bpmn

BPMN 2.0 mit der FlowAudit-Erweiterung (Schema 1.1) für Prüfbehörden und
Programmbehörden aller Fonds mit geteilter Mittelverwaltung. Framework-frei,
ohne Datenbank, ohne Pflichtabhängigkeiten.

| Bereich | Modul | Inhalt |
|---|---|---|
| Sicheres Parsen | `safe_xml`, `serialize` | DTD/Entitäten/externe Verweise verboten (defusedxml oder gehärteter Expat), rundlauftreues Schreiben |
| Elementmodell | `model` | alle BPMN-2.0-Elemente: Pools, Lanes (verschachtelt), Aktivitäten, Ereignisse, Gateways, Daten, Artefakte, Flüsse |
| Erweiterung | `extensions`, `writer` | Schema 1.0 (Freitext-Rechtsgrundlage, interne Notiz) und 1.1 (Diagramm-Infos, strukturierte Rechtsgrundlagen, Akteure, Kennzeichen, Prüfbezüge, Kontrollen, Risiken, Nachweise, Fristen, Verweise, Prüfschritte, Feststellungen, Quellen) |
| Profile | `profiles` | Kataloge je Förderperiode: KA nach Anhang XI VO (EU) 2021/1060 bzw. Anhang IV Delegierte VO (EU) Nr. 480/2014, Rollen, Fonds, Artikelüberschriften, Funktionstrennung, Vorlagen |
| Prüfregeln | `validation` | 70+ Regeln mit stabilen IDs (`BPMN-S…`, `BPMN-F…`, `BPMN-P…`, `BPMN-FT…`), Meldungen deutsch/englisch |
| Sammlung | `collection` | Ordner, Tags, Reihenfolge, Verweise, Übersichten, KA-Abdeckung, Schlüsselabfrage, Freigaben (SHA-256), Speicher-Port und Dateiablage |
| Vergleich | `comparison` | Versionsvergleich mit Synopse, Soll/Ist-Abgleich (erfüllt/nicht erfüllt), Einfärben |
| Neutralisieren | `neutralize` | Rollen statt Namen; E-Mail, Beträge, Firmen, Personen, Kennnummern, Befunde entfernt; Bericht |
| Anreichern | `enrichment` | Vorschläge aus Altbestand: Normzitate, Fundstellen, BK, Feststellungsbezüge, Prüffelder, Register, Rollen, Farben |
| Berichte | `reports` | Prozesstabelle, Risiko-Kontroll-Matrix, Feststellungsliste, Durchlauftest, KA-Kategorievorschlag; CSV, MyST, Excel |
| Legacy | `legacy` | legacy-treue Übernahme von `bpmn_analyzer.py`, `validate_bpmn_bva` und `bpmn_export.py` aus audit_designer |
| Normen | `citations`, `legal` | Zitate erkennen, CELEX/ELI/URL ableiten; Extra `legal` mit auditcore_legal_sources |

```python
from datetime import date
from auditcore_bpmn import parse_bpmn, validate, process_table, neutralize
from auditcore_bpmn.reports import to_myst, PROCESS_TABLE_COLUMNS

document = parse_bpmn(xml)
report = validate(document, reference_date=date(2026, 9, 25))
for item in report.issues:
    print(item.rule_id, item.severity, item.message())  # item.message("en")

print(to_myst(process_table(document), PROCESS_TABLE_COLUMNS, title="Prozessbeschreibung"))
neutral = neutralize(document)  # neutral.xml, neutral.summary()
```

## Extras

| Extra | Zweck | Debian |
|---|---|---|
| `xml` | defusedxml als Parser (ohne Extra: gleichwertig gehärteter Expat) | `python3-defusedxml` |
| `excel` | Legacy-Excelbericht, Berichte als xlsx | `python3-openpyxl` |
| `pdf` | Legacy-PDF-Bericht | `python3-reportlab` |
| `legal` | Normauflösung mit `auditcore_legal_sources` | `python3-auditcore-legal-sources` |

## Verbindliches Schema

`docs/bpmn/flowaudit-schema-1.1.md` im Repository und
`src/auditcore_bpmn/schemas/flowaudit-1.1.xsd`. JSON-Schemata:
`diagram-collection-1`, `validation-report-1`, `profile-1`.

## Herkunft und Verhalten

Siehe `provenance.json`, `NOTICE`, `docs/behavior-changes.md`,
`docs/consumer-integration.md` und `docs/rules.md`. Testdaten sind synthetisch;
Nutzerdiagramme werden nicht mitgeliefert.
