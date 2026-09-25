/**
 * Builds the `ProcessModel` from moddle definitions or a running editor.
 */

import type { Canvas, ElementRegistry, ModdleElement } from '../diagram/services'
import type { DiagramInfo } from '../schema/types'
import { readExtensions } from './extensions'
import { colorFromDi, createModelElement, type ModelElement, type ProcessModel } from './processModel'

function list(bo: ModdleElement | undefined, name: string): ModdleElement[] {
  return (bo?.get(name) as ModdleElement[] | undefined) ?? []
}

function rootElements(definitions: ModdleElement): ModdleElement[] {
  return list(definitions, 'rootElements')
}

/** Main element: the collaboration, otherwise the first process. */
export function mainElement(definitions: ModdleElement): ModdleElement | null {
  const roots = rootElements(definitions)
  return roots.find((el) => el.$type === 'bpmn:Collaboration') ?? roots.find((el) => el.$type === 'bpmn:Process') ?? null
}

/** Diagram info: collaboration first, then processes in document order. */
export function readDiagramInfo(definitions: ModdleElement): DiagramInfo | null {
  const roots = rootElements(definitions)
  const candidates = [...roots.filter((el) => el.$type === 'bpmn:Collaboration'), ...roots.filter((el) => el.$type === 'bpmn:Process')]
  for (const candidate of candidates) {
    const info = readExtensions(candidate).diagramInfo
    if (info) return info
  }
  return null
}

class ModelBuilder {
  readonly elements: ModelElement[] = []
  readonly byId = new Map<string, ModelElement>()
  /** Flow node id → chain of lanes from outermost to innermost. */
  readonly laneChains = new Map<string, ModdleElement[]>()
  readonly poolByProcess = new Map<string, ModdleElement>()
  readonly pools = new Map<string, ModdleElement>()

  add(element: ModelElement): ModelElement {
    if (element.id && !this.byId.has(element.id)) {
      this.elements.push(element)
      this.byId.set(element.id, element)
    }
    return element
  }

  collaboration(collaboration: ModdleElement): void {
    for (const participant of list(collaboration, 'participants')) {
      this.add(createModelElement(participant))
      this.pools.set(String(participant.id), participant)
      const process = participant.get('processRef') as ModdleElement | undefined
      if (process) this.poolByProcess.set(String(process.id), participant)
    }
    for (const flow of list(collaboration, 'messageFlows')) this.add(createModelElement(flow))
    for (const artifact of list(collaboration, 'artifacts')) this.add(createModelElement(artifact))
  }

  lanes(laneSet: ModdleElement | undefined, pool: ModdleElement | undefined, parents: ModdleElement[]): void {
    for (const lane of list(laneSet, 'lanes')) {
      const element = this.add(createModelElement(lane))
      if (pool) element.poolId = String(pool.id)
      const chain = [...parents, lane]
      for (const node of list(lane, 'flowNodeRef')) {
        const previous = this.laneChains.get(String(node.id))
        if (!previous || previous.length < chain.length) this.laneChains.set(String(node.id), chain)
      }
      this.lanes(lane.get('childLaneSet') as ModdleElement | undefined, pool, chain)
    }
  }

  container(container: ModdleElement, pool: ModdleElement | undefined, processId: string): void {
    for (const laneSet of list(container, 'laneSets')) this.lanes(laneSet, pool, [])
    for (const bo of list(container, 'flowElements')) {
      const element = this.add(createModelElement(bo))
      Object.assign(element, { parentId: String(container.id), processId }, pool ? { poolId: String(pool.id) } : {})
      if (bo.get('flowElements')) this.container(bo, pool, processId)
    }
    for (const artifact of list(container, 'artifacts')) {
      this.add(createModelElement(artifact)).parentId = String(container.id)
    }
  }

  assignActors(): void {
    for (const element of this.elements) {
      const chain = this.laneChains.get(element.id) ?? []
      if (chain.length) element.laneId = String(chain[chain.length - 1].id)
      const candidates = [...chain].reverse()
      const pool = element.poolId ? this.pools.get(element.poolId) : undefined
      if (pool) candidates.push(pool)
      const withActor = candidates.find((candidate) => {
        const actor = readExtensions(candidate).actor
        return Boolean(actor?.role || actor?.displayName)
      })
      const carrier = withActor ?? candidates[0]
      if (!carrier) continue
      const actor = withActor ? readExtensions(withActor).actor : undefined
      element.actor = { ...actor, sourceId: String(carrier.id), sourceName: String(carrier.get('name') ?? '') }
    }
  }

  diagramInterchange(definitions: ModdleElement): void {
    for (const diagram of list(definitions, 'diagrams')) {
      const plane = diagram.get('plane') as ModdleElement | undefined
      for (const di of list(plane, 'planeElement')) this.applyDi(di)
    }
  }

  private applyDi(di: ModdleElement): void {
    const ref = di.get('bpmnElement') as ModdleElement | undefined
    const element = ref ? this.byId.get(String(ref.id)) : undefined
    if (!element) return
    const bounds = di.get('bounds') as ModdleElement | undefined
    if (bounds) {
      element.bounds = {
        x: Number(bounds.get('x')),
        y: Number(bounds.get('y')),
        width: Number(bounds.get('width')),
        height: Number(bounds.get('height')),
      }
    }
    const color = colorFromDi(di)
    if (color) element.color = color
  }
}

/** Builds the model from moddle definitions (headless). */
export function modelFromDefinitions(definitions: ModdleElement): ProcessModel {
  const builder = new ModelBuilder()
  const roots = rootElements(definitions)
  for (const root of roots.filter((el) => el.$type === 'bpmn:Collaboration')) builder.collaboration(root)
  for (const process of roots.filter((el) => el.$type === 'bpmn:Process')) {
    builder.add(createModelElement(process))
    builder.container(process, builder.poolByProcess.get(String(process.id)), String(process.id))
  }
  builder.assignActors()
  builder.diagramInterchange(definitions)
  const main = mainElement(definitions)
  return { info: readDiagramInfo(definitions), mainId: main ? String(main.id) : null, elements: builder.elements, byId: builder.byId }
}

/** Definitions behind the root element of a running editor. */
export function definitionsOf(canvas: Canvas): ModdleElement | undefined {
  let current: ModdleElement | undefined = canvas.getRootElement()?.businessObject
  while (current && current.$type !== 'bpmn:Definitions') current = current.$parent
  return current
}

/** Builds the model from a running editor, using the current shape bounds. */
export function modelFromEditor(services: { canvas: Canvas; elementRegistry: ElementRegistry }): ProcessModel {
  const definitions = definitionsOf(services.canvas)
  const model: ProcessModel = definitions
    ? modelFromDefinitions(definitions)
    : { info: null, mainId: null, elements: [], byId: new Map() }
  for (const shape of services.elementRegistry.getAll()) {
    const element = model.byId.get(shape.id)
    if (!element || shape.labelTarget) continue
    if (typeof shape.x === 'number' && typeof shape.width === 'number') {
      element.bounds = { x: shape.x, y: shape.y ?? 0, width: shape.width, height: shape.height ?? 0 }
    }
    const color = colorFromDi(shape.di)
    if (color) element.color = color
  }
  return model
}
