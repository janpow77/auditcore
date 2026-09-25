# Fixtures aus dem audit_designer

Die Dateien sind wörtlich aus Tests bzw. Beispielen des Repositorys
`audit_designer` (Stand `origin/main`) übernommen – keine Produktionsdaten:

| Datei | Quelle |
| --- | --- |
| `flowaudit-metadaten.bpmn` | `backend/app/modules/flowstat/tests/test_bpmn_flowaudit_extensions.py` (`XML_MIT_METADATEN`) |
| `flowaudit-metadaten-alias-notiz.bpmn` | wie oben, Variante mit `flowaudit:notiz` (Test `test_alias_notiz_wird_ebenfalls_gelesen`) |
| `api-minimal.bpmn` | `backend/app/modules/flowstat/tests/test_bpmn_api.py` (`MINIMAL_BPMN_XML`) |
| `flowstat-legacy-attribute.bpmn` | `backend/app/modules/flowstat/tests/test_bpmn_services.py` (`FLOWSTAT_XML`) |
| `editor-standarddiagramm.bpmn` | `frontend/src/modules/flowstat/composables/useBpmnEditor.ts` (Standarddiagramm) |
| `editor-legacy-aliasse.bpmn` | `frontend/src/modules/flowstat/composables/__tests__/useBpmnEditor.spec.ts` (`LEGACY_XML`) |

Mehrere Dateien enthalten keine Diagramm-Information (DI); sie prüfen, dass
der Editor solche Dateien verlustfrei durchreicht.
