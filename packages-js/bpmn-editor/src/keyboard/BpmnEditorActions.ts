/**
 * Zusätzliche Editor-Aktionen (über `editorActions.trigger(name)` bzw.
 * Tastenkürzel erreichbar).
 */

import type { Injector } from 'didi'
import type { Element } from 'diagram-js/lib/model/Types'

import { popupPositionFor } from '../popup-menu/position'
import { isAny } from '../util/ModelUtil'
import type { Canvas, ElementRegistry, EventBus, Selection } from '../types'

type Registrar = { register(actions: Record<string, (options?: Record<string, unknown>) => unknown>): void }

function optional<T>(injector: Injector, name: string): T | null {
  return (injector.get(name, false) as T | null) || null
}

export default class BpmnEditorActions {
  static $inject = ['eventBus', 'injector']

  constructor(eventBus: EventBus, private readonly injector: Injector) {
    eventBus.on('editorActions.init', (event: { editorActions: Registrar }) => this.register(event.editorActions))
  }

  private register(editorActions: Registrar): void {
    const injector = this.injector
    const canvas = injector.get('canvas') as Canvas
    const elementRegistry = injector.get('elementRegistry') as ElementRegistry
    const selection = injector.get('selection') as Selection
    const actions: Record<string, (options?: Record<string, unknown>) => unknown> = {}

    actions.selectElements = () => {
      const root = canvas.getRootElement()
      const elements = elementRegistry.filter((element) => element !== root && canvas.findRoot(element) === root && !element.labelTarget)
      selection.select(elements as never)
      return elements
    }
    const tool = <T>(name: string, run: (service: T) => void) => {
      const service = optional<T>(injector, name)
      if (service) actions[name] = () => run(service)
    }
    tool<{ activateSelection(event?: unknown): void }>('spaceTool', (service) => service.activateSelection())
    tool<{ activateSelection(event?: unknown): void }>('lassoTool', (service) => service.activateSelection())
    tool<{ activateHand(event?: unknown, autoActivate?: boolean, reactivate?: boolean): void }>('handTool', (service) =>
      service.activateHand(undefined, true),
    )
    const globalConnect = optional<{ start(event?: unknown): void }>(injector, 'globalConnect')
    if (globalConnect) actions.globalConnectTool = () => globalConnect.start()

    this.registerSelectionActions(actions, selection)
    this.registerViewActions(actions, canvas)
    editorActions.register(actions)
  }

  private registerSelectionActions(actions: Record<string, (options?: Record<string, unknown>) => unknown>, selection: Selection): void {
    const injector = this.injector
    const selected = () => (selection.get() as Element[]).filter((element) => !!element.parent)

    const alignElements = optional<{ trigger(elements: Element[], type: string): void }>(injector, 'alignElements')
    if (alignElements) actions.alignElements = (options) => alignElements.trigger(selected(), String(options?.type || 'left'))

    const distribute = optional<{ trigger(elements: Element[], type: string): void }>(injector, 'distributeElements')
    if (distribute) actions.distributeElements = (options) => distribute.trigger(selected(), String(options?.type || 'horizontal'))

    const modeling = optional<{ setColor(elements: Element[], colors: Record<string, unknown>): void }>(injector, 'modeling')
    if (modeling) actions.setColor = (options) => modeling.setColor(selected(), options || {})

    const labelEditing = optional<{ activate(element: Element): boolean }>(injector, 'labelEditing')
    if (labelEditing) {
      actions.directEditing = () => {
        const [element] = selected()
        return element ? labelEditing.activate(element) : false
      }
    }

    const searchPad = optional<{ toggle(): void }>(injector, 'searchPad')
    if (searchPad) actions.find = () => searchPad.toggle()

    const popupMenu = optional<{ open(target: unknown, id: string, position: unknown, options?: unknown): void }>(injector, 'popupMenu')
    if (popupMenu) {
      const canvas = injector.get('canvas') as Canvas
      actions.replaceElement = () => {
        const [element] = selected()
        if (!element || isAny(element, ['bpmn:Lane'])) return
        popupMenu.open(element, 'bpmn-replace', popupPositionFor(canvas, element))
      }
    }
  }

  private registerViewActions(actions: Record<string, (options?: Record<string, unknown>) => unknown>, canvas: Canvas): void {
    const minimap = optional<{ toggle(open?: boolean): void }>(this.injector, 'minimap')
    if (minimap) actions.toggleMinimap = () => minimap.toggle()
    actions.zoomFit = () => canvas.zoom('fit-viewport')
    actions.moveToOrigin = () => {
      const viewbox = canvas.viewbox()
      canvas.viewbox({ x: 0, y: 0, width: viewbox.width, height: viewbox.height })
    }
  }
}
