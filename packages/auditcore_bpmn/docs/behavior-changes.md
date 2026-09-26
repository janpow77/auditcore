# Verhalten gegenüber den Originalen (audit_designer, FlowStat)

Charakterisiert mit `tools/capture_legacy.py` gegen `janpow77/audit_designer@eff41a4c`
(pandas 2.1.4, openpyxl 3.1.2, reportlab 4.0.8): 95 Fälle, davon 35 gezielt und
60 zufällig (Seed 20260925). Ergebnis: **eine** Abweichung in der Validierung;
Kennzahlen, ESI-Auszug, Personalkosten, Excel-Zellen/-Format/-Breiten und
PDF-Bytes (gleiche reportlab-Version, `invariant`) stimmen überein.

| Stelle | Original | auditcore_bpmn | Begründung |
|---|---|---|---|
| `validate_bpmn_bva` mit `<!DOCTYPE …>` ohne Entitäten | `DefusedET.fromstring` mit Standard `forbid_dtd=False`: DTD erlaubt, Prüfung läuft weiter | abgewiesen: „BPMN-XML ist nicht wohlgeformt: …“ | einheitliche Härtung; BPMN-Dateien enthalten nie eine DTD; das Original-Analysemodul (`safe_stdlib_fromstring`) wies DTDs bereits ab |
| Fehlermeldung bei DTD in der Analyse | `UnsafeStdlibXMLError(DTDForbidden(...))` | `UnsafeXmlError("XML mit DTD, Entität oder externem Verweis wird nicht verarbeitet: …")` | eigene Fehlerklasse (Unterklasse von `xml.etree.ElementTree.ParseError`) |
| `unique_owners`, `unique_departments`, `unique_systems` | `list(set(...))`: Reihenfolge je Prozesslauf zufällig | Reihenfolge des ersten Auftretens | deterministische Berichte; Inhalt gleich (Tests vergleichen ohne Reihenfolge) |
| Personalkosten | Datenbankabfrage `PersonnelCostRate` (im audit_designer nicht vorhanden → immer leer) | Port `personnel_rate(grade) -> float \| None`; ohne Port leer | keine Datenbank in der Bibliothek; Rechenweg (Anzahl × Satz × Stunden, Rundung) charakterisiert mit Stellvertreter-Modell |
| Excel | pandas `DataFrame.to_excel` + openpyxl | openpyxl direkt, Kopfzeilenformat wie pandas 2.1.4 (fett, dünner Rahmen, zentriert/oben) | kein pandas nötig; bei gleichen Kostenwerten bleibt die Reihenfolge (pandas sortiert kleine Tabellen stabil) |
| Rückgabe `export_bpmn_to_*` | `BytesIO` | `BytesIO` | unverändert |
| Parsen allgemein | lxml/defusedxml | defusedxml (Extra `xml`) oder gehärteter Expat | gleiches Verbot von DTD, Entitäten, externen Verweisen; zusätzlich Größenlimit 5 000 000 Zeichen wie das Altschema |

Nicht übernommen: FastAPI-Routen, Rechteprüfung, ORM, Kommentare
(`api/bpmn.py`), `ESIAnalysisService` (existiert im audit_designer nicht).
Die fachlichen Prüfregeln (`auditcore_bpmn.validation`) sind neu und ersetzen
`validate_bpmn_bva` nicht; diese bleibt für den Altvertrag erhalten.
