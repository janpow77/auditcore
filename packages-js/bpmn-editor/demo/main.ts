/**
 * Demo-Seite für die lokale Sichtprüfung (nicht Teil des Pakets).
 * Aufruf: `npm run demo -w @auditcore/bpmn-editor`, dann ?datei=… wählen.
 */

import { BpmnEditor } from '../src'
import alleElemente from '../test/fixtures/synthetisch/alle-elemente.bpmn?raw'
import verfahren from '../test/fixtures/synthetisch/verwaltungsverfahren.bpmn?raw'

const FILES: Record<string, string> = { 'alle-elemente': alleElemente, verwaltungsverfahren: verfahren }

const container = document.getElementById('canvas') as HTMLElement
const editor = new BpmnEditor({ container, keyboard: { bindTo: document }, config: { minimap: { open: true } } })
const name = new URLSearchParams(location.search).get('datei')
const xml = name ? FILES[name] : undefined
const ready = xml ? editor.importXML(xml) : editor.createDiagram()
ready.then(() => {
  editor.get<{ zoom(value: string): void }>('canvas').zoom('fit-viewport')
  document.body.dataset.bereit = 'ja'
})
Object.assign(window, { editor })
