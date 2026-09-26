# Anbindung in Anwendungen (Beispiel audit_designer)

## Installation

```text
auditcore_bpmn[xml,excel,pdf]==0.1.0
```

oder Debian: `python3-auditcore-bpmn` (empfohlen zusätzlich
`python3-defusedxml`, `python3-openpyxl`, `python3-reportlab`).

## Ersetzung im audit_designer (FlowStat)

| Bisher | Neu |
|---|---|
| `services/bpmn_analyzer.analyze_bpmn(xml, name, db_session=db)` | `auditcore_bpmn.legacy.analyze_bpmn(xml, name, personnel_rate=lookup)` |
| `services/bpmn_export.export_bpmn_to_excel/pdf(...)` | `auditcore_bpmn.legacy.export_bpmn_to_excel/pdf(...)` |
| `api/bpmn.validate_bpmn_bva(xml)` | `auditcore_bpmn.legacy.validate_bpmn_bva(xml)` (Ergebnis `.valid/.errors/.warnings`, `to_dict()`) |
| `api/bpmn._assert_well_formed_xml(xml)` | `auditcore_bpmn.legacy.assert_well_formed_xml(xml)` → `BpmnXmlError`, in HTTP 422 übersetzen |
| Spalten `header_*`, `process_*` von `BpmnDiagram` | `auditcore_bpmn.legacy.diagram_info_from_legacy(row)` → `DiagramInfo`, schreiben mit `set_diagram_info` |
| — | fachliche Prüfung: `auditcore_bpmn.validate(xml).to_dict(language)` |
| Diagrammbaum (`diagrammBaum.ts`) | `DiagramCollection` mit Speicher-Port (`Storage`), Übersichten und Schlüsselabfragen |

Autorisierung, Mandantentrennung, Versionierung in der Datenbank und
Audit-Trail bleiben in der Anwendung. Für eine Checkliste oder einen Vermerk
fragt die Anwendung Elemente über stabile Schlüssel ab:

```python
collection.elements_by_key("prueffeld", "3.21")  # [(diagramm_id, element_id), …]
collection.elements_by_key("feststellung_ref", "T15 F1")
collection.elements_by_key("ka", "4")
```

## Personalkosten-Port

```python
def lookup(grade: str) -> float | None:
    rate = session.query(PersonnelCostRate).filter(...).first()
    return rate.hourly_cost if rate else None
```

## Profile

Das Standardprofil ist `foerderperiode-2021-2027`. Bewertungskriterien (aus
Leitlinien der Kommission) speist die Anwendung ein:

```python
profile = load_profile().with_assessment_criteria({2: [("2.1", "…"), ("2.2", "…")]})
registry = ProfileRegistry([profile])
report = validate(xml, ValidationConfig(registry=registry))
```

Eigene Profile (z. B. programmspezifische Rollen-Aliasse oder
Funktionstrennungsregeln) lädt `profile_from_dict` nach Schema
`profile-1.schema.json`.
