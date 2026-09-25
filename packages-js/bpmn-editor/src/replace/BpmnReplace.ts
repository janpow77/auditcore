/**
 * Ersetzen („Morphen“) von BPMN-Elementen unter Erhalt von Kennung, Name,
 * Dokumentation, Erweiterungen (`extensionElements`, fremde Attribute),
 * Farben und Verbindungen – soweit der Zieltyp sie zulässt.
 */

import { cloneModdleElement, copyProperties } from '../util/ModdleCopy'
import { getBusinessObject, getDi, is, isAny, isExpanded, type DiagramElement } from '../util/ModelUtil'
import type { ReplaceTarget } from './ReplaceOptions'

/* eslint-disable @typescript-eslint/no-explicit-any */

const NEVER_COPY = [
  'flowElements',
  'artifacts',
  'laneSets',
  'eventDefinitions',
  'attachedToRef',
  'cancelActivity',
  'isInterrupting',
  'triggeredByEvent',
  'processRef',
  'dataInputAssociations',
  'dataOutputAssociations',
  'default',
  'sourceRef',
  'targetRef',
  'instantiate',
  'eventGatewayType',
  'parallelMultiple',
  'childLaneSet',
  'flowNodeRef',
]

const COLOR_ATTRS = ['bioc:fill', 'bioc:stroke', 'color:background-color', 'color:border-color']

type SizeClass = 'activity' | 'expanded' | 'event' | 'gateway' | 'data' | 'participant' | 'participant-collapsed' | 'other'

function sizeClass(bo: any, expanded: boolean): SizeClass {
  if (is(bo, 'bpmn:SubProcess')) return expanded ? 'expanded' : 'activity'
  if (isAny(bo, ['bpmn:Task', 'bpmn:CallActivity'])) return 'activity'
  if (is(bo, 'bpmn:Event')) return 'event'
  if (is(bo, 'bpmn:Gateway')) return 'gateway'
  if (isAny(bo, ['bpmn:DataObjectReference', 'bpmn:DataStoreReference'])) return 'data'
  if (is(bo, 'bpmn:Participant')) return expanded ? 'participant' : 'participant-collapsed'
  return 'other'
}

export default class BpmnReplace {
  static $inject = ['bpmnFactory', 'elementFactory', 'moddle', 'modeling', 'replace', 'selection', 'eventBus', 'injector']

  constructor(
    private _bpmnFactory: any,
    private _elementFactory: any,
    private _moddle: any,
    private _modeling: any,
    private _replace: any,
    private _selection: any,
    eventBus: any,
    private _injector: any,
  ) {
    // Nach dem Ersetzen die ursprüngliche Kennung wiederherstellen – im selben
    // Befehl, damit Rückgängig beides zugleich zurücknimmt.
    eventBus.on('commandStack.shape.replace.postExecuted', 1500, (event: any) => {
      const context = event.context
      const targetId = context.hints && context.hints.targetId
      const newShape = context.newShape
      if (targetId && newShape && newShape.id !== targetId) {
        this._modeling.updateProperties(newShape, { id: targetId })
      }
    })
  }

  /** Ersetzt ein Element durch den Zieltyp und liefert das neue Element. */
  replaceElement(element: DiagramElement, target: ReplaceTarget, hints: Record<string, any> = {}): any {
    if (element.waypoints) return null
    const planes = this._injector.get('subProcessPlanes', false)
    const wasExpanded = isExpanded(element)
    if (planes && is(element, 'bpmn:SubProcess') && target.type && target.isExpanded !== undefined && target.isExpanded !== wasExpanded) {
      // Auf-/Zuklappen verschiebt den Inhalt zwischen Form und eigener Ebene.
      let result = element
      this._modeling.compound(() => {
        const sameKind =
          getBusinessObject(element).$type === target.type && !!getBusinessObject(element).triggeredByEvent === !!target.triggeredByEvent
        if (!sameKind) result = this.replaceElement(element, { ...target, isExpanded: wasExpanded }, { ...hints, select: false })
        planes.toggleExpanded(result, target.isExpanded)
      })
      if (hints.select !== false) this._selection.select(result)
      return result
    }
    const oldBo = getBusinessObject(element)
    const oldDi = getDi(element)
    const newBo = this._bpmnFactory.create(target.type)

    copyProperties(this._moddle, oldBo, newBo, { exclude: NEVER_COPY })
    if (!is(newBo, 'bpmn:Activity')) newBo.loopCharacteristics = undefined
    if (is(newBo, 'bpmn:Activity') && !is(oldBo, 'bpmn:Activity')) newBo.isForCompensation = undefined

    // Ereignisdefinition: gleichartige übernehmen, sonst neu anlegen.
    if (is(newBo, 'bpmn:Event') && target.eventDefinitionType) {
      const existing = (oldBo.eventDefinitions || []).find((definition: any) => is(definition, target.eventDefinitionType!))
      const definition = existing
        ? cloneModdleElement(this._moddle, existing, {}, newBo)
        : this._bpmnFactory.create(target.eventDefinitionType)
      if (existing && existing.id) {
        definition.id = undefined
        this._bpmnFactory._ensureId(definition)
      }
      definition.$parent = newBo
      newBo.get('eventDefinitions').push(definition)
    }
    if (is(newBo, 'bpmn:StartEvent') && target.isInterrupting === false) newBo.isInterrupting = false
    if (is(newBo, 'bpmn:BoundaryEvent')) {
      newBo.cancelActivity = target.cancelActivity === false ? false : undefined
      if (element.host || oldBo.attachedToRef) newBo.attachedToRef = oldBo.attachedToRef || getBusinessObject(element.host)
    }
    if (is(newBo, 'bpmn:SubProcess') && target.triggeredByEvent) newBo.triggeredByEvent = true
    if (is(newBo, 'bpmn:EventBasedGateway')) {
      newBo.eventGatewayType = target.eventGatewayType === 'Parallel' ? 'Parallel' : undefined
      newBo.instantiate = target.instantiate ? true : undefined
    }
    if (is(newBo, 'bpmn:DataObjectReference') && !newBo.dataObjectRef) {
      newBo.dataObjectRef = this._bpmnFactory.create('bpmn:DataObject')
    }
    if ((is(newBo, 'bpmn:Gateway') || is(newBo, 'bpmn:Activity')) && oldBo.default) {
      newBo.default = oldBo.default
    }

    // Pool: Prozess behalten (aufgeklappt) oder entfernen (leer).
    let expanded: boolean
    if (is(newBo, 'bpmn:Participant')) {
      expanded = target.isExpanded !== false
      if (expanded) {
        newBo.processRef = oldBo.processRef || this._bpmnFactory.create('bpmn:Process', { isExecutable: false })
      }
    } else if (is(newBo, 'bpmn:SubProcess')) {
      expanded = target.isExpanded !== undefined ? target.isExpanded : isExpanded(element)
    } else {
      expanded = true
    }

    // DI: Farben, Ausrichtung und fremde Attribute übernehmen.
    const diAttrs: Record<string, any> = {}
    if (is(newBo, 'bpmn:SubProcess')) diAttrs.isExpanded = expanded
    if (isAny(newBo, ['bpmn:Participant', 'bpmn:Lane']) && oldDi && oldDi.isHorizontal !== undefined) {
      diAttrs.isHorizontal = oldDi.isHorizontal
    }
    if (is(newBo, 'bpmn:ExclusiveGateway')) diAttrs.isMarkerVisible = true
    const newDi = this._bpmnFactory.createDiShape(newBo, diAttrs)
    if (oldDi) {
      for (const key of COLOR_ATTRS) {
        const value = oldDi.get(key)
        if (value) newDi.set(key, value)
      }
      if (oldDi.$attrs) Object.assign(newDi.$attrs, oldDi.$attrs)
      if (oldDi.label && sizeClass(oldBo, isExpanded(element)) === sizeClass(newBo, expanded)) {
        newDi.label = cloneModdleElement(this._moddle, oldDi.label, {}, newDi)
      }
    }

    const attrs: Record<string, any> = { type: target.type, businessObject: newBo, di: newDi }
    if (is(newBo, 'bpmn:SubProcess')) attrs.collapsed = !expanded
    if (sizeClass(oldBo, isExpanded(element)) !== sizeClass(newBo, expanded)) {
      const size = this._elementFactory.getDefaultSize(newBo, newDi)
      attrs.width = size.width
      attrs.height = size.height
      attrs.x = Math.round(element.x + element.width / 2 - size.width / 2)
      attrs.y = Math.round(element.y + element.height / 2 - size.height / 2)
    }

    const keepChildren =
      (is(oldBo, 'bpmn:SubProcess') && is(newBo, 'bpmn:SubProcess') && isExpanded(element) && expanded) ||
      (is(oldBo, 'bpmn:Participant') && is(newBo, 'bpmn:Participant') && expanded)

    const newElement = this._replace.replaceElement(element, attrs, {
      ...hints,
      moveChildren: keepChildren && hints.moveChildren !== false,
      targetId: oldBo.id,
    })

    if (hints.select !== false && newElement) this._selection.select(newElement)
    return newElement
  }

  /** Sequenzfluss-Varianten: Standard, Default oder bedingt. */
  replaceFlow(connection: DiagramElement, kind: 'sequence' | 'default' | 'conditional'): void {
    this._modeling.compound(() => this._replaceFlow(connection, kind))
  }

  private _replaceFlow(connection: DiagramElement, kind: 'sequence' | 'default' | 'conditional'): void {
    const bo = getBusinessObject(connection)
    const source = connection.source
    const sourceBo = source && getBusinessObject(source)
    if (kind === 'default') {
      if (bo.conditionExpression && !is(sourceBo, 'bpmn:Activity')) {
        this._modeling.updateProperties(connection, { conditionExpression: undefined })
      }
      this._modeling.updateProperties(source, { default: bo })
    } else if (kind === 'conditional') {
      if (sourceBo && sourceBo.default === bo) this._modeling.updateProperties(source, { default: undefined })
      const expression = this._bpmnFactory.create('bpmn:FormalExpression')
      this._modeling.updateProperties(connection, { conditionExpression: expression })
    } else {
      if (sourceBo && sourceBo.default === bo) this._modeling.updateProperties(source, { default: undefined })
      if (bo.conditionExpression) this._modeling.updateProperties(connection, { conditionExpression: undefined })
    }
  }
}
