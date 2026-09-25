import { BpmnEditor, type EditorOptions } from '../../src'

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
  const editor = new BpmnEditor({ container: createContainer(), ...options })
  // happy-dom rechnet kein Layout: Größe der Zeichenfläche vorgeben.
  for (const element of [editor.container, editor.container.querySelector('.djs-container')]) {
    if (!element) continue
    Object.defineProperty(element, 'clientWidth', { value: 1200, configurable: true })
    Object.defineProperty(element, 'clientHeight', { value: 800, configurable: true })
  }
  return editor
}

export async function importXml(xml: string, options: Partial<EditorOptions> = {}): Promise<{ editor: BpmnEditor; warnings: string[] }> {
  const editor = createEditor(options)
  const result = await editor.importXML(xml)
  return { editor, warnings: result.warnings }
}
