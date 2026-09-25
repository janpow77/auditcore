import { describe, expect, it } from 'vitest'
import { createEditor, svc } from './helpers/editor'

describe('Grundgerüst', () => {
  it('legt ein Diagramm an und exportiert es', async () => {
    const editor = createEditor()
    await editor.createDiagram()
    const registry = svc(editor, 'elementRegistry')
    expect(registry.get('StartEvent_1')).toBeTruthy()
    const { xml } = await editor.saveXML({ format: true })
    expect(xml).toContain('StartEvent_1')
    const { svg } = await editor.saveSVG()
    expect(svg).toContain('<svg')
  })
})
