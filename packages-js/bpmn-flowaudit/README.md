# @flowaudit/bpmn-flowaudit

Framework-freie FlowAudit-Fachschicht für den BPMN-Editor: moddle-Deskriptor
des flowaudit-Schemas 1.0/1.1, Lesen und Schreiben der Erweiterungen, Rollen
an Pools/Bahnen, Kennzeichen, Prüfbezüge (KA/BK), Kontrollen, Risiken,
Nachweise, Fristen, Quellen, Feststellungen (`AuditFinding`), Prüfregeln
(`ValidationIssue`, gleicher Katalog wie `auditcore_bpmn`), Anreicherung aus
Dokumentation und Beschriftungen, Neutralisierung, Versions- und
Soll/Ist-Vergleich, Durchlauftest, Berichte (Prozesstabelle, RCM,
Feststellungsliste, MyST), Diagrammsammlung, SVG/PNG/PDF-Export, diagram-js-Module
(Plaketten, Hervorhebung, Rollen-Palette) und eigene Icons.

Kein Netz- oder Datenbankzugriff: Speicher, Rechtsgrundlagen-Suche,
KA/BK-Texte, Profile und Serverprüfung kommen über Ports herein.

```ts
import { loadDefinitions, modelFromDefinitions, validateModel, collectSuggestions, neutralize } from '@flowaudit/bpmn-flowaudit'
import { defaultProfile } from '@flowaudit/bpmn-flowaudit/profiles'

const model = modelFromDefinitions((await loadDefinitions(xml)).definitions)
const report = validateModel(model, { profile: defaultProfile() })
const suggestions = collectSuggestions(model, { profile: defaultProfile() })
const { xml: neutral, replacements } = neutralize(xml, { profile: defaultProfile() })
```

Im Editor: `flowauditEditorOptions()` liefert Module, moddle-Erweiterung und
Konfiguration für `new BpmnEditor({...})`. Ausführlich:
`docs/bpmn/frontend.md`.

## Lizenz und Herkunft

MIT (siehe `LICENSE`). Clean-Room-Erklärung: Dieses Paket enthält keinen Code,
keine Styles und keine Icons aus bpmn-js, bpmn-js-properties-panel,
@bpmn-io/properties-panel oder bpmn-font. Genutzt werden nur diagram-js und
bpmn-moddle (MIT) über den eigenen Kern `@flowaudit/bpmn-editor`. Portiert
wurde ausschließlich FlowAudit-eigener Code aus dem audit_designer
(Paritätsinventar: `docs/bpmn/paritaet-audit-designer.md`). Die Icons sind
eigene SVG-Pfade (24 px, `currentColor`).
