# @flowaudit/bpmn-flowaudit

## Zweck

Framework-freie FlowAudit-Fachschicht für den BPMN-Editor: Schema flowaudit 1.0/1.1, Rollen, Kennzeichen, Prüfbezüge, Prüfregeln, Anreicherung, Neutralisierung, Vergleiche, Durchlauftest, Berichte und Export.

Für Anwendungen, die BPMN-Prozesse der Verwaltungs- und Kontrollsysteme
modellieren und prüfen – mit `@flowaudit/bpmn-vue` als Oberfläche oder ohne.
Kein Netz- oder Datenbankzugriff: Speicher, Rechtsgrundlagen-Suche,
KA/BK-Texte, Profile und Serverprüfung kommen über Ports herein.

## Installation

Standardweg ist die npm-Registry; npm löst die übrigen `@flowaudit`-Pakete
der Abhängigkeitshülle selbst auf:

```sh
npm install @flowaudit/bpmn-flowaudit
```

Ohne Registry-Zugang (Intranet, offline) bleibt der signierte Tarball aus
dem GitHub-Release von auditcore; dann gehört jedes Paket der Hülle
ausdrücklich in die `package.json`:

```sh
npm install @flowaudit/bpmn-flowaudit@https://github.com/janpow77/auditcore/releases/download/v<release>/flowaudit-bpmn-flowaudit-0.2.1.tgz
```

Anleitung für Vue, React und Web Components mit Integritätsprüfung und
`vendor/`-Ablage:
[frontend-installation.md](../../docs/deployment/frontend-installation.md).

Für die Editor-Module (`flowauditEditorOptions()`) zusätzlich `@flowaudit/bpmn-editor` (optionale Peer-Abhängigkeit). Stile: `@flowaudit/bpmn-flowaudit/style.css`.

Im auditcore-Repository gehört das Paket zum npm-Workspace (`npm ci` im
Stamm, Bau mit `npm run build -w @flowaudit/bpmn-flowaudit`).

## Schnellstart

Modell lesen und mit dem Standardprofil prüfen (läuft in Node, ohne DOM):

```ts run
import { loadDefinitions, modelFromDefinitions, validateModel } from '@flowaudit/bpmn-flowaudit'
import { defaultProfile } from '@flowaudit/bpmn-flowaudit/profiles'

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
import { collectSuggestions, loadDefinitions, modelFromDefinitions, neutralize } from '@flowaudit/bpmn-flowaudit'
import { defaultProfile } from '@flowaudit/bpmn-flowaudit/profiles'

declare const xml: string
const model = modelFromDefinitions((await loadDefinitions(xml)).definitions)
const suggestions = collectSuggestions(model, { profile: defaultProfile() })
const { xml: neutral, replacements } = neutralize(xml, { profile: defaultProfile() })
```

## Einbindung

Framework-frei; im Editorkern: `flowauditEditorOptions()` liefert Module,
moddle-Erweiterung und Konfiguration für `new BpmnEditor({...})` aus
`@flowaudit/bpmn-editor`. Die Vue-Oberfläche, die Web Component
`<flowaudit-bpmn-editor>` und die React-Hülle liegen in `@flowaudit/bpmn-vue`
und `@flowaudit/bpmn-react`. Ausführlich: `docs/bpmn/frontend.md`.

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
| `@flowaudit/bpmn-flowaudit` | `AUDIT_TYPES` | Konstante | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `Actor` | Schnittstelle | – | `schema/types` |
| `@flowaudit/bpmn-flowaudit` | `ApplyOptions` | Schnittstelle | – | `enrichment/suggestions` |
| `@flowaudit/bpmn-flowaudit` | `Approval` | Schnittstelle | Immutable approved version (new version instead of change). | `collection/collectionData` |
| `@flowaudit/bpmn-flowaudit` | `AuditFinding` | Schnittstelle | – | `schema/types` |
| `@flowaudit/bpmn-flowaudit` | `AuditReference` | Schnittstelle | Reference to key requirement (KA) and assessment criterion (BK). | `schema/types` |
| `@flowaudit/bpmn-flowaudit` | `AuditStep` | Schnittstelle | Walk-through or control test step. | `schema/types` |
| `@flowaudit/bpmn-flowaudit` | `Bounds` | Schnittstelle | – | `model/processModel` |
| `@flowaudit/bpmn-flowaudit` | `CHECKLIST_ITEM` | Konstante | – | `enrichment/textPatterns` |
| `@flowaudit/bpmn-flowaudit` | `CODE_ATTRIBUTES` | Konstante | flowaudit attributes that are codes, never cleaned. | `neutralize/patterns` |
| `@flowaudit/bpmn-flowaudit` | `COLLECTION_SCHEMA` | Konstante | – | `collection/collectionData` |
| `@flowaudit/bpmn-flowaudit` | `COLOR_MARKERS` | Konstante | Colour pair (fill, stroke) → marker suggestion. | `enrichment/suggestions` |
| `@flowaudit/bpmn-flowaudit` | `COLOR_PICKER_EVENT` | Konstante | – | `diagram/colorContextPad` |
| `@flowaudit/bpmn-flowaudit` | `CONFIDENTIALITY` | Konstante | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `CONTROL_TYPES` | Konstante | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `CRITERIA` | Konstante | – | `enrichment/textPatterns` |
| `@flowaudit/bpmn-flowaudit` | `CRITERION_SHORT` | Konstante | – | `enrichment/textPatterns` |
| `@flowaudit/bpmn-flowaudit` | `CROSS_REFERENCE_KINDS` | Konstante | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `Canvas` | Schnittstelle | – | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `CatalogueBlock` | Schnittstelle | – | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `CataloguePort` | Schnittstelle | KA/BK catalogue. The application supplies the texts (e.g. of the Methodological Note); without a port the key requirements of the profile apply. | `ports` |
| `@flowaudit/bpmn-flowaudit` | `CategorySuggestion` | Schnittstelle | – | `reports/categorySuggestion` |
| `@flowaudit/bpmn-flowaudit` | `Change` | Schnittstelle | – | `compare/compare` |
| `@flowaudit/bpmn-flowaudit` | `ChangeKind` | Typ | – | `compare/compare` |
| `@flowaudit/bpmn-flowaudit` | `CitationForm` | Typ | – | `enrichment/citations` |
| `@flowaudit/bpmn-flowaudit` | `CitationHit` | Schnittstelle | – | `enrichment/citations` |
| `@flowaudit/bpmn-flowaudit` | `CollectionData` | Schnittstelle | – | `collection/collectionData` |
| `@flowaudit/bpmn-flowaudit` | `CollectionError` | Klasse | – | `collection/collection` |
| `@flowaudit/bpmn-flowaudit` | `ColorContextPadProvider` | Klasse | – | `diagram/colorContextPad` |
| `@flowaudit/bpmn-flowaudit` | `Columns` | Typ | – | `reports/tables` |
| `@flowaudit/bpmn-flowaudit` | `CommandStack` | Schnittstelle | – | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `Comment` | Schnittstelle | Comment at an element (as `BpmnComment` in the audit_designer). | `ports` |
| `@flowaudit/bpmn-flowaudit` | `Comparison` | Schnittstelle | – | `compare/compare` |
| `@flowaudit/bpmn-flowaudit` | `ContextPad` | Schnittstelle | – | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `ContextPadEntry` | Schnittstelle | – | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `Control` | Schnittstelle | – | `schema/types` |
| `@flowaudit/bpmn-flowaudit` | `Create` | Schnittstelle | – | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `CriterionData` | Schnittstelle | – | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `CrossReference` | Schnittstelle | Stable domain key towards checklists and notes (`prueffeld`, `feststellung_ref`, `register`). | `schema/types` |
| `@flowaudit/bpmn-flowaudit` | `CustomRoleData` | Schnittstelle | – | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `DEADLINE_UNITS` | Konstante | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `DEFAULT_EXPORT_CHOICE` | Konstante | – | `export/exportTypes` |
| `@flowaudit/bpmn-flowaudit` | `DEFAULT_HEADER_COLOR` | Konstante | – | `model/diagramInfo` |
| `@flowaudit/bpmn-flowaudit` | `DEFAULT_HEADER_TEXT_COLOR` | Konstante | – | `model/diagramInfo` |
| `@flowaudit/bpmn-flowaudit` | `DEFAULT_PAGE_FORMAT` | Konstante | – | `layout/pageFormats` |
| `@flowaudit/bpmn-flowaudit` | `DEFAULT_PROFILE` | Konstante | – | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `DIAGRAM_STATUS` | Konstante | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `DIFF_COLORS` | Konstante | – | `compare/compare` |
| `@flowaudit/bpmn-flowaudit` | `Deadline` | Schnittstelle | – | `schema/types` |
| `@flowaudit/bpmn-flowaudit` | `DecorationConfig` | Schnittstelle | – | `diagram/decorations` |
| `@flowaudit/bpmn-flowaudit` | `DecorationVisibility` | Schnittstelle | – | `diagram/decorations` |
| `@flowaudit/bpmn-flowaudit` | `DiagramCollection` | Klasse | – | `collection/collection` |
| `@flowaudit/bpmn-flowaudit` | `DiagramElement` | Schnittstelle | – | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `DiagramEntry` | Schnittstelle | – | `collection/collectionData` |
| `@flowaudit/bpmn-flowaudit` | `DiagramExcerpt` | Schnittstelle | Data derived from the XML (never maintained by hand). | `collection/collectionData` |
| `@flowaudit/bpmn-flowaudit` | `DiagramInfo` | Schnittstelle | – | `schema/types` |
| `@flowaudit/bpmn-flowaudit` | `DiagramReference` | Schnittstelle | – | `collection/analysis` |
| `@flowaudit/bpmn-flowaudit` | `DiagramStatus` | Typ | – | `schema/types` |
| `@flowaudit/bpmn-flowaudit` | `Direction` | Typ | – | `layout/flowDirection` |
| `@flowaudit/bpmn-flowaudit` | `EMPTY_DIAGRAM` | Konstante | Empty diagram as in the audit_designer (`EMPTY_BPMN_XML`). | `model/load` |
| `@flowaudit/bpmn-flowaudit` | `EXECUTION_MODES` | Konstante | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `EXTENSION_FIELDS` | Konstante | Mapping of `Extensions` keys to XML names (declarative, used both ways). | `model/extensions` |
| `@flowaudit/bpmn-flowaudit` | `EditorServices` | Schnittstelle | Minimal editor surface used by the FlowAudit helpers. | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `ElementActor` | Schnittstelle | – | `model/processModel` |
| `@flowaudit/bpmn-flowaudit` | `ElementFactory` | Schnittstelle | – | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `ElementRegistry` | Schnittstelle | – | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `EsiElementGroup` | Schnittstelle | – | `esi/esiRequirements` |
| `@flowaudit/bpmn-flowaudit` | `EsiPort` | Schnittstelle | ESI requirements per element (audit_designer endpoint `/esi-requirements`). Any of the supported response shapes is accepted (`normalizeEsiResponse`). | `ports` |
| `@flowaudit/bpmn-flowaudit` | `EsiRequirement` | Schnittstelle | – | `schema/types` |
| `@flowaudit/bpmn-flowaudit` | `EsiRequirementResult` | Schnittstelle | – | `esi/esiRequirements` |
| `@flowaudit/bpmn-flowaudit` | `EsiRequirements` | Schnittstelle | – | `schema/types` |
| `@flowaudit/bpmn-flowaudit` | `EsiStatus` | Typ | ESI requirements per BPMN element, ported from `useEsiRequirements.ts` of the audit_designer: accepts several plausible response shapes (array, map by element, `{ requirements }`, … | `esi/esiRequirements` |
| `@flowaudit/bpmn-flowaudit` | `EventBus` | Schnittstelle | – | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `EventCallback` | Typ | – | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `Evidence` | Schnittstelle | Audit trail evidence at data objects and data stores. | `schema/types` |
| `@flowaudit/bpmn-flowaudit` | `ExportChoice` | Schnittstelle | – | `export/exportTypes` |
| `@flowaudit/bpmn-flowaudit` | `ExportData` | Schnittstelle | – | `export/exportData` |
| `@flowaudit/bpmn-flowaudit` | `ExportFormat` | Typ | – | `export/exportTypes` |
| `@flowaudit/bpmn-flowaudit` | `Extensions` | Schnittstelle | All FlowAudit data at one BPMN element (`Erweiterungen` in auditcore_bpmn). | `schema/types` |
| `@flowaudit/bpmn-flowaudit` | `FINDINGS` | Konstante | – | `enrichment/textPatterns` |
| `@flowaudit/bpmn-flowaudit` | `FINDING_COLORS` | Konstante | Fill/stroke values of finding colours. | `neutralize/patterns` |
| `@flowaudit/bpmn-flowaudit` | `FINDING_MARKERS` | Konstante | Markers that express a finding. | `neutralize/patterns` |
| `@flowaudit/bpmn-flowaudit` | `FINDING_SEVERITIES` | Konstante | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `FINDING_STATUS` | Konstante | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `FINDING_TYPES` | Konstante | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `FLOWAUDIT_NAMESPACE` | Konstante | – | `schema/descriptor` |
| `@flowaudit/bpmn-flowaudit` | `FLOWAUDIT_PREFIX` | Konstante | – | `schema/descriptor` |
| `@flowaudit/bpmn-flowaudit` | `FLOWAUDIT_SCHEMA_VERSION` | Konstante | – | `schema/descriptor` |
| `@flowaudit/bpmn-flowaudit` | `FLOWSTAT_FIELDS` | Konstante | Canonical attribute and aliases (read, removed on write). | `model/flowstatAttributes` |
| `@flowaudit/bpmn-flowaudit` | `FONT` | Konstante | – | `export/svgBlocks` |
| `@flowaudit/bpmn-flowaudit` | `FUNCTIONING_CATEGORIES` | Konstante | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `FUNDS` | Konstante | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `FUND_SHORT` | Konstante | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `Features` | Schnittstelle | – | `compare/matching` |
| `@flowaudit/bpmn-flowaudit` | `FieldChange` | Schnittstelle | – | `compare/compare` |
| `@flowaudit/bpmn-flowaudit` | `FieldKind` | Typ | Declarative description of the FlowAudit schema 1.1. | `schema/spec` |
| `@flowaudit/bpmn-flowaudit` | `FieldSpec` | Schnittstelle | – | `schema/spec` |
| `@flowaudit/bpmn-flowaudit` | `FlowauditDecorations` | Klasse | – | `diagram/decorations` |
| `@flowaudit/bpmn-flowaudit` | `FlowauditHighlight` | Klasse | – | `diagram/highlight` |
| `@flowaudit/bpmn-flowaudit` | `FlowauditModuleOptions` | Schnittstelle | – | `diagram/modules` |
| `@flowaudit/bpmn-flowaudit` | `FlowstatField` | Typ | – | `model/flowstatAttributes` |
| `@flowaudit/bpmn-flowaudit` | `FlowstatTask` | Schnittstelle | – | `model/flowstatAttributes` |
| `@flowaudit/bpmn-flowaudit` | `Folder` | Schnittstelle | – | `collection/collectionData` |
| `@flowaudit/bpmn-flowaudit` | `FolderNode` | Schnittstelle | – | `collection/collection` |
| `@flowaudit/bpmn-flowaudit` | `FooterBlock` | Schnittstelle | A block of the footer area with its height. | `export/svgBlocks` |
| `@flowaudit/bpmn-flowaudit` | `GERMAN_SVG_TEXTS` | Konstante | – | `export/svgPostProcessing` |
| `@flowaudit/bpmn-flowaudit` | `Group` | Schnittstelle | – | `collection/legacyTree` |
| `@flowaudit/bpmn-flowaudit` | `GroupOverview` | Schnittstelle | – | `collection/analysis` |
| `@flowaudit/bpmn-flowaudit` | `Grouping` | Typ | Grouping of the diagram list into a collapsible tree, ported from `diagrammBaum.ts` of the audit_designer (`baueGruppen` → `buildGroups`). | `collection/legacyTree` |
| `@flowaudit/bpmn-flowaudit` | `HIGHLIGHT_CLASSES` | Konstante | CSS classes per layer and state. | `diagram/highlight` |
| `@flowaudit/bpmn-flowaudit` | `Header` | Schnittstelle | – | `model/diagramInfo` |
| `@flowaudit/bpmn-flowaudit` | `HighlightLayer` | Typ | – | `diagram/highlight` |
| `@flowaudit/bpmn-flowaudit` | `ICONS` | Konstante | – | `icons/icons` |
| `@flowaudit/bpmn-flowaudit` | `INTERNAL_SOURCES` | Konstante | Sources that are internal working material. | `neutralize/patterns` |
| `@flowaudit/bpmn-flowaudit` | `IconName` | Typ | – | `icons/icons` |
| `@flowaudit/bpmn-flowaudit` | `IconShape` | Typ | FlowAudit icon set – drawn from scratch for this project. | `icons/icons` |
| `@flowaudit/bpmn-flowaudit` | `InMemoryStorage` | Klasse | – | `ports/inMemory` |
| `@flowaudit/bpmn-flowaudit` | `IssueCount` | Schnittstelle | – | `validation/issue` |
| `@flowaudit/bpmn-flowaudit` | `KEY_KINDS` | Konstante | Kinds of stable domain keys (checklists and notes link only via these). | `collection/collectionData` |
| `@flowaudit/bpmn-flowaudit` | `KeyKind` | Typ | – | `collection/collectionData` |
| `@flowaudit/bpmn-flowaudit` | `KeyRequirementData` | Schnittstelle | – | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `KeyRequirementEntry` | Schnittstelle | – | `ports` |
| `@flowaudit/bpmn-flowaudit` | `LEGACY_TRANSLATIONS` | Konstante | Translation table of the audit_designer BPMN editor (`deutschTranslate.ts`, `BPMN_UEBERSETZUNGEN`), kept unchanged so strings used by existing extensions keep their German wording. … | `i18n/legacyTranslations` |
| `@flowaudit/bpmn-flowaudit` | `LINE_HEIGHT` | Konstante | – | `export/svgBlocks` |
| `@flowaudit/bpmn-flowaudit` | `Label` | Typ | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `LegacyDiagram` | Schnittstelle | Record of the audit_designer (`BpmnDiagram`), as far as needed for migration. | `model/diagramInfo` |
| `@flowaudit/bpmn-flowaudit` | `LegacyListItem` | Schnittstelle | Fields of a list item as delivered by the audit_designer API. | `collection/legacyTree` |
| `@flowaudit/bpmn-flowaudit` | `LegalBasis` | Schnittstelle | TypeScript form of the FlowAudit extensions. Empty values are absent; booleans are `boolean`. Vocabulary codes (e.g. | `schema/types` |
| `@flowaudit/bpmn-flowaudit` | `LegalBasisNote` | Schnittstelle | – | `export/svgPostProcessing` |
| `@flowaudit/bpmn-flowaudit` | `LegalBasisTemplateData` | Schnittstelle | – | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `LegalSearchHit` | Schnittstelle | – | `ports` |
| `@flowaudit/bpmn-flowaudit` | `LegalSearchOptions` | Schnittstelle | – | `ports` |
| `@flowaudit/bpmn-flowaudit` | `LegalSearchPort` | Schnittstelle | Search help for legal bases (e.g. from auditcore_legal_sources / EUR-Lex). | `ports` |
| `@flowaudit/bpmn-flowaudit` | `ListExtensionKey` | Typ | – | `schema/types` |
| `@flowaudit/bpmn-flowaudit` | `ListFilter` | Typ | – | `collection/legacyTree` |
| `@flowaudit/bpmn-flowaudit` | `LoadedDefinitions` | Schnittstelle | – | `model/load` |
| `@flowaudit/bpmn-flowaudit` | `Locale` | Typ | Controlled vocabularies of schema 1.1 (German and English labels). | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `LocalizedText` | Typ | – | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `MANUAL_REFERENCE` | Konstante | – | `enrichment/textPatterns` |
| `@flowaudit/bpmn-flowaudit` | `MARKERS` | Konstante | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `MARKER_COLORS` | Konstante | Colours derived from markers (fill, stroke). | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `MARKER_COLOR_PRECEDENCE` | Konstante | Precedence when several colouring markers sit on one element. | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `MESSAGES` | Konstante | – | `i18n/translate` |
| `@flowaudit/bpmn-flowaudit` | `METADATA_TYPES` | Konstante | Element types offering the 1.0 metadata (legal basis, internal note). | `schema/descriptor` |
| `@flowaudit/bpmn-flowaudit` | `Marker` | Schnittstelle | – | `schema/types` |
| `@flowaudit/bpmn-flowaudit` | `Messages` | Typ | – | `i18n/translate` |
| `@flowaudit/bpmn-flowaudit` | `ModdleElement` | Schnittstelle | Structural types for the diagram-js services this package uses. | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `ModdleFactory` | Schnittstelle | – | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `ModdleInstance` | Schnittstelle | – | `model/load` |
| `@flowaudit/bpmn-flowaudit` | `ModelAccess` | Schnittstelle | – | `model/access` |
| `@flowaudit/bpmn-flowaudit` | `ModelElement` | Schnittstelle | – | `model/processModel` |
| `@flowaudit/bpmn-flowaudit` | `Modeling` | Schnittstelle | – | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `MystOptions` | Schnittstelle | – | `export/myst` |
| `@flowaudit/bpmn-flowaudit` | `NeutralizationResult` | Schnittstelle | – | `neutralize/neutralize` |
| `@flowaudit/bpmn-flowaudit` | `NeutralizeOptions` | Schnittstelle | – | `neutralize/neutralize` |
| `@flowaudit/bpmn-flowaudit` | `OTHER_ROLE` | Konstante | Role „other body“ – fallback for unknown codes and own roles. | `schema/roles` |
| `@flowaudit/bpmn-flowaudit` | `Orientation` | Typ | – | `layout/pageFormats` |
| `@flowaudit/bpmn-flowaudit` | `PAGE_FORMATS` | Konstante | – | `layout/pageFormats` |
| `@flowaudit/bpmn-flowaudit` | `PALETTE_COLORS` | Konstante | – | `export/colorPalette` |
| `@flowaudit/bpmn-flowaudit` | `PERSON_ATTRIBUTES` | Konstante | Person fields at diagram info. | `neutralize/patterns` |
| `@flowaudit/bpmn-flowaudit` | `PROCESS_TABLE_COLUMNS` | Konstante | – | `reports/processReports` |
| `@flowaudit/bpmn-flowaudit` | `PROFILE_SCHEMA` | Konstante | – | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `PROGRAMMING_PERIODS` | Konstante | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `PROTECTION_NAMESPACE` | Konstante | – | `model/unknownElements` |
| `@flowaudit/bpmn-flowaudit` | `PX_PER_MM` | Konstante | Page formats and page break guides, ported from `seitenformate.ts` of the audit_designer (`seitenMasse` → `pageSize`, `berechneRaster` → `computePageGrid`). | `layout/pageFormats` |
| `@flowaudit/bpmn-flowaudit` | `PageFormat` | Schnittstelle | – | `layout/pageFormats` |
| `@flowaudit/bpmn-flowaudit` | `PageGrid` | Schnittstelle | – | `layout/pageFormats` |
| `@flowaudit/bpmn-flowaudit` | `PageSize` | Schnittstelle | – | `layout/pageFormats` |
| `@flowaudit/bpmn-flowaudit` | `Palette` | Schnittstelle | – | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `PaletteColor` | Schnittstelle | Audit-compliant colour palette for BPMN elements, ported from `farbpalette.ts` of the audit_designer. | `export/colorPalette` |
| `@flowaudit/bpmn-flowaudit` | `PaletteEntry` | Schnittstelle | – | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `PdfImage` | Schnittstelle | – | `export/pdf` |
| `@flowaudit/bpmn-flowaudit` | `PdfOptions` | Schnittstelle | – | `export/pdf` |
| `@flowaudit/bpmn-flowaudit` | `Point` | Schnittstelle | – | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `PrepareSvgOptions` | Schnittstelle | – | `export/svgPostProcessing` |
| `@flowaudit/bpmn-flowaudit` | `ProcessModel` | Schnittstelle | – | `model/processModel` |
| `@flowaudit/bpmn-flowaudit` | `ProfileCataloguePort` | Klasse | KA catalogue from a profile, optionally enriched by criteria texts of the application. | `ports/inMemory` |
| `@flowaudit/bpmn-flowaudit` | `ProfileData` | Schnittstelle | – | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `ProfileLegalSearch` | Klasse | Legal search over the frequent legal bases of a profile plus parsing of the typed citation. No network access. | `ports/inMemory` |
| `@flowaudit/bpmn-flowaudit` | `ProfilePort` | Schnittstelle | – | `ports` |
| `@flowaudit/bpmn-flowaudit` | `ProfileSummary` | Schnittstelle | – | `ports` |
| `@flowaudit/bpmn-flowaudit` | `REGISTER` | Konstante | – | `enrichment/textPatterns` |
| `@flowaudit/bpmn-flowaudit` | `REMOVED_ELEMENTS` | Konstante | Elements removed completely. | `neutralize/patterns` |
| `@flowaudit/bpmn-flowaudit` | `REPORT_SCHEMA` | Konstante | – | `validation/validate` |
| `@flowaudit/bpmn-flowaudit` | `RISK_CATEGORIES` | Konstante | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `RISK_LEVELS` | Konstante | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `ROLES` | Konstante | – | `schema/roles` |
| `@flowaudit/bpmn-flowaudit` | `ROLE_PREFIX` | Konstante | Role prefix of a task label („Stelle: Antrag prüfen“). | `enrichment/textPatterns` |
| `@flowaudit/bpmn-flowaudit` | `RULES` | Konstante | – | `validation/catalog` |
| `@flowaudit/bpmn-flowaudit` | `RULESET_VERSION` | Konstante | – | `validation/validate` |
| `@flowaudit/bpmn-flowaudit` | `Replacement` | Schnittstelle | – | `neutralize/neutralize` |
| `@flowaudit/bpmn-flowaudit` | `ReplacementKind` | Typ | Patterns removed on neutralisation (same list as `auditcore_bpmn`). | `neutralize/patterns` |
| `@flowaudit/bpmn-flowaudit` | `Risk` | Schnittstelle | – | `schema/types` |
| `@flowaudit/bpmn-flowaudit` | `Role` | Schnittstelle | – | `schema/roles` |
| `@flowaudit/bpmn-flowaudit` | `RoleAlias` | Schnittstelle | – | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `RolePaletteProvider` | Klasse | – | `diagram/rolePalette` |
| `@flowaudit/bpmn-flowaudit` | `Row` | Typ | Table output formats: CSV (UTF-8, semicolon) and MyST/Markdown pipe tables, same format as `auditcore_bpmn` reports. | `reports/tables` |
| `@flowaudit/bpmn-flowaudit` | `Rule` | Schnittstelle | – | `validation/catalog` |
| `@flowaudit/bpmn-flowaudit` | `RuleContext` | Klasse | – | `validation/context` |
| `@flowaudit/bpmn-flowaudit` | `RuleGroup` | Typ | – | `validation/catalog` |
| `@flowaudit/bpmn-flowaudit` | `SEVERITY_LABELS` | Konstante | – | `validation/catalog` |
| `@flowaudit/bpmn-flowaudit` | `SOURCE_TYPES` | Konstante | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `STRUCTURE_FIELDS` | Konstante | – | `model/legalBasis` |
| `@flowaudit/bpmn-flowaudit` | `SVG_NS` | Konstante | SVG building blocks for the export post-processing: plain shapes and `<text>` only, so the result looks the same in Word, LibreOffice and the browser. | `export/svgBlocks` |
| `@flowaudit/bpmn-flowaudit` | `SegregationKind` | Typ | – | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `SegregationRuleData` | Schnittstelle | – | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `Selection` | Schnittstelle | – | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `SelectionData` | Schnittstelle | – | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `ServiceLocator` | Schnittstelle | The `get(name)` accessor of the editor (diagram-js injector). | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `Severity` | Typ | – | `validation/catalog` |
| `@flowaudit/bpmn-flowaudit` | `Source` | Schnittstelle | – | `schema/types` |
| `@flowaudit/bpmn-flowaudit` | `StaticProfilePort` | Klasse | – | `ports/inMemory` |
| `@flowaudit/bpmn-flowaudit` | `StoragePort` | Schnittstelle | Loading and saving of collection, diagrams and approvals – same split as the `Storage` protocol of `auditcore_bpmn`. | `ports` |
| `@flowaudit/bpmn-flowaudit` | `Suggestion` | Schnittstelle | – | `enrichment/suggestions` |
| `@flowaudit/bpmn-flowaudit` | `SuggestionKind` | Typ | – | `enrichment/suggestions` |
| `@flowaudit/bpmn-flowaudit` | `SuggestionOptions` | Schnittstelle | – | `enrichment/suggestions` |
| `@flowaudit/bpmn-flowaudit` | `SuggestionOrigin` | Typ | – | `enrichment/suggestions` |
| `@flowaudit/bpmn-flowaudit` | `SvgTexts` | Schnittstelle | – | `export/svgPostProcessing` |
| `@flowaudit/bpmn-flowaudit` | `SynopsisRow` | Schnittstelle | – | `compare/compare` |
| `@flowaudit/bpmn-flowaudit` | `TASK_TYPES` | Konstante | – | `model/processModel` |
| `@flowaudit/bpmn-flowaudit` | `TEST_RESULTS` | Konstante | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `TEXT_PATTERNS` | Konstante | – | `neutralize/patterns` |
| `@flowaudit/bpmn-flowaudit` | `TEXT_TYPES` | Konstante | Child elements with plain text content; each needs its own moddle type. | `schema/spec` |
| `@flowaudit/bpmn-flowaudit` | `TYPES` | Konstante | – | `schema/spec` |
| `@flowaudit/bpmn-flowaudit` | `TYPE_INTERNAL_NOTE` | Konstante | – | `schema/descriptor` |
| `@flowaudit/bpmn-flowaudit` | `TYPE_LEGAL_BASIS` | Konstante | Type names as in the audit_designer (`flowauditModdle.ts`). | `schema/descriptor` |
| `@flowaudit/bpmn-flowaudit` | `Tag` | Schnittstelle | – | `collection/collectionData` |
| `@flowaudit/bpmn-flowaudit` | `TargetActualCheck` | Schnittstelle | – | `compare/compare` |
| `@flowaudit/bpmn-flowaudit` | `TargetActualResult` | Schnittstelle | – | `compare/compare` |
| `@flowaudit/bpmn-flowaudit` | `TemplateData` | Schnittstelle | – | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `TextHit` | Schnittstelle | – | `enrichment/textPatterns` |
| `@flowaudit/bpmn-flowaudit` | `TextOptions` | Schnittstelle | – | `export/svgBlocks` |
| `@flowaudit/bpmn-flowaudit` | `TextPattern` | Schnittstelle | – | `neutralize/patterns` |
| `@flowaudit/bpmn-flowaudit` | `Translate` | Typ | – | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `TreeOptions` | Schnittstelle | – | `collection/legacyTree` |
| `@flowaudit/bpmn-flowaudit` | `TypeSpec` | Schnittstelle | – | `schema/spec` |
| `@flowaudit/bpmn-flowaudit` | `UnknownElementsGuard` | Klasse | – | `diagram/unknownElementsModule` |
| `@flowaudit/bpmn-flowaudit` | `UsedColor` | Schnittstelle | – | `export/svgPostProcessing` |
| `@flowaudit/bpmn-flowaudit` | `UsedMarker` | Schnittstelle | – | `export/svgPostProcessing` |
| `@flowaudit/bpmn-flowaudit` | `VARIANTS` | Konstante | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `VOCABULARIES` | Konstante | Names of all vocabularies, for panels and validation messages. | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `ValidationIssue` | Schnittstelle | – | `validation/issue` |
| `@flowaudit/bpmn-flowaudit` | `ValidationOptions` | Schnittstelle | – | `validation/context` |
| `@flowaudit/bpmn-flowaudit` | `ValidationPort` | Schnittstelle | Server-side validation (e.g. `auditcore_bpmn`), optional. | `ports` |
| `@flowaudit/bpmn-flowaudit` | `ValidationReport` | Schnittstelle | – | `validation/validate` |
| `@flowaudit/bpmn-flowaudit` | `Viewbox` | Schnittstelle | – | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `ViewboxLike` | Schnittstelle | – | `layout/pageFormats` |
| `@flowaudit/bpmn-flowaudit` | `Vocabulary` | Typ | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `VocabularyName` | Typ | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `WITHOUT_ASSIGNMENT` | Konstante | – | `collection/legacyTree` |
| `@flowaudit/bpmn-flowaudit` | `WRITE_ORDER` | Konstante | Order of FlowAudit children inside `extensionElements` (same as `_REIHENFOLGE` in `auditcore_bpmn.flowaudit`), so both sides write alike. | `schema/spec` |
| `@flowaudit/bpmn-flowaudit` | `WalkthroughOverview` | Schnittstelle | – | `reports/processReports` |
| `@flowaudit/bpmn-flowaudit` | `WalkthroughProgress` | Schnittstelle | – | `walkthrough/walkthrough` |
| `@flowaudit/bpmn-flowaudit` | `WalkthroughStep` | Schnittstelle | – | `walkthrough/walkthrough` |
| `@flowaudit/bpmn-flowaudit` | `actLong` | Funktion | Long canonical form of an act name (`VO` → `Verordnung`). | `model/legalBasis` |
| `@flowaudit/bpmn-flowaudit` | `actShort` | Funktion | Short form of an act name for display (`Verordnung` → `VO`). | `model/legalBasis` |
| `@flowaudit/bpmn-flowaudit` | `activities` | Funktion | – | `model/processModel` |
| `@flowaudit/bpmn-flowaudit` | `actorLabel` | Funktion | – | `reports/processReports` |
| `@flowaudit/bpmn-flowaudit` | `applyDirection` | Funktion | Applies a direction to the whole diagram; returns the number of pools and lanes. | `layout/flowDirection` |
| `@flowaudit/bpmn-flowaudit` | `applySuggestions` | Funktion | Takes over accepted suggestions; existing data stays, duplicates are skipped. | `enrichment/suggestions` |
| `@flowaudit/bpmn-flowaudit` | `approve` | Funktion | Records the SHA-256 of an approved version; a version is immutable. | `collection/analysis` |
| `@flowaudit/bpmn-flowaudit` | `auditReferenceText` | Funktion | – | `diagram/decorations` |
| `@flowaudit/bpmn-flowaudit` | `auditReferencesIn` | Funktion | – | `enrichment/textPatterns` |
| `@flowaudit/bpmn-flowaudit` | `base64Utf8` | Funktion | Base64 with correct handling of umlauts (`btoa` only knows Latin-1). | `export/myst` |
| `@flowaudit/bpmn-flowaudit` | `bodyLabel` | Funktion | Body of an element for display: role (display name), otherwise lane/pool. | `compare/matching` |
| `@flowaudit/bpmn-flowaudit` | `buildGroups` | Funktion | Filters, searches and groups in one pass. | `collection/legacyTree` |
| `@flowaudit/bpmn-flowaudit` | `buildMystSnippet` | Funktion | – | `export/myst` |
| `@flowaudit/bpmn-flowaudit` | `camelToSnake` | Funktion | – | `model/wire` |
| `@flowaudit/bpmn-flowaudit` | `category` | Funktion | – | `compare/matching` |
| `@flowaudit/bpmn-flowaudit` | `changeLabel` | Funktion | – | `compare/compare` |
| `@flowaudit/bpmn-flowaudit` | `checkCollection` | Funktion | Collection rules (`BPMN-K001`–`K007`). | `collection/analysis` |
| `@flowaudit/bpmn-flowaudit` | `checkTargetActual` | Funktion | Per activity, gateway and event of the target: present in the actual state, same body, controls and successors. „Met“ is binary; the reasons name each deviation. | `compare/compare` |
| `@flowaudit/bpmn-flowaudit` | `citation` | Funktion | Long citation, e.g. „Artikel 73 Absatz 2 Buchstabe b der Verordnung (EU) 2021/1060“. | `model/legalBasis` |
| `@flowaudit/bpmn-flowaudit` | `cleanInfo` | Funktion | Drops empty values, sets the schema version, fills legal basis texts. | `model/diagramInfo` |
| `@flowaudit/bpmn-flowaudit` | `collectColors` | Funktion | Counts used colours for the legend. Colours outside the palette are kept but labelled „Nicht zugeordnet“ – dropping them silently would present an incomplete legend as complete. | `export/exportData` |
| `@flowaudit/bpmn-flowaudit` | `collectExportData` | Funktion | – | `export/exportData` |
| `@flowaudit/bpmn-flowaudit` | `collectLegalBasisNotes` | Funktion | – | `export/exportData` |
| `@flowaudit/bpmn-flowaudit` | `collectMarkers` | Funktion | – | `export/exportData` |
| `@flowaudit/bpmn-flowaudit` | `collectSuggestions` | Funktion | All suggestions for an unchanged diagram; duplicates per element are dropped. | `enrichment/suggestions` |
| `@flowaudit/bpmn-flowaudit` | `colorContextPadModule` | Konstante | – | `diagram/colorContextPad` |
| `@flowaudit/bpmn-flowaudit` | `colorFromDi` | Funktion | Reads a colour from the DI (`bioc:` or `color:` namespace). | `model/processModel` |
| `@flowaudit/bpmn-flowaudit` | `colorsFromMarkers` | Funktion | Fill and stroke per element from colouring markers (precedence as in the schema). | `compare/compare` |
| `@flowaudit/bpmn-flowaudit` | `comparable` | Funktion | – | `compare/matching` |
| `@flowaudit/bpmn-flowaudit` | `compareProfileVersions` | Funktion | Compares versions such as `2026.09.1` numerically part by part. | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `compareVersions` | Funktion | Element-wise comparison of two versions of the same diagram. | `compare/compare` |
| `@flowaudit/bpmn-flowaudit` | `completeEuAct` | Funktion | Fills missing CELEX/ELI/URL of an EU act; existing values stay. | `enrichment/citations` |
| `@flowaudit/bpmn-flowaudit` | `computePageGrid` | Funktion | Computes the page break grid for the current view. The origin is the diagram origin (0/0), so the grid moves with the diagram like a printout. | `layout/pageFormats` |
| `@flowaudit/bpmn-flowaudit` | `computeValues` | Funktion | New value list of `extensionElements`: foreign entries first (in their order), then FlowAudit entries in schema order. | `model/extensions` |
| `@flowaudit/bpmn-flowaudit` | `copyToClipboard` | Funktion | Puts text on the clipboard. The fallback through a hidden text field is needed because the Clipboard API is only available in secure contexts. | `export/myst` |
| `@flowaudit/bpmn-flowaudit` | `countIssues` | Funktion | – | `validation/issue` |
| `@flowaudit/bpmn-flowaudit` | `createModdle` | Funktion | – | `model/load` |
| `@flowaudit/bpmn-flowaudit` | `createModelElement` | Funktion | – | `model/processModel` |
| `@flowaudit/bpmn-flowaudit` | `createTranslator` | Funktion | Creates a translate function. Tables are merged in order: core table (optional), legacy audit_designer table (German only), FlowAudit messages, application overrides. | `i18n/translate` |
| `@flowaudit/bpmn-flowaudit` | `criterionKnown` | Funktion | `true`/`false` against the criteria catalogue of the KA; `undefined` if none exists. | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `crossReferencesIn` | Funktion | – | `enrichment/textPatterns` |
| `@flowaudit/bpmn-flowaudit` | `deadlineText` | Funktion | – | `reports/processReports` |
| `@flowaudit/bpmn-flowaudit` | `decorationsModule` | Konstante | – | `diagram/decorations` |
| `@flowaudit/bpmn-flowaudit` | `definitionsOf` | Funktion | Definitions behind the root element of a running editor. | `model/buildModel` |
| `@flowaudit/bpmn-flowaudit` | `deriveStatus` | Funktion | – | `esi/esiRequirements` |
| `@flowaudit/bpmn-flowaudit` | `diagramLabel` | Funktion | Label for the book: lower case, without blanks and special characters. | `export/myst` |
| `@flowaudit/bpmn-flowaudit` | `diagramReferences` | Funktion | Calls (call activity → process) and link events across diagram boundaries. | `collection/analysis` |
| `@flowaudit/bpmn-flowaudit` | `diffColors` | Funktion | Colours for the graphical diff: `[before, after]` by element id. | `compare/compare` |
| `@flowaudit/bpmn-flowaudit` | `displayName` | Funktion | – | `model/processModel` |
| `@flowaudit/bpmn-flowaudit` | `displayText` | Funktion | Readable text: free text, otherwise short citation. | `model/legalBasis` |
| `@flowaudit/bpmn-flowaudit` | `download` | Funktion | File output for the image formats, ported from `bildExport.ts` of the audit_designer (`ladeHerunter` → `download`, `dateiname` → `fileName`, `svgNachPng` → `svgToPng`). | `export/imageExport` |
| `@flowaudit/bpmn-flowaudit` | `editorAccess` | Funktion | – | `model/access` |
| `@flowaudit/bpmn-flowaudit` | `editorServices` | Funktion | – | `diagram/services` |
| `@flowaudit/bpmn-flowaudit` | `elementsForKey` | Funktion | Element ids of the diagram model matching a key (for highlighting). | `collection/excerpt` |
| `@flowaudit/bpmn-flowaudit` | `emptyCollection` | Funktion | – | `collection/collectionData` |
| `@flowaudit/bpmn-flowaudit` | `emptyExcerpt` | Funktion | – | `collection/collectionData` |
| `@flowaudit/bpmn-flowaudit` | `emptyExtensions` | Funktion | – | `schema/types` |
| `@flowaudit/bpmn-flowaudit` | `euAct` | Funktion | `[eliKind, year, number]` of an EU act, or `null`. | `enrichment/citations` |
| `@flowaudit/bpmn-flowaudit` | `excerptFromModel` | Funktion | – | `collection/excerpt` |
| `@flowaudit/bpmn-flowaudit` | `extensionValues` | Funktion | All values of `extensionElements` (empty list if there are none). | `model/extensions` |
| `@flowaudit/bpmn-flowaudit` | `features` | Funktion | – | `compare/matching` |
| `@flowaudit/bpmn-flowaudit` | `fileName` | Funktion | File name without blanks and special characters. | `export/imageExport` |
| `@flowaudit/bpmn-flowaudit` | `fillPlaceholders` | Funktion | – | `i18n/translate` |
| `@flowaudit/bpmn-flowaudit` | `findCitations` | Funktion | Finds legal citations in free text (e.g. `bpmn:documentation`), without overlaps. | `enrichment/citations` |
| `@flowaudit/bpmn-flowaudit` | `findPaletteColor` | Funktion | – | `export/colorPalette` |
| `@flowaudit/bpmn-flowaudit` | `findingsList` | Funktion | – | `reports/processReports` |
| `@flowaudit/bpmn-flowaudit` | `flowOrder` | Funktion | Flow nodes in flow order (breadth-first from start events), rest afterwards. | `reports/processReports` |
| `@flowaudit/bpmn-flowaudit` | `flowauditEditorOptions` | Funktion | Everything the editor needs: modules, moddle extension and module config. | `diagram/modules` |
| `@flowaudit/bpmn-flowaudit` | `flowauditModdleDescriptor` | Konstante | For `moddleExtensions: { flowaudit: flowauditModdleDescriptor }`. | `schema/descriptor` |
| `@flowaudit/bpmn-flowaudit` | `flowauditModules` | Funktion | – | `diagram/modules` |
| `@flowaudit/bpmn-flowaudit` | `forWriting` | Funktion | Prepares a legal basis for writing: text content is mandatory (1.0 readers show it). Existing free text is never overwritten. | `model/legalBasis` |
| `@flowaudit/bpmn-flowaudit` | `fromModdle` | Funktion | moddle element → TypeScript object (empty values are dropped). | `model/moddleMapping` |
| `@flowaudit/bpmn-flowaudit` | `fromWire` | Funktion | JSON of `auditcore_bpmn` → TypeScript object (camelCase keys). | `model/wire` |
| `@flowaudit/bpmn-flowaudit` | `germanTranslate` | Konstante | Legacy API: German translation (`deutschTranslate`). | `i18n/translate` |
| `@flowaudit/bpmn-flowaudit` | `groupByElement` | Funktion | – | `esi/esiRequirements` |
| `@flowaudit/bpmn-flowaudit` | `groupOverview` | Funktion | Overview of a group (folder, recursive) or a tag. | `collection/analysis` |
| `@flowaudit/bpmn-flowaudit` | `hasIcon` | Funktion | – | `icons/icons` |
| `@flowaudit/bpmn-flowaudit` | `headerOf` | Funktion | – | `model/diagramInfo` |
| `@flowaudit/bpmn-flowaudit` | `headlessAccess` | Funktion | – | `model/access` |
| `@flowaudit/bpmn-flowaudit` | `highlightModule` | Konstante | – | `diagram/highlight` |
| `@flowaudit/bpmn-flowaudit` | `iconElement` | Funktion | Icon as SVG element inside an existing SVG (diagram decorations). | `icons/icons` |
| `@flowaudit/bpmn-flowaudit` | `iconPrimitives` | Funktion | Primitive shapes of an icon as `[tag, attributes]` (for Vue render functions). | `icons/icons` |
| `@flowaudit/bpmn-flowaudit` | `iconSvg` | Funktion | SVG markup of an icon (e.g. for CSS data URIs or `innerHTML`). | `icons/icons` |
| `@flowaudit/bpmn-flowaudit` | `idFromName` | Funktion | Creates a readable, valid id from a name („Antragsverfahren 2“ → `antragsverfahren-2`). | `collection/collectionData` |
| `@flowaudit/bpmn-flowaudit` | `imageToPdf` | Funktion | Builds a one-page PDF with the image centred and fitted into the margins. | `export/pdf` |
| `@flowaudit/bpmn-flowaudit` | `infoFromLegacy` | Funktion | Migrates the legacy columns into diagram info. Data present in the XML wins – the XML is the authoritative source. | `model/diagramInfo` |
| `@flowaudit/bpmn-flowaudit` | `isActivity` | Funktion | – | `model/processModel` |
| `@flowaudit/bpmn-flowaudit` | `isColorable` | Funktion | Elements without meaningful colour (root, labels). | `diagram/colorContextPad` |
| `@flowaudit/bpmn-flowaudit` | `isEvent` | Funktion | – | `model/processModel` |
| `@flowaudit/bpmn-flowaudit` | `isFlowNode` | Funktion | – | `model/processModel` |
| `@flowaudit/bpmn-flowaudit` | `isFlowauditElement` | Funktion | – | `model/moddleMapping` |
| `@flowaudit/bpmn-flowaudit` | `isGateway` | Funktion | – | `model/processModel` |
| `@flowaudit/bpmn-flowaudit` | `isStructured` | Funktion | – | `model/legalBasis` |
| `@flowaudit/bpmn-flowaudit` | `isTask` | Funktion | – | `model/processModel` |
| `@flowaudit/bpmn-flowaudit` | `isUnchanged` | Funktion | – | `compare/compare` |
| `@flowaudit/bpmn-flowaudit` | `isValidId` | Funktion | – | `collection/collectionData` |
| `@flowaudit/bpmn-flowaudit` | `issue` | Funktion | – | `validation/issue` |
| `@flowaudit/bpmn-flowaudit` | `issueFromWire` | Funktion | Converts a server issue of `auditcore_bpmn` (`rule_id`, `severity`, `params`, …) into a `ValidationIssue`. | `validation/issue` |
| `@flowaudit/bpmn-flowaudit` | `issueMessage` | Funktion | – | `validation/issue` |
| `@flowaudit/bpmn-flowaudit` | `keepDirection` | Funktion | Keeps newly created pools on the chosen direction; returns an unsubscribe function. | `layout/flowDirection` |
| `@flowaudit/bpmn-flowaudit` | `keyRequirement` | Funktion | – | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `keyRequirements` | Funktion | – | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `label` | Funktion | – | `schema/vocabulary` |
| `@flowaudit/bpmn-flowaudit` | `latestProfiles` | Funktion | Latest version per profile id. | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `legacyFromInfo` | Funktion | Diagram info back into the legacy columns (for applications in transition). | `model/diagramInfo` |
| `@flowaudit/bpmn-flowaudit` | `legalBasisKey` | Funktion | Key for duplicate detection (structured fields or text). | `model/legalBasis` |
| `@flowaudit/bpmn-flowaudit` | `loadDefinitions` | Funktion | – | `model/load` |
| `@flowaudit/bpmn-flowaudit` | `localType` | Funktion | `bpmn:UserTask` → `userTask`. | `model/processModel` |
| `@flowaudit/bpmn-flowaudit` | `localXmlName` | Funktion | Local XML name of a flowaudit moddle element, e.g. `kennzeichen`. | `model/moddleMapping` |
| `@flowaudit/bpmn-flowaudit` | `localized` | Funktion | – | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `mainElement` | Funktion | Main element: the collaboration, otherwise the first process. | `model/buildModel` |
| `@flowaudit/bpmn-flowaudit` | `matchElements` | Funktion | Element id old → element id new. | `compare/matching` |
| `@flowaudit/bpmn-flowaudit` | `modelFromDefinitions` | Funktion | Builds the model from moddle definitions (headless). | `model/buildModel` |
| `@flowaudit/bpmn-flowaudit` | `modelFromEditor` | Funktion | Builds the model from a running editor, using the current shape bounds. | `model/buildModel` |
| `@flowaudit/bpmn-flowaudit` | `neighbours` | Funktion | – | `compare/matching` |
| `@flowaudit/bpmn-flowaudit` | `neutralize` | Funktion | Neutralises a diagram; `replacements` adds names known to the application. | `neutralize/neutralize` |
| `@flowaudit/bpmn-flowaudit` | `nextStepId` | Funktion | Next id for an audit step (`PS1`, `PS2`, …) unique across the diagram. | `walkthrough/walkthrough` |
| `@flowaudit/bpmn-flowaudit` | `normalName` | Funktion | – | `compare/matching` |
| `@flowaudit/bpmn-flowaudit` | `normalizeColor` | Funktion | Compares colour values tolerant of case and short form (`#abc`). | `export/colorPalette` |
| `@flowaudit/bpmn-flowaudit` | `normalizeEsiResponse` | Funktion | Flat list from any of the supported response shapes. | `esi/esiRequirements` |
| `@flowaudit/bpmn-flowaudit` | `normalizeRequirement` | Funktion | – | `esi/esiRequirements` |
| `@flowaudit/bpmn-flowaudit` | `normalized` | Funktion | Act in long form and text content as long citation. | `model/legalBasis` |
| `@flowaudit/bpmn-flowaudit` | `pageSize` | Funktion | Page size in diagram pixels, including orientation. | `layout/pageFormats` |
| `@flowaudit/bpmn-flowaudit` | `parseCitation` | Funktion | Reads a single citation; without a hit it stays free text. | `enrichment/citations` |
| `@flowaudit/bpmn-flowaudit` | `pdfString` | Funktion | Escapes text for a PDF string literal (Latin-1 range only; others become „?“). | `export/pdf` |
| `@flowaudit/bpmn-flowaudit` | `periodStart` | Funktion | Start year from `YYYY-YYYY`, otherwise `null`. | `schema/roles` |
| `@flowaudit/bpmn-flowaudit` | `pixelsToMm` | Funktion | Diagram pixels → millimetres at 96 dpi (for choosing the page format). | `export/pdf` |
| `@flowaudit/bpmn-flowaudit` | `prepareSvg` | Funktion | Adds header, legends and directory of legal bases to the exported SVG. | `export/svgPostProcessing` |
| `@flowaudit/bpmn-flowaudit` | `processTable` | Funktion | Process description in flow order. | `reports/processReports` |
| `@flowaudit/bpmn-flowaudit` | `profileReference` | Funktion | – | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `protectUnknownElements` | Funktion | – | `model/unknownElements` |
| `@flowaudit/bpmn-flowaudit` | `readDiagramInfo` | Funktion | Diagram info: collaboration first, then processes in document order. | `model/buildModel` |
| `@flowaudit/bpmn-flowaudit` | `readDiagramInfoFromEditor` | Funktion | Editor: reads the diagram info (collaboration, otherwise first process). | `model/diagramInfo` |
| `@flowaudit/bpmn-flowaudit` | `readExtensions` | Funktion | Reads all FlowAudit data of a business object. | `model/extensions` |
| `@flowaudit/bpmn-flowaudit` | `readFlowstatValues` | Funktion | – | `model/flowstatAttributes` |
| `@flowaudit/bpmn-flowaudit` | `readMetadata` | Funktion | Reads the text value of a flowaudit entry; '' if not maintained. | `model/legacyMetadata` |
| `@flowaudit/bpmn-flowaudit` | `readSvgSize` | Funktion | – | `export/imageExport` |
| `@flowaudit/bpmn-flowaudit` | `readTasksFromXml` | Funktion | – | `model/flowstatAttributes` |
| `@flowaudit/bpmn-flowaudit` | `recordStep` | Funktion | Records or replaces an audit step at an element. | `walkthrough/walkthrough` |
| `@flowaudit/bpmn-flowaudit` | `removeRolePrefix` | Funktion | „Stelle: Antrag prüfen“ → „Antrag prüfen“. | `enrichment/textPatterns` |
| `@flowaudit/bpmn-flowaudit` | `removeStep` | Funktion | – | `walkthrough/walkthrough` |
| `@flowaudit/bpmn-flowaudit` | `reportToWire` | Funktion | Report as JSON of `auditcore_bpmn` (`validation-report-1.schema.json`). | `validation/validate` |
| `@flowaudit/bpmn-flowaudit` | `restoreUnknownElements` | Funktion | – | `model/unknownElements` |
| `@flowaudit/bpmn-flowaudit` | `riskControlMatrix` | Funktion | One row per risk and linked control (risks without control once). | `reports/processReports` |
| `@flowaudit/bpmn-flowaudit` | `roleAppliesTo` | Funktion | `true` if the role exists in the programming period (unknown period: yes). | `schema/roles` |
| `@flowaudit/bpmn-flowaudit` | `roleFromText` | Funktion | Role from a lane name or task prefix via the alias list (first hit, case insensitive). Additional aliases – e.g. names of bodies in a programme – are supplied by the application. | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `roleOf` | Funktion | Role by code (own roles of the profile win). | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `rolePaletteModule` | Konstante | – | `diagram/rolePalette` |
| `@flowaudit/bpmn-flowaudit` | `roleProvided` | Funktion | – | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `rolesFor` | Funktion | Roles of the profile, filtered by programming period (no profile: full catalogue). | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `ruleText` | Funktion | Message of a rule; parameters `name_de`/`name_en` override `name`. | `validation/catalog` |
| `@flowaudit/bpmn-flowaudit` | `saveDefinitions` | Funktion | – | `model/load` |
| `@flowaudit/bpmn-flowaudit` | `setColor` | Funktion | Sets a palette colour; `null` removes the colouring. | `diagram/colorContextPad` |
| `@flowaudit/bpmn-flowaudit` | `setDiagramInfo` | Funktion | Headless: sets the diagram info at the main element. | `model/diagramInfo` |
| `@flowaudit/bpmn-flowaudit` | `setExtensionsDirect` | Funktion | Like `writeExtensions`, but mutates the model directly (headless). | `model/extensions` |
| `@flowaudit/bpmn-flowaudit` | `severityLabel` | Funktion | – | `validation/issue` |
| `@flowaudit/bpmn-flowaudit` | `sha256Xml` | Funktion | SHA-256 over the UTF-8 bytes of the XML exactly as stored (hex). | `collection/analysis` |
| `@flowaudit/bpmn-flowaudit` | `shortCitation` | Funktion | Short citation for display, e.g. „Art. 73 Abs. 2 Buchst. b VO (EU) 2021/1060“. | `model/legalBasis` |
| `@flowaudit/bpmn-flowaudit` | `snakeToCamel` | Funktion | – | `model/wire` |
| `@flowaudit/bpmn-flowaudit` | `sortIssues` | Funktion | – | `validation/issue` |
| `@flowaudit/bpmn-flowaudit` | `sourcesIn` | Funktion | – | `enrichment/textPatterns` |
| `@flowaudit/bpmn-flowaudit` | `splitFreeText` | Funktion | Splits a 1.0 free text with several acts („§ 55 BHO; Art. 74 VO (EU) 2021/1060“). | `model/legalBasis` |
| `@flowaudit/bpmn-flowaudit` | `splitList` | Funktion | – | `enrichment/textPatterns` |
| `@flowaudit/bpmn-flowaudit` | `suggestCategories` | Funktion | – | `reports/categorySuggestion` |
| `@flowaudit/bpmn-flowaudit` | `summarize` | Funktion | – | `esi/esiRequirements` |
| `@flowaudit/bpmn-flowaudit` | `svgGroup` | Funktion | – | `export/svgBlocks` |
| `@flowaudit/bpmn-flowaudit` | `svgRect` | Funktion | – | `export/svgBlocks` |
| `@flowaudit/bpmn-flowaudit` | `svgText` | Funktion | – | `export/svgBlocks` |
| `@flowaudit/bpmn-flowaudit` | `svgToCanvas` | Funktion | Paints an SVG onto a canvas with white ground. `scale` 2 ≈ 192 dpi. | `export/imageExport` |
| `@flowaudit/bpmn-flowaudit` | `svgToJpeg` | Funktion | – | `export/imageExport` |
| `@flowaudit/bpmn-flowaudit` | `svgToPng` | Funktion | – | `export/imageExport` |
| `@flowaudit/bpmn-flowaudit` | `synopsis` | Funktion | Rows „element \| before \| after \| change“ for reports. | `compare/compare` |
| `@flowaudit/bpmn-flowaudit` | `targetActualPairs` | Funktion | `[actualId, targetId]` of all linked actual-state diagrams. | `collection/analysis` |
| `@flowaudit/bpmn-flowaudit` | `textSuggestions` | Funktion | – | `enrichment/suggestions` |
| `@flowaudit/bpmn-flowaudit` | `toCsv` | Funktion | CSV with header from `columns` (or the keys); `bom` for Excel. | `reports/tables` |
| `@flowaudit/bpmn-flowaudit` | `toModdle` | Funktion | TypeScript object → new moddle element (empty values are dropped). | `model/moddleMapping` |
| `@flowaudit/bpmn-flowaudit` | `toMyst` | Funktion | Table as MyST Markdown, optionally with heading and target label. | `reports/tables` |
| `@flowaudit/bpmn-flowaudit` | `toWire` | Funktion | TypeScript object → JSON for `auditcore_bpmn` (snake_case keys). | `model/wire` |
| `@flowaudit/bpmn-flowaudit` | `today` | Funktion | – | `validation/context` |
| `@flowaudit/bpmn-flowaudit` | `translateModule` | Funktion | diagram-js module replacing `translate` (legacy `deutschModul`). | `i18n/translate` |
| `@flowaudit/bpmn-flowaudit` | `typeByModdleName` | Funktion | – | `schema/spec` |
| `@flowaudit/bpmn-flowaudit` | `unknownElementsModule` | Konstante | – | `diagram/unknownElementsModule` |
| `@flowaudit/bpmn-flowaudit` | `validateModel` | Funktion | – | `validation/validate` |
| `@flowaudit/bpmn-flowaudit` | `validateProfile` | Funktion | – | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `valueText` | Funktion | – | `compare/compare` |
| `@flowaudit/bpmn-flowaudit` | `verifyApproval` | Funktion | `null` if the XML equals the approved version, otherwise `BPMN-K008`. | `collection/analysis` |
| `@flowaudit/bpmn-flowaudit` | `walkthroughOverview` | Funktion | Audit steps per flow node; activities without steps separately. | `reports/processReports` |
| `@flowaudit/bpmn-flowaudit` | `walkthroughProgress` | Funktion | – | `walkthrough/walkthrough` |
| `@flowaudit/bpmn-flowaudit` | `walkthroughSteps` | Funktion | Steps of the walk-through in flow order: activities and gateways. | `walkthrough/walkthrough` |
| `@flowaudit/bpmn-flowaudit` | `withCriteria` | Funktion | Profile with injected assessment criteria (e.g. from a catalogue port). | `profile/profile` |
| `@flowaudit/bpmn-flowaudit` | `wrapWords` | Funktion | Rough word wrap to a number of characters (SVG has no text measure). | `export/svgBlocks` |
| `@flowaudit/bpmn-flowaudit` | `writeDiagramInfo` | Funktion | Editor: writes the diagram info through `modeling` (one undo step). | `model/diagramInfo` |
| `@flowaudit/bpmn-flowaudit` | `writeExtensions` | Funktion | Writes part of the extensions through `modeling` (one undo step). When the last entry disappears, `extensionElements` is removed as well. | `model/extensions` |
| `@flowaudit/bpmn-flowaudit` | `writeFlowstatValues` | Funktion | Writes FlowStat fields canonically through `modeling.updateProperties`. | `model/flowstatAttributes` |
| `@flowaudit/bpmn-flowaudit` | `writeMetadata` | Funktion | Writes (or removes) a flowaudit text entry. | `model/legacyMetadata` |
| `@flowaudit/bpmn-flowaudit` | `writeTaskToXml` | Funktion | Writes one task back; returns the new XML, or the old one if nothing matches. | `model/flowstatAttributes` |
<!-- api-overview:end -->

## Konfiguration

Profile (`@flowaudit/bpmn-flowaudit/profiles`, `defaultProfile()`) bündeln
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

`bpmn-moddle@^10.3.1`; optionaler Peer `@flowaudit/bpmn-editor@^0.1.0` (nur für
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
bpmn-moddle (MIT) über den eigenen Kern `@flowaudit/bpmn-editor`. Portiert
wurde ausschließlich FlowAudit-eigener Code aus dem audit_designer
(Paritätsinventar: `docs/bpmn/paritaet-audit-designer.md`). Die Icons sind
eigene SVG-Pfade (24 px, `currentColor`).

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
