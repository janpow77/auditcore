/**
 * Befehle zum Ändern von Eigenschaften, Farben, Kennungen und der
 * Diagrammwurzel. Alle Befehle sind rückgängig machbar.
 */

import { getIds } from '../../util/Ids'
import { addToList, getBusinessObject, getDefinitions, getDi, is, removeFromList } from '../../util/ModelUtil'
import type { BpmnElement, ElementRegistry, Moddle, ModdleElement } from '../../types'

type Properties = Record<string, unknown>

function getProperties(target: ModdleElement, keys: string[]): Properties {
  const result: Properties = {}
  for (const key of keys) result[key] = target.get(key)
  return result
}

function setProperties(target: ModdleElement, properties: Properties): void {
  for (const [key, value] of Object.entries(properties)) target.set(key, value)
}

interface IdChange {
  oldId: string
  newId: string
  oldDiId?: string
}

/** Wechselt die Kennung samt DI-Kennung, Registry-Eintrag und Beschriftung. */
class IdSwitch {
  constructor(
    private readonly moddle: Moddle,
    private readonly elementRegistry: ElementRegistry,
  ) {}

  apply(element: BpmnElement, bo: ModdleElement, from: string, to: string, diFrom?: string, diTo?: string): void {
    const ids = getIds(this.moddle)
    ids.unclaim(from)
    ids.claim(to, bo)
    bo.id = to
    if (this.elementRegistry.get(from) === element) this.elementRegistry.updateId(element, to)
    const label = element.label as BpmnElement | undefined
    if (label && this.elementRegistry.get(`${from}_label`) === label) this.elementRegistry.updateId(label, `${to}_label`)
    const di = element.di
    if (di && diFrom && diTo && di.id === diFrom) {
      ids.unclaim(diFrom)
      di.id = diTo
      ids.claim(diTo, di)
    }
  }

  change(element: BpmnElement, bo: ModdleElement, newId: string): IdChange {
    const oldId = bo.id as string
    const oldDiId = element.di?.id === `${oldId}_di` ? `${oldId}_di` : undefined
    this.apply(element, bo, oldId, newId, oldDiId, oldDiId ? `${newId}_di` : undefined)
    return { oldId, newId, oldDiId }
  }

  revert(element: BpmnElement, bo: ModdleElement, change: IdChange): void {
    const diNow = change.oldDiId ? `${change.newId}_di` : undefined
    this.apply(element, bo, change.newId, change.oldId, diNow, change.oldDiId)
  }
}

interface UpdatePropertiesContext {
  element: BpmnElement
  properties: Properties & { di?: Properties; id?: string; default?: ModdleElement }
  oldProperties?: Properties
  oldDiProperties?: Properties
  idChange?: IdChange
  changed?: BpmnElement[]
}

export class UpdatePropertiesHandler {
  static $inject = ['elementRegistry', 'moddle']

  private readonly ids: IdSwitch

  constructor(
    private readonly elementRegistry: ElementRegistry,
    moddle: Moddle,
  ) {
    this.ids = new IdSwitch(moddle, elementRegistry)
  }

  execute(context: UpdatePropertiesContext): BpmnElement[] {
    const { element } = context
    const bo = getBusinessObject(element)
    const { di: diProperties, id, ...properties } = context.properties
    const changed = [element, ...this.defaultFlowChanges(bo, properties)]
    const di = getDi(element)
    if (diProperties && di) {
      context.oldDiProperties = getProperties(di, Object.keys(diProperties))
      setProperties(di, diProperties)
    }
    if (id && id !== bo.id) context.idChange = this.ids.change(element, bo, id)
    context.oldProperties = getProperties(bo, Object.keys(properties))
    setProperties(bo, properties)
    if (element.label) changed.push(element.label as BpmnElement)
    context.changed = changed
    return changed
  }

  /** Beim Wechsel des Standardflusses beide Kanten neu zeichnen. */
  private defaultFlowChanges(bo: ModdleElement, properties: Properties): BpmnElement[] {
    if (!('default' in properties)) return []
    const next = properties.default as ModdleElement | undefined
    return [bo.default?.id, next?.id]
      .map((flowId) => (flowId ? this.elementRegistry.get(flowId) : undefined))
      .filter((flow): flow is BpmnElement => !!flow)
  }

  revert(context: UpdatePropertiesContext): BpmnElement[] {
    const { element } = context
    const bo = getBusinessObject(element)
    setProperties(bo, context.oldProperties || {})
    const di = getDi(element)
    if (context.oldDiProperties && di) setProperties(di, context.oldDiProperties)
    if (context.idChange) this.ids.revert(element, bo, context.idChange)
    return context.changed || [element]
  }
}

interface UpdateModdlePropertiesContext {
  element: BpmnElement
  moddleElement: ModdleElement
  properties: Properties & { id?: string }
  oldProperties?: Properties
  idChange?: IdChange
  changed?: BpmnElement[]
}

export class UpdateModdlePropertiesHandler {
  static $inject = ['elementRegistry', 'moddle']

  private readonly ids: IdSwitch

  constructor(elementRegistry: ElementRegistry, moddle: Moddle) {
    this.ids = new IdSwitch(moddle, elementRegistry)
  }

  execute(context: UpdateModdlePropertiesContext): BpmnElement[] {
    const { element, moddleElement } = context
    if (!moddleElement) throw new Error('moddleElement fehlt')
    const { id, ...properties } = context.properties
    const bo = getBusinessObject(element)
    if (id && moddleElement === bo && id !== bo.id) context.idChange = this.ids.change(element, bo, id)
    else if (id !== undefined) properties.id = id
    context.oldProperties = getProperties(moddleElement, Object.keys(properties))
    setProperties(moddleElement, properties)
    context.changed = element.label ? [element, element.label as BpmnElement] : [element]
    return context.changed
  }

  revert(context: UpdateModdlePropertiesContext): BpmnElement[] {
    setProperties(context.moddleElement, context.oldProperties || {})
    if (context.idChange) this.ids.revert(context.element, getBusinessObject(context.element), context.idChange)
    return context.changed || [context.element]
  }
}

const COLOR_KEYS = ['bioc:fill', 'bioc:stroke', 'color:background-color', 'color:border-color']

interface SetColorContext {
  elements: BpmnElement[]
  colors: { fill?: string | null; stroke?: string | null }
  oldColors?: Map<BpmnElement, Properties>
  changed?: BpmnElement[]
}

function applyColor(di: ModdleElement, colors: SetColorContext['colors']): void {
  if ('fill' in colors) {
    di.set('bioc:fill', colors.fill || undefined)
    di.set('color:background-color', colors.fill || undefined)
  }
  if ('stroke' in colors) {
    di.set('bioc:stroke', colors.stroke || undefined)
    di.set('color:border-color', colors.stroke || undefined)
    if (di.label) di.label.set('color:color', colors.stroke || undefined)
  }
}

export class SetColorHandler {
  execute(context: SetColorContext): BpmnElement[] {
    const changed: BpmnElement[] = []
    context.oldColors = new Map()
    for (const raw of context.elements) {
      const element = (raw.labelTarget as BpmnElement | undefined) || raw
      const di = getDi(element)
      if (!di) continue
      context.oldColors.set(element, { ...getProperties(di, COLOR_KEYS), label: di.label?.get('color:color') })
      applyColor(di, context.colors || {})
      changed.push(element)
      if (element.label) changed.push(element.label as BpmnElement)
    }
    context.changed = changed
    return changed
  }

  revert(context: SetColorContext): BpmnElement[] {
    for (const [element, old] of context.oldColors || []) {
      const di = getDi(element)
      if (!di) continue
      for (const key of COLOR_KEYS) di.set(key, old[key])
      if (di.label) di.label.set('color:color', old.label)
    }
    return context.changed || []
  }
}

interface UpdateRootContext {
  newBusinessObject: ModdleElement
  keepOld?: boolean
  rootElement?: BpmnElement
  definitions?: ModdleElement
  oldBusinessObject?: ModdleElement
  oldIndex?: number
}

/**
 * Tauscht das semantische Objekt der Diagrammwurzel (Prozess ↔ Kollaboration).
 * Kontext: `{ newBusinessObject, keepOld }`.
 */
export class UpdateCanvasRootHandler {
  static $inject = ['canvas', 'elementRegistry', 'moddle']

  constructor(
    private readonly canvas: { getRootElement(): unknown },
    private readonly elementRegistry: ElementRegistry,
    private readonly moddle: Moddle,
  ) {}

  execute(context: UpdateRootContext): BpmnElement[] {
    const root = context.rootElement || (this.canvas.getRootElement() as BpmnElement)
    const oldBo = root.businessObject
    const newBo = context.newBusinessObject
    const definitions = getDefinitions(oldBo) || context.definitions
    if (!definitions) throw new Error('Definitionen fehlen')
    Object.assign(context, { rootElement: root, oldBusinessObject: oldBo, definitions })
    const rootElements = definitions.get<ModdleElement[]>('rootElements')
    context.oldIndex = rootElements.indexOf(oldBo)
    if (!context.keepOld) removeFromList(rootElements, oldBo)
    addToList(rootElements, newBo, is(newBo, 'bpmn:Collaboration') ? 0 : Math.max(0, context.oldIndex))
    newBo.$parent = definitions
    this.switchRoot(root, newBo)
    getIds(this.moddle).claim(newBo.id as string, newBo)
    return [root]
  }

  revert(context: UpdateRootContext): BpmnElement[] {
    const root = context.rootElement as BpmnElement
    const oldBo = context.oldBusinessObject as ModdleElement
    const rootElements = (context.definitions as ModdleElement).get<ModdleElement[]>('rootElements')
    removeFromList(rootElements, context.newBusinessObject)
    if (!context.keepOld) addToList(rootElements, oldBo, Math.max(0, context.oldIndex ?? 0))
    this.switchRoot(root, oldBo)
    return [root]
  }

  private switchRoot(root: BpmnElement, bo: ModdleElement): void {
    if (root.di) root.di.bpmnElement = bo
    root.businessObject = bo
    this.elementRegistry.updateId(root, bo.id as string)
  }
}

interface IdClaimContext {
  id: string
  element: ModdleElement
  claiming: boolean
}

export class IdClaimHandler {
  static $inject = ['moddle']

  constructor(private readonly moddle: Moddle) {}

  execute(context: IdClaimContext): BpmnElement[] {
    const ids = getIds(this.moddle)
    if (context.claiming) ids.claim(context.id, context.element)
    else ids.unclaim(context.id)
    return []
  }

  revert(context: IdClaimContext): BpmnElement[] {
    const ids = getIds(this.moddle)
    if (context.claiming) ids.unclaim(context.id)
    else ids.claim(context.id, context.element)
    return []
  }
}
