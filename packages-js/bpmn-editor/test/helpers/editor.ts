import { BpmnEditor, type EditorOptions } from '../../src'

/* eslint-disable @typescript-eslint/no-explicit-any */

export function createContainer(): HTMLElement {
  const container = document.createElement('div')
  Object.defineProperty(container, 'clientWidth', { value: 1200, configurable: true })
  Object.defineProperty(container, 'clientHeight', { value: 800, configurable: true })
  container.style.width = '1200px'
  container.style.height = '800px'
  document.body.appendChild(container)
  return container
}

export function createEditor(options: Partial<EditorOptions> = {}): BpmnEditor {
  return new BpmnEditor({ container: createContainer(), ...options })
}

export async function importXml(xml: string, options: Partial<EditorOptions> = {}) {
  const editor = createEditor(options)
  const result = await editor.importXML(xml)
  return { editor, warnings: result.warnings }
}

export function svc<T = any>(editor: BpmnEditor, name: string): T {
  return editor.get<T>(name)
}
