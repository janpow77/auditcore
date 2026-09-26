# @auditcore/bpmn-editor

## Zweck

Eigener, vollständiger BPMN-2.0-Zeicheneditor in TypeScript auf Basis von diagram-js und bpmn-moddle, framework-frei und unter MIT-Lizenz.

Für FlowAudit-Anwendungen, die Geschäftsprozesse modellieren und prüfen –
er löst bpmn-js im audit_designer ab. Fachliche FlowAudit-Erweiterungen und
Vue-/React-Oberflächen gehören nicht in dieses Paket, sondern setzen auf ihm
auf (`additionalModules`, `moddleExtensions`).

## Installation

Standardweg ist die npm-Registry; npm löst die übrigen `@auditcore`-Pakete
der Abhängigkeitshülle selbst auf:

```sh
npm install @auditcore/bpmn-editor
```

Ohne Registry-Zugang (Intranet, offline) bleibt der signierte Tarball aus
dem GitHub-Release von auditcore; dann gehört jedes Paket der Hülle
ausdrücklich in die `package.json`:

```sh
npm install @auditcore/bpmn-editor@https://github.com/janpow77/auditcore/releases/download/v<release>/auditcore-bpmn-editor-0.1.1.tgz
```

Anleitung für Vue, React und Web Components mit Integritätsprüfung und
`vendor/`-Ablage:
[frontend-installation.md](../../docs/deployment/frontend-installation.md).

Keine weiteren `@auditcore`-Pakete. Stile: `@auditcore/bpmn-editor/style.css`.

Im auditcore-Repository gehört das Paket zum npm-Workspace (`npm ci` im
Stamm, Bau mit `npm run build -w @auditcore/bpmn-editor`).

## Schnellstart

```ts
import { BpmnEditor, INITIAL_DIAGRAM } from '@auditcore/bpmn-editor'
import '@auditcore/bpmn-editor/style.css'

interface Modeling {
  updateProperties(element: unknown, properties: Record<string, unknown>): void
  setColor(elements: unknown[], colors: { fill?: string; stroke?: string }): void
}
interface ElementRegistry {
  get(id: string): unknown
}

const container = document.getElementById('canvas')
if (!container) throw new Error('Zeichenfläche fehlt')

const editor = new BpmnEditor({ container, locale: 'de', gridSize: 10 })
const { warnings } = await editor.importXML(INITIAL_DIAGRAM)
console.log(warnings.length === 0 ? 'Import ohne Warnungen' : warnings)

const start = editor.get<ElementRegistry>('elementRegistry').get('StartEvent_1')
const modeling = editor.get<Modeling>('modeling')
modeling.updateProperties(start, { name: 'Antrag eingegangen' })
modeling.setColor([start], { fill: '#dbeafe', stroke: '#1d4ed8' })

editor.on('selection.changed', (event) => console.log(event))
const { xml } = await editor.saveXML({ format: true })
const { svg } = await editor.saveSVG()
console.log(xml.length, svg.length)
editor.destroy()
```

## Einbindung

- **Framework-frei:** `new BpmnEditor({ container, … })` in ein beliebiges
  DOM-Element; das Paket bringt keine Vue-, React- oder Web-Component-Hülle
  mit. Die FlowAudit-Fachschicht und Vue-Komponenten (`@auditcore/bpmn-flowaudit`,
  `@auditcore/bpmn-vue`) sind eigene Pakete und setzen auf diesem Kern auf.
- **Erweitern:** zusätzliche diagram-js-Module über `additionalModules`,
  eigene Namensräume über `moddleExtensions`
  (z. B. `{ flowaudit: descriptor }`); Dienste über `editor.get(name)`,
  Ereignisse über `editor.on(event, callback)`.
- `createDiagram()` legt ein leeres Diagramm mit Startereignis an
  (`INITIAL_DIAGRAM`).

Architektur, Dienste, Ereignisse und Elementumfang:
[`docs/bpmn/editor.md`](../../docs/bpmn/editor.md).

## API-Überblick

`BpmnEditor`: `importXML(xml)` → `{ warnings }`, `saveXML({ format })` →
`{ xml }`, `saveSVG()` → `{ svg }`, `createDiagram()`, `get<T>(service)`,
`on(event, callback, priority?)`/`off`, `destroy()`, `getDefinitions()`,
`importDefinitions(definitions)`, `clear()`, `container`. Wichtige Dienste:
`modeling`, `bpmnRules`, `bpmnReplace`, `elementRegistry`, `canvas`,
`selection`, `commandStack`, `copyPaste`, `minimap`, `subProcessPlanes`,
`editorActions`, `translate`.

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Exporte der Einstiegspunkte aus `package.json#exports` (25):

| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |
|---|---|---|---|---|
| `@auditcore/bpmn-editor` | `BIOC_NAMESPACE` | Konstante | – | `moddle/createModdle` |
| `@auditcore/bpmn-editor` | `BpmnEditor` | Klasse | – | `BpmnEditor` |
| `@auditcore/bpmn-editor` | `COLOR_NAMESPACE` | Konstante | – | `moddle/createModdle` |
| `@auditcore/bpmn-editor` | `DEFAULT_MODULES` | Konstante | – | `modules` |
| `@auditcore/bpmn-editor` | `EditorOptions` | Schnittstelle | – | `BpmnEditor` |
| `@auditcore/bpmn-editor` | `INITIAL_DIAGRAM` | Konstante | Leeres Diagramm mit einem Startereignis (Ausgangspunkt für `createDiagram`). | `initialDiagram` |
| `@auditcore/bpmn-editor` | `ImportXMLResult` | Schnittstelle | – | `BpmnEditor` |
| `@auditcore/bpmn-editor` | `Translate` | Typ | – | `i18n/translate` |
| `@auditcore/bpmn-editor` | `createModdle` | Funktion | Erzeugt eine moddle-Instanz mit BPMN 2.0 samt DI und den Farb-Namensräumen `bioc` und `color` (beide bringt bpmn-moddle mit) sowie beliebigen zusätzlichen Erweiterungen (z. B. | `moddle/createModdle` |
| `@auditcore/bpmn-editor` | `createTranslate` | Funktion | – | `i18n/translate` |
| `@auditcore/bpmn-editor` | `getBusinessObject` | Funktion | Liefert das semantische Objekt eines Diagrammelements (oder das Objekt selbst). | `util/ModelUtil` |
| `@auditcore/bpmn-editor` | `getDi` | Funktion | Liefert die DI eines Diagrammelements; Beschriftungen teilen die DI ihres Ziels. | `util/ModelUtil` |
| `@auditcore/bpmn-editor` | `getEventDefinition` | Funktion | – | `util/ModelUtil` |
| `@auditcore/bpmn-editor` | `getLabel` | Funktion | Name bzw. Text der Beschriftung. | `util/LabelUtil` |
| `@auditcore/bpmn-editor` | `hasEventDefinition` | Funktion | – | `util/ModelUtil` |
| `@auditcore/bpmn-editor` | `is` | Funktion | Prüft, ob ein Element (oder moddle-Objekt) vom angegebenen Typ ist. | `util/ModelUtil` |
| `@auditcore/bpmn-editor` | `isAny` | Funktion | Prüft, ob ein Element einem der Typen entspricht. | `util/ModelUtil` |
| `@auditcore/bpmn-editor` | `isEventSubProcess` | Funktion | – | `util/ModelUtil` |
| `@auditcore/bpmn-editor` | `isExpanded` | Funktion | Aufgeklappt? Gilt für Teilprozesse, Pools und Aufrufaktivitäten. | `util/ModelUtil` |
| `@auditcore/bpmn-editor` | `isHorizontal` | Funktion | Waagerechte Ausrichtung eines Pools bzw. einer Bahn (Standard: ja). | `util/ModelUtil` |
| `@auditcore/bpmn-editor` | `isInterrupting` | Funktion | Unterbrechend? Randereignisse über `cancelActivity`, Startereignisse über `isInterrupting`. | `util/ModelUtil` |
| `@auditcore/bpmn-editor` | `isLabelExternal` | Funktion | Hat das Element eine eigenständig verschiebbare (externe) Beschriftung? | `util/LabelUtil` |
| `@auditcore/bpmn-editor` | `setLabel` | Funktion | Setzt den Beschriftungstext direkt am moddle-Objekt (ohne Befehlsstapel). | `util/LabelUtil` |
| `@auditcore/bpmn-editor` | `setTextMeasure` | Funktion | Erlaubt Tests oder Anwendungen, die Messfunktion auszutauschen. | `draw/TextLayout` |
| `@auditcore/bpmn-editor` | `translations` | Konstante | – | `i18n/translations` |
<!-- api-overview:end -->

## Konfiguration

`EditorOptions`:

| Option | Bedeutung |
|---|---|
| `container` | DOM-Element der Zeichenfläche (Pflicht) |
| `additionalModules` | weitere diagram-js-Module |
| `moddleExtensions` | moddle-Beschreibungen weiterer Namensräume |
| `keyboard` | `{ bindTo }` wird angenommen, aber nicht weitergegeben: diagram-js 15 bindet Tastenkürzel an die fokussierte Zeichenfläche |
| `gridSize` | Rasterweite in Pixeln, Standard 10 |
| `locale` | `'de'` (Standard) oder `'en'`; eigene Texte über `createTranslate(locale, extra)` |
| `config` | Konfiguration einzelner Module, z. B. `bpmnRenderer`, `colorPicker.colors`, `minimap.open`, `grid.visible` |

Farben werden an der DI in beiden üblichen Namensräumen geschrieben
(`bioc:fill`/`bioc:stroke` und `color:background-color`/`color:border-color`,
`BIOC_NAMESPACE`, `COLOR_NAMESPACE`). `setTextMeasure` ersetzt die
Textmessung (etwa in Tests ohne Layout-Engine).

## Herkunft und Charakterisierung

Neu im Clean-Room-Verfahren geschrieben (PR #76). Grundlage waren
ausschließlich die OMG-BPMN-2.0.2-Spezifikation, diagram-js und
bpmn-moddle/moddle (MIT) sowie der eigene Code des audit_designer für
Schnittstellen-Kompatibilität (Dienstnamen, Farbattribute, DI-Zugriff).
`bpmn-js`, `bpmn-js-properties-panel`, `@bpmn-io/properties-panel` und
`bpmn-font` wurden weder verwendet noch gelesen; `npm run license-check`
schlägt fehl, sobald eines davon im Lockfile auftaucht. Rundlauf-Tests:
Export ohne Bearbeitung entspricht exakt dem kanonisch serialisierten
Original (synthetische Fixtures, Beispiel-XML aus Tests des audit_designer);
lokal zusätzlich gegen nicht veröffentlichte Nutzerdiagramme
(`BPMN_LOCAL_FIXTURES`). Bekannte Grenzen: Diagramme ohne DI werden
durchgereicht, aber nicht angezeigt; beim Kopieren von Pools wird die
Bahn-Verschachtelung flach eingefügt.

## Abhängigkeiten

Laufzeit (alle MIT):

- `diagram-js` ^15.27.1
- `bpmn-moddle` ^10.3.1
- `didi` ^11.0.0
- `min-dash` ^5.1.0
- `min-dom` ^5.3.0
- `tiny-svg` ^4.1.4

Transitive Laufzeitpakete mit Lizenz stehen in `PROVENANCE.md`. Keine
Peer-Abhängigkeiten, Node ≥ 20.19 für Bau und Tests.

## Sicherheit und Datenschutz

BPMN-XML wird mit bpmn-moddle geparst; unbekannte Erweiterungen und Attribute
bleiben erhalten und werden unverändert wieder ausgegeben. Beschriftungen
werden als Text (`textContent`/SVG-`tspan`) gesetzt, `innerHTML` nur für die
eigenen, statischen Symbole. Der Editor lädt nichts nach, greift nicht auf
das Netzwerk zu und speichert nichts; Diagramme (die Namen und
Organisationsangaben enthalten können) liegen allein bei der Anwendung.
Nutzerdiagramme werden nicht eingecheckt.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Herkunft, Clean-Room-Erklärung, Laufzeitlizenzen und
Testdaten: `PROVENANCE.md`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
