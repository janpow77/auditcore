/**
 * Befehle zum Ändern von Eigenschaften, Farben, Beschriftungen, Kennungen
 * und der Diagrammwurzel. Alle Befehle sind rückgängig machbar.
 */

import { getIds } from '../../util/Ids'
import {
  addToList,
  getBusinessObject,
  getDefinitions,
  getDi,
  is,
  removeFromList,
} from '../../util/ModelUtil'
import {
  getExternalLabelMid,
  getExternalLabelSize,
  getLabel,
  isLabelExternal,
  setLabel,
} from '../../util/LabelUtil'

/* eslint-disable @typescript-eslint/no-explicit-any */

function getProperties(target: any, keys: string[]): Record<string, any> {
  const result: Record<string, any> = {}
  for (const key of keys) result[key] = target.get ? target.get(key) : target[key]
  return result
}

function setProperties(target: any, properties: Record<string, any>): void {
  for (const [key, value] of Object.entries(properties)) {
    if (target.set) target.set(key, value)
    else target[key] = value
  }
}

/** Kennungswechsel am semantischen Objekt samt DI und Registry. */
function changeId(element: any, bo: any, newId: string, moddle: any, elementRegistry: any): { oldId: string; oldDiId?: string } {
  const ids = getIds(moddle)
  const oldId = bo.id
  ids.unclaim(oldId)
  ids.claim(newId, bo)
  bo.id = newId
  if (element && elementRegistry.get(oldId) === element) elementRegistry.updateId(element, newId)
  const di = element && element.di
  let oldDiId: string | undefined
  if (di && di.id === `${oldId}_di`) {
    oldDiId = di.id
    ids.unclaim(di.id)
    di.id = `${newId}_di`
    ids.claim(di.id, di)
  }
  if (element && element.label && elementRegistry.get(`${oldId}_label`) === element.label) {
    elementRegistry.updateId(element.label, `${newId}_label`)
  }
  return { oldId, oldDiId }
}

function revertId(element: any, bo: any, oldId: string, oldDiId: string | undefined, moddle: any, elementRegistry: any): void {
  const ids = getIds(moddle)
  const currentId = bo.id
  ids.unclaim(currentId)
  ids.claim(oldId, bo)
  bo.id = oldId
  if (element && elementRegistry.get(currentId) === element) elementRegistry.updateId(element, oldId)
  const di = element && element.di
  if (di && oldDiId) {
    ids.unclaim(di.id)
    di.id = oldDiId
    ids.claim(oldDiId, di)
  }
  if (element && element.label && elementRegistry.get(`${currentId}_label`) === element.label) {
    elementRegistry.updateId(element.label, `${oldId}_label`)
  }
}

// ---------------------------------------------------------------------------

export class UpdatePropertiesHandler {
  static $inject = ['elementRegistry', 'moddle']

  constructor(private _elementRegistry: any, private _moddle: any) {}

  execute(context: any): any[] {
    const element = context.element
    const bo = getBusinessObject(element)
    const properties = { ...context.properties }
    const changed = [element]

    if (properties.di) {
      const di = getDi(element)
      context.oldDiProperties = getProperties(di, Object.keys(properties.di))
      setProperties(di, properties.di)
      delete properties.di
    }

    if ('id' in properties && properties.id && properties.id !== bo.id) {
      context.idChange = changeId(element, bo, properties.id, this._moddle, this._elementRegistry)
      delete properties.id
    }

    if ('default' in properties) {
      const oldDefault = bo.default && this._elementRegistry.get(bo.default.id)
      const newDefault = properties.default && this._elementRegistry.get(properties.default.id)
      if (oldDefault) changed.push(oldDefault)
      if (newDefault) changed.push(newDefault)
    }

    context.oldProperties = getProperties(bo, Object.keys(properties))
    setProperties(bo, properties)
    if (element.label) changed.push(element.label)
    context.changed = changed
    return changed
  }

  revert(context: any): any[] {
    const element = context.element
    const bo = getBusinessObject(element)
    setProperties(bo, context.oldProperties)
    if (context.oldDiProperties) setProperties(getDi(element), context.oldDiProperties)
    if (context.idChange) {
      revertId(element, bo, context.idChange.oldId, context.idChange.oldDiId, this._moddle, this._elementRegistry)
    }
    return context.changed
  }
}

export class UpdateModdlePropertiesHandler {
  static $inject = ['elementRegistry', 'moddle']

  constructor(private _elementRegistry: any, private _moddle: any) {}

  execute(context: any): any[] {
    const { element, moddleElement } = context
    const properties = { ...context.properties }
    if (!moddleElement) throw new Error('moddleElement fehlt')
    const bo = getBusinessObject(element)
    if ('id' in properties && moddleElement === bo && properties.id && properties.id !== bo.id) {
      context.idChange = changeId(element, bo, properties.id, this._moddle, this._elementRegistry)
      delete properties.id
    }
    context.oldProperties = getProperties(moddleElement, Object.keys(properties))
    setProperties(moddleElement, properties)
    const changed = [element]
    if (element.label) changed.push(element.label)
    context.changed = changed
    return changed
  }

  revert(context: any): any[] {
    setProperties(context.moddleElement, context.oldProperties)
    if (context.idChange) {
      revertId(context.element, getBusinessObject(context.element), context.idChange.oldId, context.idChange.oldDiId, this._moddle, this._elementRegistry)
    }
    return context.changed
  }
}

const COLOR_KEYS = ['bioc:fill', 'bioc:stroke', 'color:background-color', 'color:border-color']

export class SetColorHandler {
  static $inject = ['commandStack']

  execute(context: any): any[] {
    const colors = context.colors || {}
    const changed: any[] = []
    context.oldColors = new Map()
    for (const raw of context.elements) {
      const element = raw.labelTarget || raw
      const di = getDi(element)
      if (!di) continue
      const old = getProperties(di, COLOR_KEYS)
      old.label = di.label ? di.label.get('color:color') : undefined
      context.oldColors.set(element, old)

      if ('fill' in colors) {
        di.set('bioc:fill', colors.fill || undefined)
        di.set('color:background-color', colors.fill || undefined)
      }
      if ('stroke' in colors) {
        di.set('bioc:stroke', colors.stroke || undefined)
        di.set('color:border-color', colors.stroke || undefined)
        if (di.label) di.label.set('color:color', colors.stroke || undefined)
      }
      changed.push(element)
      if (element.label) changed.push(element.label)
    }
    context.changed = changed
    return changed
  }

  revert(context: any): any[] {
    for (const [element, old] of context.oldColors as Map<any, any>) {
      const di = getDi(element)
      for (const key of COLOR_KEYS) di.set(key, old[key])
      if (di.label) di.label.set('color:color', old.label)
    }
    return context.changed
  }
}

export class UpdateLabelHandler {
  static $inject = ['modeling']

  constructor(private _modeling: any) {}

  execute(context: any): any[] {
    const element = context.element
    const target = element.labelTarget || element
    context.labelTarget = target
    context.oldLabel = getLabel(target)
    setLabel(target, normalizeText(context.newLabel))
    const changed = [target]
    if (target.label) changed.push(target.label)
    return changed
  }

  postExecute(context: any): void {
    const target = context.labelTarget
    const text = normalizeText(context.newLabel)
    const label = target.label

    if (isLabelExternal(target)) {
      if (text && !label) {
        const mid = getExternalLabelMid(target)
        const size = getExternalLabelSize(text)
        this._modeling.createLabel(target, { x: mid.x, y: mid.y - 10 + size.height / 2 }, {
          id: `${target.id}_label`,
          businessObject: target.businessObject,
          di: target.di,
          width: size.width,
          height: size.height,
        })
      } else if (label && !text) {
        this._modeling.removeShape(label, { removeLabelOnly: true })
      } else if (label && text) {
        const size = getExternalLabelSize(text)
        const centerX = label.x + label.width / 2
        const bounds = {
          x: Math.round(centerX - size.width / 2),
          y: label.y,
          width: size.width,
          height: size.height,
        }
        if (bounds.x !== label.x || bounds.width !== label.width || bounds.height !== label.height) {
          this._modeling.resizeShape(label, bounds, { width: 0, height: 0 })
        }
      }
    }

    if (context.newBounds && !target.waypoints) {
      this._modeling.resizeShape(target, context.newBounds)
    }
  }

  revert(context: any): any[] {
    const target = context.labelTarget
    setLabel(target, context.oldLabel)
    const changed = [target]
    if (target.label) changed.push(target.label)
    return changed
  }
}

function normalizeText(text: unknown): string | undefined {
  if (text === null || text === undefined) return undefined
  const value = String(text)
  return value.trim().length === 0 ? undefined : value
}

/**
 * Tauscht das semantische Objekt der Diagrammwurzel (Prozess ↔ Kollaboration).
 * Kontext: `{ newBusinessObject, keepOld }`.
 */
export class UpdateCanvasRootHandler {
  static $inject = ['canvas', 'elementRegistry', 'moddle']

  constructor(private _canvas: any, private _elementRegistry: any, private _moddle: any) {}

  execute(context: any): any[] {
    const root = context.rootElement || this._canvas.getRootElement()
    context.rootElement = root
    const oldBo = root.businessObject
    const newBo = context.newBusinessObject
    const definitions = getDefinitions(oldBo) || context.definitions
    context.definitions = definitions
    context.oldBusinessObject = oldBo

    const rootElements = definitions.get('rootElements')
    context.oldIndex = rootElements.indexOf(oldBo)
    if (!context.keepOld) removeFromList(rootElements, oldBo)
    const index = is(newBo, 'bpmn:Collaboration') ? 0 : Math.max(0, context.oldIndex)
    addToList(rootElements, newBo, Math.min(index, rootElements.length))
    newBo.$parent = definitions

    const plane = root.di
    if (plane) plane.bpmnElement = newBo
    root.businessObject = newBo
    this._elementRegistry.updateId(root, newBo.id)
    getIds(this._moddle).claim(newBo.id, newBo)
    return [root]
  }

  revert(context: any): any[] {
    const root = context.rootElement
    const oldBo = context.oldBusinessObject
    const newBo = context.newBusinessObject
    const rootElements = context.definitions.get('rootElements')
    removeFromList(rootElements, newBo)
    if (!context.keepOld) addToList(rootElements, oldBo, Math.max(0, context.oldIndex))
    if (root.di) root.di.bpmnElement = oldBo
    root.businessObject = oldBo
    this._elementRegistry.updateId(root, oldBo.id)
    return [root]
  }
}

export class IdClaimHandler {
  static $inject = ['moddle']

  constructor(private _moddle: any) {}

  execute(context: any): void {
    const ids = getIds(this._moddle)
    if (context.claiming) ids.claim(context.id, context.element)
    else ids.unclaim(context.id)
  }

  revert(context: any): void {
    const ids = getIds(this._moddle)
    if (context.claiming) ids.unclaim(context.id)
    else ids.claim(context.id, context.element)
  }
}
