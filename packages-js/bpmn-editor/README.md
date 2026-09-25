# @flowaudit/bpmn-editor

Eigener, vollständiger BPMN-2.0-Zeicheneditor für FlowAudit – framework-frei,
in TypeScript, auf Basis von [diagram-js](https://github.com/bpmn-io/diagram-js)
und [bpmn-moddle](https://github.com/bpmn-io/bpmn-moddle) (beide MIT).
Lizenz: **MIT** (siehe `LICENSE`). Herkunft und Clean-Room-Erklärung: `PROVENANCE.md`.

## Verwendung

```ts
import { BpmnEditor } from '@flowaudit/bpmn-editor'
import '@flowaudit/bpmn-editor/style.css'

const editor = new BpmnEditor({ container: document.getElementById('canvas')! })
await editor.importXML(xml)                 // { warnings }
const { xml: saved } = await editor.saveXML({ format: true })
const { svg } = await editor.saveSVG()
await editor.createDiagram()                // leeres Diagramm mit Startereignis

const modeling = editor.get('modeling')
modeling.updateProperties(element, { name: 'Antrag prüfen' })
modeling.setColor([element], { fill: '#dbeafe', stroke: '#1d4ed8' })
editor.on('selection.changed', (event) => { /* … */ })
editor.destroy()
```

Optionen: `container`, `additionalModules` (diagram-js-Module), `moddleExtensions`
(z. B. `{ flowaudit: descriptor }`), `keyboard`, `gridSize` (Standard 10),
`locale` (`'de'` Standard, `'en'`), `config` (z. B. `bpmnRenderer`,
`colorPicker.colors`, `minimap.open`, `grid.visible`).

Weitere Beschreibung (Architektur, Dienste, Elementumfang): `docs/bpmn/editor.md`
im Repository.

## Entwicklung

```sh
npm ci                                   # im Repository-Stamm
npm run test -w @flowaudit/bpmn-editor
npm run build -w @flowaudit/bpmn-editor  # dist/: ESM, Typen, CSS
npm run demo -w @flowaudit/bpmn-editor   # Demo-Seite zur Sichtprüfung
```
