import type { BpmnEditor } from '../../src'
import { createEditor } from './editor'

/* Testhilfen: kleine Diagramme per API aufbauen. */

export interface Kit {
  editor: BpmnEditor
  modeling: any
  elementFactory: any
  registry: any
  canvas: any
  commandStack: any
  rules: any
  replace: any
  root: () => any
  create: (type: string, x: number, y: number, parent?: any, attrs?: Record<string, unknown>) => any
  xml: () => Promise<string>
}

export async function createKit(): Promise<Kit> {
  const editor = createEditor()
  await editor.createDiagram()
  const modeling = editor.get<any>('modeling')
  const elementFactory = editor.get<any>('elementFactory')
  const canvas = editor.get<any>('canvas')
  const kit: Kit = {
    editor,
    modeling,
    elementFactory,
    canvas,
    registry: editor.get('elementRegistry'),
    commandStack: editor.get('commandStack'),
    rules: editor.get('bpmnRules'),
    replace: editor.get('bpmnReplace'),
    root: () => canvas.getRootElement(),
    create: (type, x, y, parent, attrs = {}) => {
      const shape = elementFactory.createShape({ type, ...attrs })
      return modeling.createShape(shape, { x, y }, parent || canvas.getRootElement())
    },
    xml: async () => (await editor.saveXML({ format: true })).xml,
  }
  return kit
}
