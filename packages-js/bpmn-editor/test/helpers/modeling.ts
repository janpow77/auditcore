import type { BpmnEditor } from '../../src'
import type BpmnReplace from '../../src/replace/BpmnReplace'
import type BpmnRules from '../../src/rules/BpmnRules'
import type ElementFactory from '../../src/modeling/ElementFactory'
import type Modeling from '../../src/modeling/Modeling'
import type { BpmnElement, Canvas, CommandStack, CreatedElement, ElementRegistry, Moddle } from '../../src/types'
import { createEditor } from './editor'

/* Testhilfen: kleine Diagramme per API aufbauen. */

export interface Kit {
  editor: BpmnEditor
  modeling: Modeling
  elementFactory: ElementFactory
  registry: ElementRegistry
  canvas: Canvas
  commandStack: CommandStack
  rules: BpmnRules
  replace: BpmnReplace
  moddle: Moddle
  root: () => BpmnElement
  get: (id: string) => CreatedElement
  create: (type: string, x: number, y: number, parent?: BpmnElement, attrs?: Record<string, unknown>) => CreatedElement
  xml: () => Promise<string>
}

export async function createKit(xml?: string): Promise<Kit> {
  const editor = createEditor()
  if (xml) await editor.importXML(xml)
  else await editor.createDiagram()
  const modeling = editor.get<Modeling>('modeling')
  const elementFactory = editor.get<ElementFactory>('elementFactory')
  const canvas = editor.get<Canvas>('canvas')
  const registry = editor.get<ElementRegistry>('elementRegistry')
  const root = () => canvas.getRootElement() as unknown as BpmnElement
  return {
    editor,
    modeling,
    elementFactory,
    canvas,
    registry,
    commandStack: editor.get<CommandStack>('commandStack'),
    rules: editor.get<BpmnRules>('bpmnRules'),
    replace: editor.get<BpmnReplace>('bpmnReplace'),
    moddle: editor.get<Moddle>('moddle'),
    root,
    get: (id) => {
      const element = registry.get(id)
      if (!element) throw new Error(`Element ${id} fehlt`)
      return element as CreatedElement
    },
    create: (type, x, y, parent, attrs = {}) => {
      const shape = elementFactory.createShape({ type, ...attrs })
      return modeling.createShape(shape, { x, y }, (parent || root()) as never) as unknown as CreatedElement
    },
    xml: async () => (await editor.saveXML({ format: true })).xml,
  }
}

/** Kinder eines Elements eines bestimmten Typs, nach Lage sortiert. */
export function childrenOfType(parent: BpmnElement, type: string): CreatedElement[] {
  return ((parent.children || []) as CreatedElement[]).filter((child) => child.type === type).sort((a, b) => a.y - b.y || a.x - b.x)
}
