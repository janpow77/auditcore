/**
 * Ersetzen („Morphen“) von BPMN-Elementen unter Erhalt von Kennung, Name,
 * Dokumentation, Erweiterungen (`extensionElements`, fremde Attribute),
 * Farben und Verbindungen – soweit der Zieltyp sie zulässt.
 */

import type { Injector } from 'didi'
import type { Element } from 'diagram-js/lib/model/Types'

import { cloneModdleElement, copyProperties } from '../util/ModdleCopy'
import { getBusinessObject, getDi, is, isAny, isExpanded } from '../util/ModelUtil'
import type { BpmnElement, CommandEvent, EventBus, Moddle, ModdleElement, Selection } from '../types'
import type BpmnFactory from '../modeling/BpmnFactory'
import type ElementFactory from '../modeling/ElementFactory'
import type Modeling from '../modeling/Modeling'
import type { ReplaceTarget } from './ReplaceOptions'

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

const SIZE_CLASSES: [string[], SizeClass][] = [
  [['bpmn:Task', 'bpmn:CallActivity'], 'activity'],
  [['bpmn:Event'], 'event'],
  [['bpmn:Gateway'], 'gateway'],
  [['bpmn:DataObjectReference', 'bpmn:DataStoreReference'], 'data'],
]

function sizeClass(bo: ModdleElement, expanded: boolean): SizeClass {
  if (is(bo, 'bpmn:SubProcess')) return expanded ? 'expanded' : 'activity'
  if (is(bo, 'bpmn:Participant')) return expanded ? 'participant' : 'participant-collapsed'
  return SIZE_CLASSES.find(([types]) => isAny(bo, types))?.[1] || 'other'
}

/** Kinder wandern mit, wenn Teilprozess bzw. Pool aufgeklappt bleiben. */
function keepsChildren(element: BpmnElement, newBo: ModdleElement, expanded: boolean): boolean {
  const oldBo = getBusinessObject(element)
  if (!expanded) return false
  if (is(oldBo, 'bpmn:SubProcess') && is(newBo, 'bpmn:SubProcess')) return isExpanded(element)
  return is(oldBo, 'bpmn:Participant') && is(newBo, 'bpmn:Participant')
}

interface ReplaceHints {
  select?: boolean
  moveChildren?: boolean
  targetId?: string
  [key: string]: unknown
}

interface FlagContext {
  element: BpmnElement
  oldBo: ModdleElement
  newBo: ModdleElement
  target: ReplaceTarget
  factory: BpmnFactory
}

/** Typabhängige Übernahmen und Vorgaben beim Ersetzen (deklarative Tabelle). */
const TARGET_FLAGS: [string, (context: FlagContext) => void][] = [
  ['bpmn:StartEvent', ({ newBo, target }) => void (target.isInterrupting === false && (newBo.isInterrupting = false))],
  [
    'bpmn:BoundaryEvent',
    ({ element, oldBo, newBo, target }) => {
      newBo.cancelActivity = target.cancelActivity === false ? false : undefined
      newBo.attachedToRef = oldBo.attachedToRef || getBusinessObject(element.host as BpmnElement | undefined)
    },
  ],
  ['bpmn:SubProcess', ({ newBo, target }) => void (target.triggeredByEvent && (newBo.triggeredByEvent = true))],
  [
    'bpmn:EventBasedGateway',
    ({ newBo, target }) => {
      newBo.eventGatewayType = target.eventGatewayType === 'Parallel' ? 'Parallel' : undefined
      newBo.instantiate = target.instantiate ? true : undefined
    },
  ],
  ['bpmn:DataObjectReference', ({ newBo, factory }) => void (newBo.dataObjectRef ||= factory.create('bpmn:DataObject'))],
  ['bpmn:Gateway', ({ oldBo, newBo }) => void (oldBo.default && (newBo.default = oldBo.default))],
  ['bpmn:Activity', ({ oldBo, newBo }) => void (oldBo.default && (newBo.default = oldBo.default))],
  [
    'bpmn:Participant',
    ({ oldBo, newBo, target, factory }) => {
      if (target.isExpanded !== false) newBo.processRef = oldBo.processRef || factory.create('bpmn:Process', { isExecutable: false })
    },
  ],
]

interface SubProcessPlanes {
  toggleExpanded(shape: BpmnElement, expand?: boolean): void
}

type Replace = { replaceElement(element: Element, attrs: Record<string, unknown>, hints?: ReplaceHints): BpmnElement }

export default class BpmnReplace {
  static $inject = ['bpmnFactory', 'elementFactory', 'moddle', 'modeling', 'replace', 'selection', 'eventBus', 'injector']

  constructor(
    private readonly bpmnFactory: BpmnFactory,
    private readonly elementFactory: ElementFactory,
    private readonly moddle: Moddle,
    private readonly modeling: Modeling,
    private readonly replace: Replace,
    private readonly selection: Selection,
    eventBus: EventBus,
    private readonly injector: Injector,
  ) {
    // Nach dem Ersetzen die ursprüngliche Kennung wiederherstellen – im selben
    // Befehl, damit Rückgängig beides zugleich zurücknimmt.
    eventBus.on('commandStack.shape.replace.postExecuted', 1500, (event: CommandEvent<{ hints?: ReplaceHints; newShape?: BpmnElement }>) => {
      const { hints, newShape } = event.context
      if (hints?.targetId && newShape && newShape.id !== hints.targetId) {
        this.modeling.updateProperties(newShape, { id: hints.targetId })
      }
    })
  }

  /** Ersetzt ein Element durch den Zieltyp und liefert das neue Element. */
  replaceElement(input: Element, target: ReplaceTarget, hints: ReplaceHints = {}): BpmnElement {
    const element = input as BpmnElement
    if (element.waypoints) return element
    const planes = this.togglePlanes(element, target)
    if (planes) return this.replaceWithToggle(element, target, hints, planes)
    const oldBo = getBusinessObject(element)
    const newBo = this.createBusinessObject(element, oldBo, target)
    const expanded = this.targetExpanded(element, newBo, target)
    const newDi = this.createDi(element, oldBo, newBo, expanded)
    const attrs = this.shapeAttrs(element, oldBo, newBo, newDi, target, expanded)
    const newElement = this.replace.replaceElement(element, attrs, {
      ...hints,
      moveChildren: keepsChildren(element, newBo, expanded) && hints.moveChildren !== false,
      targetId: oldBo.id,
    })
    if (hints.select !== false) this.selection.select(newElement as never)
    return newElement
  }

  /** Dienst für Teilprozess-Ebenen, wenn sich nur der Auf-/Zuklappzustand ändert. */
  private togglePlanes(element: BpmnElement, target: ReplaceTarget): SubProcessPlanes | null {
    if (!is(element, 'bpmn:SubProcess') || target.isExpanded === undefined || target.isExpanded === isExpanded(element)) return null
    return this.injector.get('subProcessPlanes', false) as SubProcessPlanes | null
  }

  /** Auf-/Zuklappen verschiebt den Inhalt zwischen Form und eigener Ebene. */
  private replaceWithToggle(element: BpmnElement, target: ReplaceTarget, hints: ReplaceHints, planes: SubProcessPlanes): BpmnElement {
    const bo = getBusinessObject(element)
    let result = element
    this.modeling.compound(() => {
      const sameKind = bo.$type === target.type && !!bo.triggeredByEvent === !!target.triggeredByEvent
      if (!sameKind) result = this.replaceElement(element, { ...target, isExpanded: isExpanded(element) }, { ...hints, select: false })
      planes.toggleExpanded(result, target.isExpanded)
    })
    if (hints.select !== false) this.selection.select(result as never)
    return result
  }

  private createBusinessObject(element: BpmnElement, oldBo: ModdleElement, target: ReplaceTarget): ModdleElement {
    const newBo = this.bpmnFactory.create(target.type)
    copyProperties(this.moddle, oldBo, newBo, { exclude: NEVER_COPY })
    if (!is(newBo, 'bpmn:Activity')) newBo.loopCharacteristics = undefined
    if (is(newBo, 'bpmn:Activity') && !is(oldBo, 'bpmn:Activity')) newBo.isForCompensation = undefined
    if (is(newBo, 'bpmn:Event') && target.eventDefinitionType) this.addEventDefinition(oldBo, newBo, target.eventDefinitionType)
    this.applyTargetFlags(element, oldBo, newBo, target)
    return newBo
  }

  /** Gleichartige Ereignisdefinition übernehmen (mit neuer Kennung), sonst neu anlegen. */
  private addEventDefinition(oldBo: ModdleElement, newBo: ModdleElement, type: string): void {
    const existing = (oldBo.eventDefinitions || []).find((definition) => is(definition, type))
    const definition = existing ? cloneModdleElement(this.moddle, existing, {}, newBo) : this.bpmnFactory.create(type)
    if (existing?.id) {
      definition.id = undefined
      this.bpmnFactory._ensureId(definition)
    }
    definition.$parent = newBo
    newBo.get<ModdleElement[]>('eventDefinitions').push(definition)
  }

  private applyTargetFlags(element: BpmnElement, oldBo: ModdleElement, newBo: ModdleElement, target: ReplaceTarget): void {
    for (const [type, apply] of TARGET_FLAGS) {
      if (is(newBo, type)) apply({ element, oldBo, newBo, target, factory: this.bpmnFactory })
    }
  }

  private targetExpanded(element: BpmnElement, newBo: ModdleElement, target: ReplaceTarget): boolean {
    if (is(newBo, 'bpmn:Participant')) return target.isExpanded !== false
    if (is(newBo, 'bpmn:SubProcess')) return target.isExpanded !== undefined ? target.isExpanded : isExpanded(element)
    return true
  }

  /** DI: Farben, Ausrichtung, fremde Attribute und ggf. Beschriftungslage übernehmen. */
  private createDi(element: BpmnElement, oldBo: ModdleElement, newBo: ModdleElement, expanded: boolean): ModdleElement {
    const oldDi = getDi(element)
    const attrs: Record<string, unknown> = {}
    if (is(newBo, 'bpmn:SubProcess')) attrs.isExpanded = expanded
    if (isAny(newBo, ['bpmn:Participant', 'bpmn:Lane']) && oldDi?.isHorizontal !== undefined) attrs.isHorizontal = oldDi.isHorizontal
    if (is(newBo, 'bpmn:ExclusiveGateway')) attrs.isMarkerVisible = true
    const newDi = this.bpmnFactory.createDiShape(newBo, attrs)
    if (!oldDi) return newDi
    for (const key of COLOR_ATTRS) {
      const value = oldDi.get(key)
      if (value) newDi.set(key, value)
    }
    Object.assign(newDi.$attrs, oldDi.$attrs || {})
    if (oldDi.label && sizeClass(oldBo, isExpanded(element)) === sizeClass(newBo, expanded)) {
      newDi.label = cloneModdleElement(this.moddle, oldDi.label, {}, newDi)
    }
    return newDi
  }

  private shapeAttrs(
    element: BpmnElement,
    oldBo: ModdleElement,
    newBo: ModdleElement,
    di: ModdleElement,
    target: ReplaceTarget,
    expanded: boolean,
  ): Record<string, unknown> {
    const attrs: Record<string, unknown> = { type: target.type, businessObject: newBo, di }
    if (is(newBo, 'bpmn:SubProcess')) attrs.collapsed = !expanded
    if (sizeClass(oldBo, isExpanded(element)) === sizeClass(newBo, expanded)) return attrs
    const size = this.elementFactory.getDefaultSize(newBo, di)
    const shape = element as unknown as { x: number; y: number; width: number; height: number }
    return {
      ...attrs,
      ...size,
      x: Math.round(shape.x + shape.width / 2 - size.width / 2),
      y: Math.round(shape.y + shape.height / 2 - size.height / 2),
    }
  }

  /** Sequenzfluss-Varianten: Standard, Default oder bedingt. */
  replaceFlow(connection: Element, kind: 'sequence' | 'default' | 'conditional'): void {
    this.modeling.compound(() => this.applyFlowKind(connection as BpmnElement, kind))
  }

  private applyFlowKind(connection: BpmnElement, kind: 'sequence' | 'default' | 'conditional'): void {
    const bo = getBusinessObject(connection)
    const source = connection.source as BpmnElement | undefined
    const sourceBo = getBusinessObject(source)
    const isDefault = !!sourceBo && sourceBo.default === bo
    if (kind !== 'default' && isDefault && source) this.modeling.updateProperties(source, { default: undefined })
    if (kind === 'default') {
      if (bo.conditionExpression && !is(sourceBo, 'bpmn:Activity')) this.modeling.updateProperties(connection, { conditionExpression: undefined })
      if (source) this.modeling.updateProperties(source, { default: bo })
    } else if (kind === 'conditional') {
      this.modeling.updateProperties(connection, { conditionExpression: this.bpmnFactory.create('bpmn:FormalExpression') })
    } else if (bo.conditionExpression) {
      this.modeling.updateProperties(connection, { conditionExpression: undefined })
    }
  }
}
