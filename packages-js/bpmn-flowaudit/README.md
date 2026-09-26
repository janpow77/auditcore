# @auditcore/bpmn-flowaudit

## Zweck

Framework-freie FlowAudit-Fachschicht für den BPMN-Editor: Schema flowaudit 1.0/1.1, Rollen, Kennzeichen, Prüfbezüge, Prüfregeln, Anreicherung, Neutralisierung, Vergleiche, Durchlauftest, Berichte und Export.

Für Anwendungen, die BPMN-Prozesse der Verwaltungs- und Kontrollsysteme
modellieren und prüfen – mit `@auditcore/bpmn-vue` als Oberfläche oder ohne.
Kein Netz- oder Datenbankzugriff: Speicher, Rechtsgrundlagen-Suche,
KA/BK-Texte, Profile und Serverprüfung kommen über Ports herein.

## Installation

Standardweg ist die npm-Registry; npm löst die übrigen `@auditcore`-Pakete
der Abhängigkeitshülle selbst auf:

```sh
npm install @auditcore/bpmn-flowaudit
```

Ohne Registry-Zugang (Intranet, offline) bleibt der signierte Tarball aus
dem GitHub-Release von auditcore; dann gehört jedes Paket der Hülle
ausdrücklich in die `package.json`:

```sh
npm install @auditcore/bpmn-flowaudit@https://github.com/janpow77/auditcore/releases/download/v<release>/auditcore-bpmn-flowaudit-0.2.0.tgz
```

Anleitung für Vue, React und Web Components mit Integritätsprüfung und
`vendor/`-Ablage:
[frontend-installation.md](../../docs/deployment/frontend-installation.md).

Für die Editor-Module (`flowauditEditorOptions()`) zusätzlich `@auditcore/bpmn-editor` (optionale Peer-Abhängigkeit). Stile: `@auditcore/bpmn-flowaudit/style.css`.

Im auditcore-Repository gehört das Paket zum npm-Workspace (`npm ci` im
Stamm, Bau mit `npm run build -w @auditcore/bpmn-flowaudit`).

## Schnellstart

Modell lesen und mit dem Standardprofil prüfen (läuft in Node, ohne DOM):

```ts run
import { loadDefinitions, modelFromDefinitions, validateModel } from '@auditcore/bpmn-flowaudit'
import { defaultProfile } from '@auditcore/bpmn-flowaudit/profiles'

const xml = `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_1" isExecutable="false">
    <bpmn:startEvent id="Start_1" name="Antrag eingegangen" />
    <bpmn:task id="Task_1" name="Antrag prüfen" />
    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start_1" targetRef="Task_1" />
  </bpmn:process>
</bpmn:definitions>`

const model = modelFromDefinitions((await loadDefinitions(xml)).definitions)
const report = validateModel(model, { profile: defaultProfile() })
if (!report.issues.some((issue) => issue.elementId === 'Task_1')) throw new Error('Hinweis zu Task_1 fehlt')
console.log(report.issues.map((issue) => `${issue.ruleId} ${issue.severity}`))
```

Vorschläge und Neutralisierung (`neutralize` braucht `DOMParser`, also Browser
oder DOM-Umgebung):

```ts
import { collectSuggestions, loadDefinitions, modelFromDefinitions, neutralize } from '@auditcore/bpmn-flowaudit'
import { defaultProfile } from '@auditcore/bpmn-flowaudit/profiles'

declare const xml: string
const model = modelFromDefinitions((await loadDefinitions(xml)).definitions)
const suggestions = collectSuggestions(model, { profile: defaultProfile() })
const { xml: neutral, replacements } = neutralize(xml, { profile: defaultProfile() })
```

## Einbindung

Framework-frei; im Editorkern: `flowauditEditorOptions()` liefert Module,
moddle-Erweiterung und Konfiguration für `new BpmnEditor({...})` aus
`@auditcore/bpmn-editor`. Die Vue-Oberfläche, die Web Component
`<flowaudit-bpmn-editor>` und die React-Hülle liegen in `@auditcore/bpmn-vue`
und `@auditcore/bpmn-react`. Ausführlich: `docs/bpmn/frontend.md`.

## API-Überblick

Inhalt: moddle-Deskriptor des flowaudit-Schemas 1.0/1.1, Lesen und Schreiben
der Erweiterungen, Rollen an Pools/Bahnen, Kennzeichen, Prüfbezüge (KA/BK),
Kontrollen, Risiken, Nachweise, Fristen, Quellen, Feststellungen
(`AuditFinding`), Prüfregeln (`ValidationIssue`, gleicher Katalog wie
`auditcore_bpmn`), Anreicherung aus Dokumentation und Beschriftungen,
Neutralisierung, Versions- und Soll/Ist-Vergleich, Durchlauftest, Berichte
(Prozesstabelle, RCM, Feststellungsliste, MyST), Diagrammsammlung,
SVG/PNG/PDF-Export, diagram-js-Module (Plaketten, Hervorhebung,
Rollen-Palette) und eigene Icons.

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Exporte der Einstiegspunkte aus `package.json#exports` (450):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@auditcore/bpmn-flowaudit` | `AUDIT_TYPES` | Konstante | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `Actor` | Schnittstelle | – | `schema/types` |
| `@auditcore/bpmn-flowaudit` | `ApplyOptions` | Schnittstelle | – | `enrichment/suggestions` |
| `@auditcore/bpmn-flowaudit` | `Approval` | Schnittstelle | Immutable approved version (new version instead of change). | `collection/collectionData` |
| `@auditcore/bpmn-flowaudit` | `AuditFinding` | Schnittstelle | – | `schema/types` |
| `@auditcore/bpmn-flowaudit` | `AuditReference` | Schnittstelle | Reference to key requirement (KA) and assessment criterion (BK). | `schema/types` |
| `@auditcore/bpmn-flowaudit` | `AuditStep` | Schnittstelle | Walk-through or control test step. | `schema/types` |
| `@auditcore/bpmn-flowaudit` | `Bounds` | Schnittstelle | – | `model/processModel` |
| `@auditcore/bpmn-flowaudit` | `CHECKLIST_ITEM` | Konstante | – | `enrichment/textPatterns` |
| `@auditcore/bpmn-flowaudit` | `CODE_ATTRIBUTES` | Konstante | flowaudit attributes that are codes, never cleaned. | `neutralize/patterns` |
| `@auditcore/bpmn-flowaudit` | `COLLECTION_SCHEMA` | Konstante | – | `collection/collectionData` |
| `@auditcore/bpmn-flowaudit` | `COLOR_MARKERS` | Konstante | Colour pair (fill, stroke) → marker suggestion. | `enrichment/suggestions` |
| `@auditcore/bpmn-flowaudit` | `COLOR_PICKER_EVENT` | Konstante | – | `diagram/colorContextPad` |
| `@auditcore/bpmn-flowaudit` | `CONFIDENTIALITY` | Konstante | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `CONTROL_TYPES` | Konstante | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `CRITERIA` | Konstante | – | `enrichment/textPatterns` |
| `@auditcore/bpmn-flowaudit` | `CRITERION_SHORT` | Konstante | – | `enrichment/textPatterns` |
| `@auditcore/bpmn-flowaudit` | `CROSS_REFERENCE_KINDS` | Konstante | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `Canvas` | Schnittstelle | – | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `CatalogueBlock` | Schnittstelle | – | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `CataloguePort` | Schnittstelle | KA/BK catalogue. The application supplies the texts (e.g. of the Methodological Note); without a port the key requirements of the profile apply. | `ports` |
| `@auditcore/bpmn-flowaudit` | `CategorySuggestion` | Schnittstelle | – | `reports/categorySuggestion` |
| `@auditcore/bpmn-flowaudit` | `Change` | Schnittstelle | – | `compare/compare` |
| `@auditcore/bpmn-flowaudit` | `ChangeKind` | Typ | – | `compare/compare` |
| `@auditcore/bpmn-flowaudit` | `CitationForm` | Typ | – | `enrichment/citations` |
| `@auditcore/bpmn-flowaudit` | `CitationHit` | Schnittstelle | – | `enrichment/citations` |
| `@auditcore/bpmn-flowaudit` | `CollectionData` | Schnittstelle | – | `collection/collectionData` |
| `@auditcore/bpmn-flowaudit` | `CollectionError` | Klasse | – | `collection/collection` |
| `@auditcore/bpmn-flowaudit` | `ColorContextPadProvider` | Klasse | – | `diagram/colorContextPad` |
| `@auditcore/bpmn-flowaudit` | `Columns` | Typ | – | `reports/tables` |
| `@auditcore/bpmn-flowaudit` | `CommandStack` | Schnittstelle | – | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `Comment` | Schnittstelle | Comment at an element (as `BpmnComment` in the audit_designer). | `ports` |
| `@auditcore/bpmn-flowaudit` | `Comparison` | Schnittstelle | – | `compare/compare` |
| `@auditcore/bpmn-flowaudit` | `ContextPad` | Schnittstelle | – | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `ContextPadEntry` | Schnittstelle | – | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `Control` | Schnittstelle | – | `schema/types` |
| `@auditcore/bpmn-flowaudit` | `Create` | Schnittstelle | – | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `CriterionData` | Schnittstelle | – | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `CrossReference` | Schnittstelle | Stable domain key towards checklists and notes (`prueffeld`, `feststellung_ref`, `register`). | `schema/types` |
| `@auditcore/bpmn-flowaudit` | `CustomRoleData` | Schnittstelle | – | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `DEADLINE_UNITS` | Konstante | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `DEFAULT_EXPORT_CHOICE` | Konstante | – | `export/exportTypes` |
| `@auditcore/bpmn-flowaudit` | `DEFAULT_HEADER_COLOR` | Konstante | – | `model/diagramInfo` |
| `@auditcore/bpmn-flowaudit` | `DEFAULT_HEADER_TEXT_COLOR` | Konstante | – | `model/diagramInfo` |
| `@auditcore/bpmn-flowaudit` | `DEFAULT_PAGE_FORMAT` | Konstante | – | `layout/pageFormats` |
| `@auditcore/bpmn-flowaudit` | `DEFAULT_PROFILE` | Konstante | – | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `DIAGRAM_STATUS` | Konstante | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `DIFF_COLORS` | Konstante | – | `compare/compare` |
| `@auditcore/bpmn-flowaudit` | `Deadline` | Schnittstelle | – | `schema/types` |
| `@auditcore/bpmn-flowaudit` | `DecorationConfig` | Schnittstelle | – | `diagram/decorations` |
| `@auditcore/bpmn-flowaudit` | `DecorationVisibility` | Schnittstelle | – | `diagram/decorations` |
| `@auditcore/bpmn-flowaudit` | `DiagramCollection` | Klasse | – | `collection/collection` |
| `@auditcore/bpmn-flowaudit` | `DiagramElement` | Schnittstelle | – | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `DiagramEntry` | Schnittstelle | – | `collection/collectionData` |
| `@auditcore/bpmn-flowaudit` | `DiagramExcerpt` | Schnittstelle | Data derived from the XML (never maintained by hand). | `collection/collectionData` |
| `@auditcore/bpmn-flowaudit` | `DiagramInfo` | Schnittstelle | – | `schema/types` |
| `@auditcore/bpmn-flowaudit` | `DiagramReference` | Schnittstelle | – | `collection/analysis` |
| `@auditcore/bpmn-flowaudit` | `DiagramStatus` | Typ | – | `schema/types` |
| `@auditcore/bpmn-flowaudit` | `Direction` | Typ | – | `layout/flowDirection` |
| `@auditcore/bpmn-flowaudit` | `EMPTY_DIAGRAM` | Konstante | Empty diagram as in the audit_designer (`EMPTY_BPMN_XML`). | `model/load` |
| `@auditcore/bpmn-flowaudit` | `EXECUTION_MODES` | Konstante | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `EXTENSION_FIELDS` | Konstante | Mapping of `Extensions` keys to XML names (declarative, used both ways). | `model/extensions` |
| `@auditcore/bpmn-flowaudit` | `EditorServices` | Schnittstelle | Minimal editor surface used by the FlowAudit helpers. | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `ElementActor` | Schnittstelle | – | `model/processModel` |
| `@auditcore/bpmn-flowaudit` | `ElementFactory` | Schnittstelle | – | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `ElementRegistry` | Schnittstelle | – | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `EsiElementGroup` | Schnittstelle | – | `esi/esiRequirements` |
| `@auditcore/bpmn-flowaudit` | `EsiPort` | Schnittstelle | ESI requirements per element (audit_designer endpoint `/esi-requirements`). Any of the supported response shapes is accepted (`normalizeEsiResponse`). | `ports` |
| `@auditcore/bpmn-flowaudit` | `EsiRequirement` | Schnittstelle | – | `schema/types` |
| `@auditcore/bpmn-flowaudit` | `EsiRequirementResult` | Schnittstelle | – | `esi/esiRequirements` |
| `@auditcore/bpmn-flowaudit` | `EsiRequirements` | Schnittstelle | – | `schema/types` |
| `@auditcore/bpmn-flowaudit` | `EsiStatus` | Typ | ESI requirements per BPMN element, ported from `useEsiRequirements.ts` of the audit_designer: accepts several plausible response shapes (array, map by element, `{ requirements }`, … | `esi/esiRequirements` |
| `@auditcore/bpmn-flowaudit` | `EventBus` | Schnittstelle | – | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `EventCallback` | Typ | – | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `Evidence` | Schnittstelle | Audit trail evidence at data objects and data stores. | `schema/types` |
| `@auditcore/bpmn-flowaudit` | `ExportChoice` | Schnittstelle | – | `export/exportTypes` |
| `@auditcore/bpmn-flowaudit` | `ExportData` | Schnittstelle | – | `export/exportData` |
| `@auditcore/bpmn-flowaudit` | `ExportFormat` | Typ | – | `export/exportTypes` |
| `@auditcore/bpmn-flowaudit` | `Extensions` | Schnittstelle | All FlowAudit data at one BPMN element (`Erweiterungen` in auditcore_bpmn). | `schema/types` |
| `@auditcore/bpmn-flowaudit` | `FINDINGS` | Konstante | – | `enrichment/textPatterns` |
| `@auditcore/bpmn-flowaudit` | `FINDING_COLORS` | Konstante | Fill/stroke values of finding colours. | `neutralize/patterns` |
| `@auditcore/bpmn-flowaudit` | `FINDING_MARKERS` | Konstante | Markers that express a finding. | `neutralize/patterns` |
| `@auditcore/bpmn-flowaudit` | `FINDING_SEVERITIES` | Konstante | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `FINDING_STATUS` | Konstante | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `FINDING_TYPES` | Konstante | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `FLOWAUDIT_NAMESPACE` | Konstante | – | `schema/descriptor` |
| `@auditcore/bpmn-flowaudit` | `FLOWAUDIT_PREFIX` | Konstante | – | `schema/descriptor` |
| `@auditcore/bpmn-flowaudit` | `FLOWAUDIT_SCHEMA_VERSION` | Konstante | – | `schema/descriptor` |
| `@auditcore/bpmn-flowaudit` | `FLOWSTAT_FIELDS` | Konstante | Canonical attribute and aliases (read, removed on write). | `model/flowstatAttributes` |
| `@auditcore/bpmn-flowaudit` | `FONT` | Konstante | – | `export/svgBlocks` |
| `@auditcore/bpmn-flowaudit` | `FUNCTIONING_CATEGORIES` | Konstante | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `FUNDS` | Konstante | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `FUND_SHORT` | Konstante | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `Features` | Schnittstelle | – | `compare/matching` |
| `@auditcore/bpmn-flowaudit` | `FieldChange` | Schnittstelle | – | `compare/compare` |
| `@auditcore/bpmn-flowaudit` | `FieldKind` | Typ | Declarative description of the FlowAudit schema 1.1. | `schema/spec` |
| `@auditcore/bpmn-flowaudit` | `FieldSpec` | Schnittstelle | – | `schema/spec` |
| `@auditcore/bpmn-flowaudit` | `FlowauditDecorations` | Klasse | – | `diagram/decorations` |
| `@auditcore/bpmn-flowaudit` | `FlowauditHighlight` | Klasse | – | `diagram/highlight` |
| `@auditcore/bpmn-flowaudit` | `FlowauditModuleOptions` | Schnittstelle | – | `diagram/modules` |
| `@auditcore/bpmn-flowaudit` | `FlowstatField` | Typ | – | `model/flowstatAttributes` |
| `@auditcore/bpmn-flowaudit` | `FlowstatTask` | Schnittstelle | – | `model/flowstatAttributes` |
| `@auditcore/bpmn-flowaudit` | `Folder` | Schnittstelle | – | `collection/collectionData` |
| `@auditcore/bpmn-flowaudit` | `FolderNode` | Schnittstelle | – | `collection/collection` |
| `@auditcore/bpmn-flowaudit` | `FooterBlock` | Schnittstelle | A block of the footer area with its height. | `export/svgBlocks` |
| `@auditcore/bpmn-flowaudit` | `GERMAN_SVG_TEXTS` | Konstante | – | `export/svgPostProcessing` |
| `@auditcore/bpmn-flowaudit` | `Group` | Schnittstelle | – | `collection/legacyTree` |
| `@auditcore/bpmn-flowaudit` | `GroupOverview` | Schnittstelle | – | `collection/analysis` |
| `@auditcore/bpmn-flowaudit` | `Grouping` | Typ | Grouping of the diagram list into a collapsible tree, ported from `diagrammBaum.ts` of the audit_designer (`baueGruppen` → `buildGroups`). | `collection/legacyTree` |
| `@auditcore/bpmn-flowaudit` | `HIGHLIGHT_CLASSES` | Konstante | CSS classes per layer and state. | `diagram/highlight` |
| `@auditcore/bpmn-flowaudit` | `Header` | Schnittstelle | – | `model/diagramInfo` |
| `@auditcore/bpmn-flowaudit` | `HighlightLayer` | Typ | – | `diagram/highlight` |
| `@auditcore/bpmn-flowaudit` | `ICONS` | Konstante | – | `icons/icons` |
| `@auditcore/bpmn-flowaudit` | `INTERNAL_SOURCES` | Konstante | Sources that are internal working material. | `neutralize/patterns` |
| `@auditcore/bpmn-flowaudit` | `IconName` | Typ | – | `icons/icons` |
| `@auditcore/bpmn-flowaudit` | `IconShape` | Typ | FlowAudit icon set – drawn from scratch for this project. | `icons/icons` |
| `@auditcore/bpmn-flowaudit` | `InMemoryStorage` | Klasse | – | `ports/inMemory` |
| `@auditcore/bpmn-flowaudit` | `IssueCount` | Schnittstelle | – | `validation/issue` |
| `@auditcore/bpmn-flowaudit` | `KEY_KINDS` | Konstante | Kinds of stable domain keys (checklists and notes link only via these). | `collection/collectionData` |
| `@auditcore/bpmn-flowaudit` | `KeyKind` | Typ | – | `collection/collectionData` |
| `@auditcore/bpmn-flowaudit` | `KeyRequirementData` | Schnittstelle | – | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `KeyRequirementEntry` | Schnittstelle | – | `ports` |
| `@auditcore/bpmn-flowaudit` | `LEGACY_TRANSLATIONS` | Konstante | Translation table of the audit_designer BPMN editor (`deutschTranslate.ts`, `BPMN_UEBERSETZUNGEN`), kept unchanged so strings used by existing extensions keep their German wording. … | `i18n/legacyTranslations` |
| `@auditcore/bpmn-flowaudit` | `LINE_HEIGHT` | Konstante | – | `export/svgBlocks` |
| `@auditcore/bpmn-flowaudit` | `Label` | Typ | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `LegacyDiagram` | Schnittstelle | Record of the audit_designer (`BpmnDiagram`), as far as needed for migration. | `model/diagramInfo` |
| `@auditcore/bpmn-flowaudit` | `LegacyListItem` | Schnittstelle | Fields of a list item as delivered by the audit_designer API. | `collection/legacyTree` |
| `@auditcore/bpmn-flowaudit` | `LegalBasis` | Schnittstelle | TypeScript form of the FlowAudit extensions. Empty values are absent; booleans are `boolean`. Vocabulary codes (e.g. | `schema/types` |
| `@auditcore/bpmn-flowaudit` | `LegalBasisNote` | Schnittstelle | – | `export/svgPostProcessing` |
| `@auditcore/bpmn-flowaudit` | `LegalBasisTemplateData` | Schnittstelle | – | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `LegalSearchHit` | Schnittstelle | – | `ports` |
| `@auditcore/bpmn-flowaudit` | `LegalSearchOptions` | Schnittstelle | – | `ports` |
| `@auditcore/bpmn-flowaudit` | `LegalSearchPort` | Schnittstelle | Search help for legal bases (e.g. from auditcore_legal_sources / EUR-Lex). | `ports` |
| `@auditcore/bpmn-flowaudit` | `ListExtensionKey` | Typ | – | `schema/types` |
| `@auditcore/bpmn-flowaudit` | `ListFilter` | Typ | – | `collection/legacyTree` |
| `@auditcore/bpmn-flowaudit` | `LoadedDefinitions` | Schnittstelle | – | `model/load` |
| `@auditcore/bpmn-flowaudit` | `Locale` | Typ | Controlled vocabularies of schema 1.1 (German and English labels). | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `LocalizedText` | Typ | – | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `MANUAL_REFERENCE` | Konstante | – | `enrichment/textPatterns` |
| `@auditcore/bpmn-flowaudit` | `MARKERS` | Konstante | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `MARKER_COLORS` | Konstante | Colours derived from markers (fill, stroke). | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `MARKER_COLOR_PRECEDENCE` | Konstante | Precedence when several colouring markers sit on one element. | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `MESSAGES` | Konstante | – | `i18n/translate` |
| `@auditcore/bpmn-flowaudit` | `METADATA_TYPES` | Konstante | Element types offering the 1.0 metadata (legal basis, internal note). | `schema/descriptor` |
| `@auditcore/bpmn-flowaudit` | `Marker` | Schnittstelle | – | `schema/types` |
| `@auditcore/bpmn-flowaudit` | `Messages` | Typ | – | `i18n/translate` |
| `@auditcore/bpmn-flowaudit` | `ModdleElement` | Schnittstelle | Structural types for the diagram-js services this package uses. | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `ModdleFactory` | Schnittstelle | – | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `ModdleInstance` | Schnittstelle | – | `model/load` |
| `@auditcore/bpmn-flowaudit` | `ModelAccess` | Schnittstelle | – | `model/access` |
| `@auditcore/bpmn-flowaudit` | `ModelElement` | Schnittstelle | – | `model/processModel` |
| `@auditcore/bpmn-flowaudit` | `Modeling` | Schnittstelle | – | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `MystOptions` | Schnittstelle | – | `export/myst` |
| `@auditcore/bpmn-flowaudit` | `NeutralizationResult` | Schnittstelle | – | `neutralize/neutralize` |
| `@auditcore/bpmn-flowaudit` | `NeutralizeOptions` | Schnittstelle | – | `neutralize/neutralize` |
| `@auditcore/bpmn-flowaudit` | `OTHER_ROLE` | Konstante | Role „other body“ – fallback for unknown codes and own roles. | `schema/roles` |
| `@auditcore/bpmn-flowaudit` | `Orientation` | Typ | – | `layout/pageFormats` |
| `@auditcore/bpmn-flowaudit` | `PAGE_FORMATS` | Konstante | – | `layout/pageFormats` |
| `@auditcore/bpmn-flowaudit` | `PALETTE_COLORS` | Konstante | – | `export/colorPalette` |
| `@auditcore/bpmn-flowaudit` | `PERSON_ATTRIBUTES` | Konstante | Person fields at diagram info. | `neutralize/patterns` |
| `@auditcore/bpmn-flowaudit` | `PROCESS_TABLE_COLUMNS` | Konstante | – | `reports/processReports` |
| `@auditcore/bpmn-flowaudit` | `PROFILE_SCHEMA` | Konstante | – | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `PROGRAMMING_PERIODS` | Konstante | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `PROTECTION_NAMESPACE` | Konstante | – | `model/unknownElements` |
| `@auditcore/bpmn-flowaudit` | `PX_PER_MM` | Konstante | Page formats and page break guides, ported from `seitenformate.ts` of the audit_designer (`seitenMasse` → `pageSize`, `berechneRaster` → `computePageGrid`). | `layout/pageFormats` |
| `@auditcore/bpmn-flowaudit` | `PageFormat` | Schnittstelle | – | `layout/pageFormats` |
| `@auditcore/bpmn-flowaudit` | `PageGrid` | Schnittstelle | – | `layout/pageFormats` |
| `@auditcore/bpmn-flowaudit` | `PageSize` | Schnittstelle | – | `layout/pageFormats` |
| `@auditcore/bpmn-flowaudit` | `Palette` | Schnittstelle | – | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `PaletteColor` | Schnittstelle | Audit-compliant colour palette for BPMN elements, ported from `farbpalette.ts` of the audit_designer. | `export/colorPalette` |
| `@auditcore/bpmn-flowaudit` | `PaletteEntry` | Schnittstelle | – | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `PdfImage` | Schnittstelle | – | `export/pdf` |
| `@auditcore/bpmn-flowaudit` | `PdfOptions` | Schnittstelle | – | `export/pdf` |
| `@auditcore/bpmn-flowaudit` | `Point` | Schnittstelle | – | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `PrepareSvgOptions` | Schnittstelle | – | `export/svgPostProcessing` |
| `@auditcore/bpmn-flowaudit` | `ProcessModel` | Schnittstelle | – | `model/processModel` |
| `@auditcore/bpmn-flowaudit` | `ProfileCataloguePort` | Klasse | KA catalogue from a profile, optionally enriched by criteria texts of the application. | `ports/inMemory` |
| `@auditcore/bpmn-flowaudit` | `ProfileData` | Schnittstelle | – | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `ProfileLegalSearch` | Klasse | Legal search over the frequent legal bases of a profile plus parsing of the typed citation. No network access. | `ports/inMemory` |
| `@auditcore/bpmn-flowaudit` | `ProfilePort` | Schnittstelle | – | `ports` |
| `@auditcore/bpmn-flowaudit` | `ProfileSummary` | Schnittstelle | – | `ports` |
| `@auditcore/bpmn-flowaudit` | `REGISTER` | Konstante | – | `enrichment/textPatterns` |
| `@auditcore/bpmn-flowaudit` | `REMOVED_ELEMENTS` | Konstante | Elements removed completely. | `neutralize/patterns` |
| `@auditcore/bpmn-flowaudit` | `REPORT_SCHEMA` | Konstante | – | `validation/validate` |
| `@auditcore/bpmn-flowaudit` | `RISK_CATEGORIES` | Konstante | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `RISK_LEVELS` | Konstante | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `ROLES` | Konstante | – | `schema/roles` |
| `@auditcore/bpmn-flowaudit` | `ROLE_PREFIX` | Konstante | Role prefix of a task label („Stelle: Antrag prüfen“). | `enrichment/textPatterns` |
| `@auditcore/bpmn-flowaudit` | `RULES` | Konstante | – | `validation/catalog` |
| `@auditcore/bpmn-flowaudit` | `RULESET_VERSION` | Konstante | – | `validation/validate` |
| `@auditcore/bpmn-flowaudit` | `Replacement` | Schnittstelle | – | `neutralize/neutralize` |
| `@auditcore/bpmn-flowaudit` | `ReplacementKind` | Typ | Patterns removed on neutralisation (same list as `auditcore_bpmn`). | `neutralize/patterns` |
| `@auditcore/bpmn-flowaudit` | `Risk` | Schnittstelle | – | `schema/types` |
| `@auditcore/bpmn-flowaudit` | `Role` | Schnittstelle | – | `schema/roles` |
| `@auditcore/bpmn-flowaudit` | `RoleAlias` | Schnittstelle | – | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `RolePaletteProvider` | Klasse | – | `diagram/rolePalette` |
| `@auditcore/bpmn-flowaudit` | `Row` | Typ | Table output formats: CSV (UTF-8, semicolon) and MyST/Markdown pipe tables, same format as `auditcore_bpmn` reports. | `reports/tables` |
| `@auditcore/bpmn-flowaudit` | `Rule` | Schnittstelle | – | `validation/catalog` |
| `@auditcore/bpmn-flowaudit` | `RuleContext` | Klasse | – | `validation/context` |
| `@auditcore/bpmn-flowaudit` | `RuleGroup` | Typ | – | `validation/catalog` |
| `@auditcore/bpmn-flowaudit` | `SEVERITY_LABELS` | Konstante | – | `validation/catalog` |
| `@auditcore/bpmn-flowaudit` | `SOURCE_TYPES` | Konstante | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `STRUCTURE_FIELDS` | Konstante | – | `model/legalBasis` |
| `@auditcore/bpmn-flowaudit` | `SVG_NS` | Konstante | SVG building blocks for the export post-processing: plain shapes and `<text>` only, so the result looks the same in Word, LibreOffice and the browser. | `export/svgBlocks` |
| `@auditcore/bpmn-flowaudit` | `SegregationKind` | Typ | – | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `SegregationRuleData` | Schnittstelle | – | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `Selection` | Schnittstelle | – | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `SelectionData` | Schnittstelle | – | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `ServiceLocator` | Schnittstelle | The `get(name)` accessor of the editor (diagram-js injector). | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `Severity` | Typ | – | `validation/catalog` |
| `@auditcore/bpmn-flowaudit` | `Source` | Schnittstelle | – | `schema/types` |
| `@auditcore/bpmn-flowaudit` | `StaticProfilePort` | Klasse | – | `ports/inMemory` |
| `@auditcore/bpmn-flowaudit` | `StoragePort` | Schnittstelle | Loading and saving of collection, diagrams and approvals – same split as the `Storage` protocol of `auditcore_bpmn`. | `ports` |
| `@auditcore/bpmn-flowaudit` | `Suggestion` | Schnittstelle | – | `enrichment/suggestions` |
| `@auditcore/bpmn-flowaudit` | `SuggestionKind` | Typ | – | `enrichment/suggestions` |
| `@auditcore/bpmn-flowaudit` | `SuggestionOptions` | Schnittstelle | – | `enrichment/suggestions` |
| `@auditcore/bpmn-flowaudit` | `SuggestionOrigin` | Typ | – | `enrichment/suggestions` |
| `@auditcore/bpmn-flowaudit` | `SvgTexts` | Schnittstelle | – | `export/svgPostProcessing` |
| `@auditcore/bpmn-flowaudit` | `SynopsisRow` | Schnittstelle | – | `compare/compare` |
| `@auditcore/bpmn-flowaudit` | `TASK_TYPES` | Konstante | – | `model/processModel` |
| `@auditcore/bpmn-flowaudit` | `TEST_RESULTS` | Konstante | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `TEXT_PATTERNS` | Konstante | – | `neutralize/patterns` |
| `@auditcore/bpmn-flowaudit` | `TEXT_TYPES` | Konstante | Child elements with plain text content; each needs its own moddle type. | `schema/spec` |
| `@auditcore/bpmn-flowaudit` | `TYPES` | Konstante | – | `schema/spec` |
| `@auditcore/bpmn-flowaudit` | `TYPE_INTERNAL_NOTE` | Konstante | – | `schema/descriptor` |
| `@auditcore/bpmn-flowaudit` | `TYPE_LEGAL_BASIS` | Konstante | Type names as in the audit_designer (`flowauditModdle.ts`). | `schema/descriptor` |
| `@auditcore/bpmn-flowaudit` | `Tag` | Schnittstelle | – | `collection/collectionData` |
| `@auditcore/bpmn-flowaudit` | `TargetActualCheck` | Schnittstelle | – | `compare/compare` |
| `@auditcore/bpmn-flowaudit` | `TargetActualResult` | Schnittstelle | – | `compare/compare` |
| `@auditcore/bpmn-flowaudit` | `TemplateData` | Schnittstelle | – | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `TextHit` | Schnittstelle | – | `enrichment/textPatterns` |
| `@auditcore/bpmn-flowaudit` | `TextOptions` | Schnittstelle | – | `export/svgBlocks` |
| `@auditcore/bpmn-flowaudit` | `TextPattern` | Schnittstelle | – | `neutralize/patterns` |
| `@auditcore/bpmn-flowaudit` | `Translate` | Typ | – | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `TreeOptions` | Schnittstelle | – | `collection/legacyTree` |
| `@auditcore/bpmn-flowaudit` | `TypeSpec` | Schnittstelle | – | `schema/spec` |
| `@auditcore/bpmn-flowaudit` | `UnknownElementsGuard` | Klasse | – | `diagram/unknownElementsModule` |
| `@auditcore/bpmn-flowaudit` | `UsedColor` | Schnittstelle | – | `export/svgPostProcessing` |
| `@auditcore/bpmn-flowaudit` | `UsedMarker` | Schnittstelle | – | `export/svgPostProcessing` |
| `@auditcore/bpmn-flowaudit` | `VARIANTS` | Konstante | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `VOCABULARIES` | Konstante | Names of all vocabularies, for panels and validation messages. | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `ValidationIssue` | Schnittstelle | – | `validation/issue` |
| `@auditcore/bpmn-flowaudit` | `ValidationOptions` | Schnittstelle | – | `validation/context` |
| `@auditcore/bpmn-flowaudit` | `ValidationPort` | Schnittstelle | Server-side validation (e.g. `auditcore_bpmn`), optional. | `ports` |
| `@auditcore/bpmn-flowaudit` | `ValidationReport` | Schnittstelle | – | `validation/validate` |
| `@auditcore/bpmn-flowaudit` | `Viewbox` | Schnittstelle | – | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `ViewboxLike` | Schnittstelle | – | `layout/pageFormats` |
| `@auditcore/bpmn-flowaudit` | `Vocabulary` | Typ | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `VocabularyName` | Typ | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `WITHOUT_ASSIGNMENT` | Konstante | – | `collection/legacyTree` |
| `@auditcore/bpmn-flowaudit` | `WRITE_ORDER` | Konstante | Order of FlowAudit children inside `extensionElements` (same as `_REIHENFOLGE` in `auditcore_bpmn.flowaudit`), so both sides write alike. | `schema/spec` |
| `@auditcore/bpmn-flowaudit` | `WalkthroughOverview` | Schnittstelle | – | `reports/processReports` |
| `@auditcore/bpmn-flowaudit` | `WalkthroughProgress` | Schnittstelle | – | `walkthrough/walkthrough` |
| `@auditcore/bpmn-flowaudit` | `WalkthroughStep` | Schnittstelle | – | `walkthrough/walkthrough` |
| `@auditcore/bpmn-flowaudit` | `actLong` | Funktion | Long canonical form of an act name (`VO` → `Verordnung`). | `model/legalBasis` |
| `@auditcore/bpmn-flowaudit` | `actShort` | Funktion | Short form of an act name for display (`Verordnung` → `VO`). | `model/legalBasis` |
| `@auditcore/bpmn-flowaudit` | `activities` | Funktion | – | `model/processModel` |
| `@auditcore/bpmn-flowaudit` | `actorLabel` | Funktion | – | `reports/processReports` |
| `@auditcore/bpmn-flowaudit` | `applyDirection` | Funktion | Applies a direction to the whole diagram; returns the number of pools and lanes. | `layout/flowDirection` |
| `@auditcore/bpmn-flowaudit` | `applySuggestions` | Funktion | Takes over accepted suggestions; existing data stays, duplicates are skipped. | `enrichment/suggestions` |
| `@auditcore/bpmn-flowaudit` | `approve` | Funktion | Records the SHA-256 of an approved version; a version is immutable. | `collection/analysis` |
| `@auditcore/bpmn-flowaudit` | `auditReferenceText` | Funktion | – | `diagram/decorations` |
| `@auditcore/bpmn-flowaudit` | `auditReferencesIn` | Funktion | – | `enrichment/textPatterns` |
| `@auditcore/bpmn-flowaudit` | `base64Utf8` | Funktion | Base64 with correct handling of umlauts (`btoa` only knows Latin-1). | `export/myst` |
| `@auditcore/bpmn-flowaudit` | `bodyLabel` | Funktion | Body of an element for display: role (display name), otherwise lane/pool. | `compare/matching` |
| `@auditcore/bpmn-flowaudit` | `buildGroups` | Funktion | Filters, searches and groups in one pass. | `collection/legacyTree` |
| `@auditcore/bpmn-flowaudit` | `buildMystSnippet` | Funktion | – | `export/myst` |
| `@auditcore/bpmn-flowaudit` | `camelToSnake` | Funktion | – | `model/wire` |
| `@auditcore/bpmn-flowaudit` | `category` | Funktion | – | `compare/matching` |
| `@auditcore/bpmn-flowaudit` | `changeLabel` | Funktion | – | `compare/compare` |
| `@auditcore/bpmn-flowaudit` | `checkCollection` | Funktion | Collection rules (`BPMN-K001`–`K007`). | `collection/analysis` |
| `@auditcore/bpmn-flowaudit` | `checkTargetActual` | Funktion | Per activity, gateway and event of the target: present in the actual state, same body, controls and successors. „Met“ is binary; the reasons name each deviation. | `compare/compare` |
| `@auditcore/bpmn-flowaudit` | `citation` | Funktion | Long citation, e.g. „Artikel 73 Absatz 2 Buchstabe b der Verordnung (EU) 2021/1060“. | `model/legalBasis` |
| `@auditcore/bpmn-flowaudit` | `cleanInfo` | Funktion | Drops empty values, sets the schema version, fills legal basis texts. | `model/diagramInfo` |
| `@auditcore/bpmn-flowaudit` | `collectColors` | Funktion | Counts used colours for the legend. Colours outside the palette are kept but labelled „Nicht zugeordnet“ – dropping them silently would present an incomplete legend as complete. | `export/exportData` |
| `@auditcore/bpmn-flowaudit` | `collectExportData` | Funktion | – | `export/exportData` |
| `@auditcore/bpmn-flowaudit` | `collectLegalBasisNotes` | Funktion | – | `export/exportData` |
| `@auditcore/bpmn-flowaudit` | `collectMarkers` | Funktion | – | `export/exportData` |
| `@auditcore/bpmn-flowaudit` | `collectSuggestions` | Funktion | All suggestions for an unchanged diagram; duplicates per element are dropped. | `enrichment/suggestions` |
| `@auditcore/bpmn-flowaudit` | `colorContextPadModule` | Konstante | – | `diagram/colorContextPad` |
| `@auditcore/bpmn-flowaudit` | `colorFromDi` | Funktion | Reads a colour from the DI (`bioc:` or `color:` namespace). | `model/processModel` |
| `@auditcore/bpmn-flowaudit` | `colorsFromMarkers` | Funktion | Fill and stroke per element from colouring markers (precedence as in the schema). | `compare/compare` |
| `@auditcore/bpmn-flowaudit` | `comparable` | Funktion | – | `compare/matching` |
| `@auditcore/bpmn-flowaudit` | `compareProfileVersions` | Funktion | Compares versions such as `2026.09.1` numerically part by part. | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `compareVersions` | Funktion | Element-wise comparison of two versions of the same diagram. | `compare/compare` |
| `@auditcore/bpmn-flowaudit` | `completeEuAct` | Funktion | Fills missing CELEX/ELI/URL of an EU act; existing values stay. | `enrichment/citations` |
| `@auditcore/bpmn-flowaudit` | `computePageGrid` | Funktion | Computes the page break grid for the current view. The origin is the diagram origin (0/0), so the grid moves with the diagram like a printout. | `layout/pageFormats` |
| `@auditcore/bpmn-flowaudit` | `computeValues` | Funktion | New value list of `extensionElements`: foreign entries first (in their order), then FlowAudit entries in schema order. | `model/extensions` |
| `@auditcore/bpmn-flowaudit` | `copyToClipboard` | Funktion | Puts text on the clipboard. The fallback through a hidden text field is needed because the Clipboard API is only available in secure contexts. | `export/myst` |
| `@auditcore/bpmn-flowaudit` | `countIssues` | Funktion | – | `validation/issue` |
| `@auditcore/bpmn-flowaudit` | `createModdle` | Funktion | – | `model/load` |
| `@auditcore/bpmn-flowaudit` | `createModelElement` | Funktion | – | `model/processModel` |
| `@auditcore/bpmn-flowaudit` | `createTranslator` | Funktion | Creates a translate function. Tables are merged in order: core table (optional), legacy audit_designer table (German only), FlowAudit messages, application overrides. | `i18n/translate` |
| `@auditcore/bpmn-flowaudit` | `criterionKnown` | Funktion | `true`/`false` against the criteria catalogue of the KA; `undefined` if none exists. | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `crossReferencesIn` | Funktion | – | `enrichment/textPatterns` |
| `@auditcore/bpmn-flowaudit` | `deadlineText` | Funktion | – | `reports/processReports` |
| `@auditcore/bpmn-flowaudit` | `decorationsModule` | Konstante | – | `diagram/decorations` |
| `@auditcore/bpmn-flowaudit` | `definitionsOf` | Funktion | Definitions behind the root element of a running editor. | `model/buildModel` |
| `@auditcore/bpmn-flowaudit` | `deriveStatus` | Funktion | – | `esi/esiRequirements` |
| `@auditcore/bpmn-flowaudit` | `diagramLabel` | Funktion | Label for the book: lower case, without blanks and special characters. | `export/myst` |
| `@auditcore/bpmn-flowaudit` | `diagramReferences` | Funktion | Calls (call activity → process) and link events across diagram boundaries. | `collection/analysis` |
| `@auditcore/bpmn-flowaudit` | `diffColors` | Funktion | Colours for the graphical diff: `[before, after]` by element id. | `compare/compare` |
| `@auditcore/bpmn-flowaudit` | `displayName` | Funktion | – | `model/processModel` |
| `@auditcore/bpmn-flowaudit` | `displayText` | Funktion | Readable text: free text, otherwise short citation. | `model/legalBasis` |
| `@auditcore/bpmn-flowaudit` | `download` | Funktion | File output for the image formats, ported from `bildExport.ts` of the audit_designer (`ladeHerunter` → `download`, `dateiname` → `fileName`, `svgNachPng` → `svgToPng`). | `export/imageExport` |
| `@auditcore/bpmn-flowaudit` | `editorAccess` | Funktion | – | `model/access` |
| `@auditcore/bpmn-flowaudit` | `editorServices` | Funktion | – | `diagram/services` |
| `@auditcore/bpmn-flowaudit` | `elementsForKey` | Funktion | Element ids of the diagram model matching a key (for highlighting). | `collection/excerpt` |
| `@auditcore/bpmn-flowaudit` | `emptyCollection` | Funktion | – | `collection/collectionData` |
| `@auditcore/bpmn-flowaudit` | `emptyExcerpt` | Funktion | – | `collection/collectionData` |
| `@auditcore/bpmn-flowaudit` | `emptyExtensions` | Funktion | – | `schema/types` |
| `@auditcore/bpmn-flowaudit` | `euAct` | Funktion | `[eliKind, year, number]` of an EU act, or `null`. | `enrichment/citations` |
| `@auditcore/bpmn-flowaudit` | `excerptFromModel` | Funktion | – | `collection/excerpt` |
| `@auditcore/bpmn-flowaudit` | `extensionValues` | Funktion | All values of `extensionElements` (empty list if there are none). | `model/extensions` |
| `@auditcore/bpmn-flowaudit` | `features` | Funktion | – | `compare/matching` |
| `@auditcore/bpmn-flowaudit` | `fileName` | Funktion | File name without blanks and special characters. | `export/imageExport` |
| `@auditcore/bpmn-flowaudit` | `fillPlaceholders` | Funktion | – | `i18n/translate` |
| `@auditcore/bpmn-flowaudit` | `findCitations` | Funktion | Finds legal citations in free text (e.g. `bpmn:documentation`), without overlaps. | `enrichment/citations` |
| `@auditcore/bpmn-flowaudit` | `findPaletteColor` | Funktion | – | `export/colorPalette` |
| `@auditcore/bpmn-flowaudit` | `findingsList` | Funktion | – | `reports/processReports` |
| `@auditcore/bpmn-flowaudit` | `flowOrder` | Funktion | Flow nodes in flow order (breadth-first from start events), rest afterwards. | `reports/processReports` |
| `@auditcore/bpmn-flowaudit` | `flowauditEditorOptions` | Funktion | Everything the editor needs: modules, moddle extension and module config. | `diagram/modules` |
| `@auditcore/bpmn-flowaudit` | `flowauditModdleDescriptor` | Konstante | For `moddleExtensions: { flowaudit: flowauditModdleDescriptor }`. | `schema/descriptor` |
| `@auditcore/bpmn-flowaudit` | `flowauditModules` | Funktion | – | `diagram/modules` |
| `@auditcore/bpmn-flowaudit` | `forWriting` | Funktion | Prepares a legal basis for writing: text content is mandatory (1.0 readers show it). Existing free text is never overwritten. | `model/legalBasis` |
| `@auditcore/bpmn-flowaudit` | `fromModdle` | Funktion | moddle element → TypeScript object (empty values are dropped). | `model/moddleMapping` |
| `@auditcore/bpmn-flowaudit` | `fromWire` | Funktion | JSON of `auditcore_bpmn` → TypeScript object (camelCase keys). | `model/wire` |
| `@auditcore/bpmn-flowaudit` | `germanTranslate` | Konstante | Legacy API: German translation (`deutschTranslate`). | `i18n/translate` |
| `@auditcore/bpmn-flowaudit` | `groupByElement` | Funktion | – | `esi/esiRequirements` |
| `@auditcore/bpmn-flowaudit` | `groupOverview` | Funktion | Overview of a group (folder, recursive) or a tag. | `collection/analysis` |
| `@auditcore/bpmn-flowaudit` | `hasIcon` | Funktion | – | `icons/icons` |
| `@auditcore/bpmn-flowaudit` | `headerOf` | Funktion | – | `model/diagramInfo` |
| `@auditcore/bpmn-flowaudit` | `headlessAccess` | Funktion | – | `model/access` |
| `@auditcore/bpmn-flowaudit` | `highlightModule` | Konstante | – | `diagram/highlight` |
| `@auditcore/bpmn-flowaudit` | `iconElement` | Funktion | Icon as SVG element inside an existing SVG (diagram decorations). | `icons/icons` |
| `@auditcore/bpmn-flowaudit` | `iconPrimitives` | Funktion | Primitive shapes of an icon as `[tag, attributes]` (for Vue render functions). | `icons/icons` |
| `@auditcore/bpmn-flowaudit` | `iconSvg` | Funktion | SVG markup of an icon (e.g. for CSS data URIs or `innerHTML`). | `icons/icons` |
| `@auditcore/bpmn-flowaudit` | `idFromName` | Funktion | Creates a readable, valid id from a name („Antragsverfahren 2“ → `antragsverfahren-2`). | `collection/collectionData` |
| `@auditcore/bpmn-flowaudit` | `imageToPdf` | Funktion | Builds a one-page PDF with the image centred and fitted into the margins. | `export/pdf` |
| `@auditcore/bpmn-flowaudit` | `infoFromLegacy` | Funktion | Migrates the legacy columns into diagram info. Data present in the XML wins – the XML is the authoritative source. | `model/diagramInfo` |
| `@auditcore/bpmn-flowaudit` | `isActivity` | Funktion | – | `model/processModel` |
| `@auditcore/bpmn-flowaudit` | `isColorable` | Funktion | Elements without meaningful colour (root, labels). | `diagram/colorContextPad` |
| `@auditcore/bpmn-flowaudit` | `isEvent` | Funktion | – | `model/processModel` |
| `@auditcore/bpmn-flowaudit` | `isFlowNode` | Funktion | – | `model/processModel` |
| `@auditcore/bpmn-flowaudit` | `isFlowauditElement` | Funktion | – | `model/moddleMapping` |
| `@auditcore/bpmn-flowaudit` | `isGateway` | Funktion | – | `model/processModel` |
| `@auditcore/bpmn-flowaudit` | `isStructured` | Funktion | – | `model/legalBasis` |
| `@auditcore/bpmn-flowaudit` | `isTask` | Funktion | – | `model/processModel` |
| `@auditcore/bpmn-flowaudit` | `isUnchanged` | Funktion | – | `compare/compare` |
| `@auditcore/bpmn-flowaudit` | `isValidId` | Funktion | – | `collection/collectionData` |
| `@auditcore/bpmn-flowaudit` | `issue` | Funktion | – | `validation/issue` |
| `@auditcore/bpmn-flowaudit` | `issueFromWire` | Funktion | Converts a server issue of `auditcore_bpmn` (`rule_id`, `severity`, `params`, …) into a `ValidationIssue`. | `validation/issue` |
| `@auditcore/bpmn-flowaudit` | `issueMessage` | Funktion | – | `validation/issue` |
| `@auditcore/bpmn-flowaudit` | `keepDirection` | Funktion | Keeps newly created pools on the chosen direction; returns an unsubscribe function. | `layout/flowDirection` |
| `@auditcore/bpmn-flowaudit` | `keyRequirement` | Funktion | – | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `keyRequirements` | Funktion | – | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `label` | Funktion | – | `schema/vocabulary` |
| `@auditcore/bpmn-flowaudit` | `latestProfiles` | Funktion | Latest version per profile id. | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `legacyFromInfo` | Funktion | Diagram info back into the legacy columns (for applications in transition). | `model/diagramInfo` |
| `@auditcore/bpmn-flowaudit` | `legalBasisKey` | Funktion | Key for duplicate detection (structured fields or text). | `model/legalBasis` |
| `@auditcore/bpmn-flowaudit` | `loadDefinitions` | Funktion | – | `model/load` |
| `@auditcore/bpmn-flowaudit` | `localType` | Funktion | `bpmn:UserTask` → `userTask`. | `model/processModel` |
| `@auditcore/bpmn-flowaudit` | `localXmlName` | Funktion | Local XML name of a flowaudit moddle element, e.g. `kennzeichen`. | `model/moddleMapping` |
| `@auditcore/bpmn-flowaudit` | `localized` | Funktion | – | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `mainElement` | Funktion | Main element: the collaboration, otherwise the first process. | `model/buildModel` |
| `@auditcore/bpmn-flowaudit` | `matchElements` | Funktion | Element id old → element id new. | `compare/matching` |
| `@auditcore/bpmn-flowaudit` | `modelFromDefinitions` | Funktion | Builds the model from moddle definitions (headless). | `model/buildModel` |
| `@auditcore/bpmn-flowaudit` | `modelFromEditor` | Funktion | Builds the model from a running editor, using the current shape bounds. | `model/buildModel` |
| `@auditcore/bpmn-flowaudit` | `neighbours` | Funktion | – | `compare/matching` |
| `@auditcore/bpmn-flowaudit` | `neutralize` | Funktion | Neutralises a diagram; `replacements` adds names known to the application. | `neutralize/neutralize` |
| `@auditcore/bpmn-flowaudit` | `nextStepId` | Funktion | Next id for an audit step (`PS1`, `PS2`, …) unique across the diagram. | `walkthrough/walkthrough` |
| `@auditcore/bpmn-flowaudit` | `normalName` | Funktion | – | `compare/matching` |
| `@auditcore/bpmn-flowaudit` | `normalizeColor` | Funktion | Compares colour values tolerant of case and short form (`#abc`). | `export/colorPalette` |
| `@auditcore/bpmn-flowaudit` | `normalizeEsiResponse` | Funktion | Flat list from any of the supported response shapes. | `esi/esiRequirements` |
| `@auditcore/bpmn-flowaudit` | `normalizeRequirement` | Funktion | – | `esi/esiRequirements` |
| `@auditcore/bpmn-flowaudit` | `normalized` | Funktion | Act in long form and text content as long citation. | `model/legalBasis` |
| `@auditcore/bpmn-flowaudit` | `pageSize` | Funktion | Page size in diagram pixels, including orientation. | `layout/pageFormats` |
| `@auditcore/bpmn-flowaudit` | `parseCitation` | Funktion | Reads a single citation; without a hit it stays free text. | `enrichment/citations` |
| `@auditcore/bpmn-flowaudit` | `pdfString` | Funktion | Escapes text for a PDF string literal (Latin-1 range only; others become „?“). | `export/pdf` |
| `@auditcore/bpmn-flowaudit` | `periodStart` | Funktion | Start year from `YYYY-YYYY`, otherwise `null`. | `schema/roles` |
| `@auditcore/bpmn-flowaudit` | `pixelsToMm` | Funktion | Diagram pixels → millimetres at 96 dpi (for choosing the page format). | `export/pdf` |
| `@auditcore/bpmn-flowaudit` | `prepareSvg` | Funktion | Adds header, legends and directory of legal bases to the exported SVG. | `export/svgPostProcessing` |
| `@auditcore/bpmn-flowaudit` | `processTable` | Funktion | Process description in flow order. | `reports/processReports` |
| `@auditcore/bpmn-flowaudit` | `profileReference` | Funktion | – | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `protectUnknownElements` | Funktion | – | `model/unknownElements` |
| `@auditcore/bpmn-flowaudit` | `readDiagramInfo` | Funktion | Diagram info: collaboration first, then processes in document order. | `model/buildModel` |
| `@auditcore/bpmn-flowaudit` | `readDiagramInfoFromEditor` | Funktion | Editor: reads the diagram info (collaboration, otherwise first process). | `model/diagramInfo` |
| `@auditcore/bpmn-flowaudit` | `readExtensions` | Funktion | Reads all FlowAudit data of a business object. | `model/extensions` |
| `@auditcore/bpmn-flowaudit` | `readFlowstatValues` | Funktion | – | `model/flowstatAttributes` |
| `@auditcore/bpmn-flowaudit` | `readMetadata` | Funktion | Reads the text value of a flowaudit entry; '' if not maintained. | `model/legacyMetadata` |
| `@auditcore/bpmn-flowaudit` | `readSvgSize` | Funktion | – | `export/imageExport` |
| `@auditcore/bpmn-flowaudit` | `readTasksFromXml` | Funktion | – | `model/flowstatAttributes` |
| `@auditcore/bpmn-flowaudit` | `recordStep` | Funktion | Records or replaces an audit step at an element. | `walkthrough/walkthrough` |
| `@auditcore/bpmn-flowaudit` | `removeRolePrefix` | Funktion | „Stelle: Antrag prüfen“ → „Antrag prüfen“. | `enrichment/textPatterns` |
| `@auditcore/bpmn-flowaudit` | `removeStep` | Funktion | – | `walkthrough/walkthrough` |
| `@auditcore/bpmn-flowaudit` | `reportToWire` | Funktion | Report as JSON of `auditcore_bpmn` (`validation-report-1.schema.json`). | `validation/validate` |
| `@auditcore/bpmn-flowaudit` | `restoreUnknownElements` | Funktion | – | `model/unknownElements` |
| `@auditcore/bpmn-flowaudit` | `riskControlMatrix` | Funktion | One row per risk and linked control (risks without control once). | `reports/processReports` |
| `@auditcore/bpmn-flowaudit` | `roleAppliesTo` | Funktion | `true` if the role exists in the programming period (unknown period: yes). | `schema/roles` |
| `@auditcore/bpmn-flowaudit` | `roleFromText` | Funktion | Role from a lane name or task prefix via the alias list (first hit, case insensitive). Additional aliases – e.g. names of bodies in a programme – are supplied by the application. | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `roleOf` | Funktion | Role by code (own roles of the profile win). | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `rolePaletteModule` | Konstante | – | `diagram/rolePalette` |
| `@auditcore/bpmn-flowaudit` | `roleProvided` | Funktion | – | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `rolesFor` | Funktion | Roles of the profile, filtered by programming period (no profile: full catalogue). | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `ruleText` | Funktion | Message of a rule; parameters `name_de`/`name_en` override `name`. | `validation/catalog` |
| `@auditcore/bpmn-flowaudit` | `saveDefinitions` | Funktion | – | `model/load` |
| `@auditcore/bpmn-flowaudit` | `setColor` | Funktion | Sets a palette colour; `null` removes the colouring. | `diagram/colorContextPad` |
| `@auditcore/bpmn-flowaudit` | `setDiagramInfo` | Funktion | Headless: sets the diagram info at the main element. | `model/diagramInfo` |
| `@auditcore/bpmn-flowaudit` | `setExtensionsDirect` | Funktion | Like `writeExtensions`, but mutates the model directly (headless). | `model/extensions` |
| `@auditcore/bpmn-flowaudit` | `severityLabel` | Funktion | – | `validation/issue` |
| `@auditcore/bpmn-flowaudit` | `sha256Xml` | Funktion | SHA-256 over the UTF-8 bytes of the XML exactly as stored (hex). | `collection/analysis` |
| `@auditcore/bpmn-flowaudit` | `shortCitation` | Funktion | Short citation for display, e.g. „Art. 73 Abs. 2 Buchst. b VO (EU) 2021/1060“. | `model/legalBasis` |
| `@auditcore/bpmn-flowaudit` | `snakeToCamel` | Funktion | – | `model/wire` |
| `@auditcore/bpmn-flowaudit` | `sortIssues` | Funktion | – | `validation/issue` |
| `@auditcore/bpmn-flowaudit` | `sourcesIn` | Funktion | – | `enrichment/textPatterns` |
| `@auditcore/bpmn-flowaudit` | `splitFreeText` | Funktion | Splits a 1.0 free text with several acts („§ 55 BHO; Art. 74 VO (EU) 2021/1060“). | `model/legalBasis` |
| `@auditcore/bpmn-flowaudit` | `splitList` | Funktion | – | `enrichment/textPatterns` |
| `@auditcore/bpmn-flowaudit` | `suggestCategories` | Funktion | – | `reports/categorySuggestion` |
| `@auditcore/bpmn-flowaudit` | `summarize` | Funktion | – | `esi/esiRequirements` |
| `@auditcore/bpmn-flowaudit` | `svgGroup` | Funktion | – | `export/svgBlocks` |
| `@auditcore/bpmn-flowaudit` | `svgRect` | Funktion | – | `export/svgBlocks` |
| `@auditcore/bpmn-flowaudit` | `svgText` | Funktion | – | `export/svgBlocks` |
| `@auditcore/bpmn-flowaudit` | `svgToCanvas` | Funktion | Paints an SVG onto a canvas with white ground. `scale` 2 ≈ 192 dpi. | `export/imageExport` |
| `@auditcore/bpmn-flowaudit` | `svgToJpeg` | Funktion | – | `export/imageExport` |
| `@auditcore/bpmn-flowaudit` | `svgToPng` | Funktion | – | `export/imageExport` |
| `@auditcore/bpmn-flowaudit` | `synopsis` | Funktion | Rows „element \| before \| after \| change“ for reports. | `compare/compare` |
| `@auditcore/bpmn-flowaudit` | `targetActualPairs` | Funktion | `[actualId, targetId]` of all linked actual-state diagrams. | `collection/analysis` |
| `@auditcore/bpmn-flowaudit` | `textSuggestions` | Funktion | – | `enrichment/suggestions` |
| `@auditcore/bpmn-flowaudit` | `toCsv` | Funktion | CSV with header from `columns` (or the keys); `bom` for Excel. | `reports/tables` |
| `@auditcore/bpmn-flowaudit` | `toModdle` | Funktion | TypeScript object → new moddle element (empty values are dropped). | `model/moddleMapping` |
| `@auditcore/bpmn-flowaudit` | `toMyst` | Funktion | Table as MyST Markdown, optionally with heading and target label. | `reports/tables` |
| `@auditcore/bpmn-flowaudit` | `toWire` | Funktion | TypeScript object → JSON for `auditcore_bpmn` (snake_case keys). | `model/wire` |
| `@auditcore/bpmn-flowaudit` | `today` | Funktion | – | `validation/context` |
| `@auditcore/bpmn-flowaudit` | `translateModule` | Funktion | diagram-js module replacing `translate` (legacy `deutschModul`). | `i18n/translate` |
| `@auditcore/bpmn-flowaudit` | `typeByModdleName` | Funktion | – | `schema/spec` |
| `@auditcore/bpmn-flowaudit` | `unknownElementsModule` | Konstante | – | `diagram/unknownElementsModule` |
| `@auditcore/bpmn-flowaudit` | `validateModel` | Funktion | – | `validation/validate` |
| `@auditcore/bpmn-flowaudit` | `validateProfile` | Funktion | – | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `valueText` | Funktion | – | `compare/compare` |
| `@auditcore/bpmn-flowaudit` | `verifyApproval` | Funktion | `null` if the XML equals the approved version, otherwise `BPMN-K008`. | `collection/analysis` |
| `@auditcore/bpmn-flowaudit` | `walkthroughOverview` | Funktion | Audit steps per flow node; activities without steps separately. | `reports/processReports` |
| `@auditcore/bpmn-flowaudit` | `walkthroughProgress` | Funktion | – | `walkthrough/walkthrough` |
| `@auditcore/bpmn-flowaudit` | `walkthroughSteps` | Funktion | Steps of the walk-through in flow order: activities and gateways. | `walkthrough/walkthrough` |
| `@auditcore/bpmn-flowaudit` | `withCriteria` | Funktion | Profile with injected assessment criteria (e.g. from a catalogue port). | `profile/profile` |
| `@auditcore/bpmn-flowaudit` | `wrapWords` | Funktion | Rough word wrap to a number of characters (SVG has no text measure). | `export/svgBlocks` |
| `@auditcore/bpmn-flowaudit` | `writeDiagramInfo` | Funktion | Editor: writes the diagram info through `modeling` (one undo step). | `model/diagramInfo` |
| `@auditcore/bpmn-flowaudit` | `writeExtensions` | Funktion | Writes part of the extensions through `modeling` (one undo step). When the last entry disappears, `extensionElements` is removed as well. | `model/extensions` |
| `@auditcore/bpmn-flowaudit` | `writeFlowstatValues` | Funktion | Writes FlowStat fields canonically through `modeling.updateProperties`. | `model/flowstatAttributes` |
| `@auditcore/bpmn-flowaudit` | `writeMetadata` | Funktion | Writes (or removes) a flowaudit text entry. | `model/legacyMetadata` |
| `@auditcore/bpmn-flowaudit` | `writeTaskToXml` | Funktion | Writes one task back; returns the new XML, or the old one if nothing matches. | `model/flowstatAttributes` |
<!-- api-overview:end -->

## Konfiguration

Profile (`@auditcore/bpmn-flowaudit/profiles`, `defaultProfile()`) bündeln
Regeln, Schlüssel und Vorgaben. Anwendungsspezifisches ist nicht eingebaut:
Rollen-Aliasse, Profile und Ersetzungen für die Neutralisierung liefert die
Anwendung. Ports: `StoragePort`, `LegalSearchPort`, `CataloguePort`,
`ProfilePort`, `ValidationPort`, `EsiPort`; für Demo und Tests
`InMemoryStorage`, `StaticProfilePort`, `ProfileCataloguePort`,
`ProfileLegalSearch`.

## Herkunft und Charakterisierung

Neuimplementierung im Clean-Room; portiert wurde nur FlowAudit-eigener Code aus
dem audit_designer (Paritätsinventar `docs/bpmn/paritaet-audit-designer.md`).
Der Prüfregel-Katalog ist derselbe wie in `auditcore_bpmn`.

## Abhängigkeiten

`bpmn-moddle@^10.3.1`; optionaler Peer `@auditcore/bpmn-editor@^0.1.0` (nur für
die Editor-Module).

## Sicherheit und Datenschutz

Kein Netz- und kein Datenbankzugriff; Daten kommen nur über die vom Consumer
gelieferten Ports. Diagramme können Namen von Stellen und Personen enthalten –
`neutralize` ersetzt sie nach den Ersetzungen der Anwendung, bevor Diagramme
weitergegeben werden. Freigaben werden mit SHA-256 festgehalten; das ersetzt
keine fachliche Freigabe.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Clean-Room-Erklärung: Dieses Paket enthält keinen Code,
keine Styles und keine Icons aus bpmn-js, bpmn-js-properties-panel,
@bpmn-io/properties-panel oder bpmn-font. Genutzt werden nur diagram-js und
bpmn-moddle (MIT) über den eigenen Kern `@auditcore/bpmn-editor`. Portiert
wurde ausschließlich FlowAudit-eigener Code aus dem audit_designer
(Paritätsinventar: `docs/bpmn/paritaet-audit-designer.md`). Die Icons sind
eigene SVG-Pfade (24 px, `currentColor`).

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
