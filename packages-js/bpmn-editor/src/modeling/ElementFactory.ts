/**
 * Erzeugt Diagrammelemente (Formen, Kanten, Beschriftungen) samt
 * semantischem Objekt und DI. Bekannte Kurzattribute:
 *
 * - `type`: BPMN-Typ, z. B. `bpmn:UserTask`
 * - `eventDefinitionType` / `eventDefinitionAttrs`: Ereignisdefinition
 * - `isExpanded`, `isInterrupting`, `cancelActivity`, `triggeredByEvent`,
 *   `isHorizontal`, `isForCompensation`, `associationDirection`,
 *   `isCollection`, `processRef`, `colors` ({ fill, stroke })
 */

import BaseElementFactory from 'diagram-js/lib/core/ElementFactory'

import { DEFAULT_LABEL_SIZE } from '../util/LabelUtil'
import { getDi, is, isAny } from '../util/ModelUtil'
import type { BpmnElement, CreatedElement, ModdleElement } from '../types'
import type BpmnFactory from './BpmnFactory'

type Size = { width: number; height: number }
type Attrs = Record<string, unknown>

export const SIZES = {
  task: { width: 100, height: 80 },
  subProcessExpanded: { width: 350, height: 200 },
  event: { width: 36, height: 36 },
  gateway: { width: 50, height: 50 },
  dataObject: { width: 36, height: 50 },
  dataStore: { width: 50, height: 50 },
  textAnnotation: { width: 100, height: 30 },
  participant: { width: 600, height: 250 },
  participantCollapsed: { width: 400, height: 60 },
  lane: { width: 570, height: 120 },
  group: { width: 300, height: 300 },
} as const

/** Standardgrößen je Typ (erster Treffer gewinnt; Teilprozess/Pool gesondert). */
const DEFAULT_SIZES: [string[], Size][] = [
  [['bpmn:Task', 'bpmn:CallActivity'], SIZES.task],
  [['bpmn:Gateway'], SIZES.gateway],
  [['bpmn:Event'], SIZES.event],
  [['bpmn:Lane'], SIZES.lane],
  [['bpmn:DataObjectReference', 'bpmn:DataInput', 'bpmn:DataOutput'], SIZES.dataObject],
  [['bpmn:DataStoreReference'], SIZES.dataStore],
  [['bpmn:TextAnnotation'], SIZES.textAnnotation],
  [['bpmn:Group'], SIZES.group],
]

/** Kurzattribute, die nicht am Diagrammelement landen. */
const SHORTCUT_KEYS = [
  'eventDefinitionType',
  'eventDefinitionAttrs',
  'isExpanded',
  'isInterrupting',
  'isHorizontal',
  'cancelActivity',
  'triggeredByEvent',
  'isForCompensation',
  'associationDirection',
  'processRef',
  'isCollection',
  'colors',
]

/** Kurzattribute, die unverändert ans semantische Objekt gehen: [Name, Typ, zulässiger Wert]. */
const SEMANTIC_SHORTCUTS: [string, string, (value: unknown) => boolean][] = [
  ['isInterrupting', 'bpmn:StartEvent', (value) => value === false],
  ['cancelActivity', 'bpmn:BoundaryEvent', (value) => value === false],
  ['triggeredByEvent', 'bpmn:SubProcess', (value) => value === true],
  ['isForCompensation', 'bpmn:Activity', (value) => value === true],
  ['associationDirection', 'bpmn:Association', (value) => typeof value === 'string'],
  ['processRef', 'bpmn:Participant', (value) => !!value],
]

export function applyColors(di: ModdleElement | undefined, colors: { fill?: string | null; stroke?: string | null }): void {
  if (!di) return
  if (colors.fill !== undefined) {
    di.set('bioc:fill', colors.fill || undefined)
    di.set('color:background-color', colors.fill || undefined)
  }
  if (colors.stroke !== undefined) {
    di.set('bioc:stroke', colors.stroke || undefined)
    di.set('color:border-color', colors.stroke || undefined)
  }
}

export default class ElementFactory extends BaseElementFactory {
  static $inject = ['bpmnFactory']

  constructor(private readonly bpmnFactory: BpmnFactory) {
    super()
  }

  create(elementType: string, attrs: Attrs = {}): CreatedElement {
    if (elementType === 'label') {
      const target = attrs.labelTarget as BpmnElement | undefined
      const di = attrs.di || getDi(target)
      return super.create('label', { ...DEFAULT_LABEL_SIZE, ...attrs, di }) as unknown as CreatedElement
    }
    return this.createElement(elementType, attrs)
  }

  createElement(elementType: string, input: Attrs = {}): CreatedElement {
    const attrs = { ...input }
    const createdBo = !attrs.businessObject
    const givenDi = attrs.di as ModdleElement | Attrs | undefined
    const createdDi = !givenDi || !(givenDi as ModdleElement).$type
    const businessObject = (attrs.businessObject as ModdleElement | undefined) || this.createBusinessObject(attrs)
    const di = createdDi ? this.createDi(elementType, businessObject, givenDi as Attrs | undefined) : (givenDi as ModdleElement)

    if (attrs.colors) applyColors(di, attrs.colors as { fill?: string; stroke?: string })
    this.applySemanticShortcuts(businessObject, attrs, createdBo)
    if (createdDi) this.applyDiDefaults(businessObject, di, attrs)

    const size = elementType === 'root' ? {} : this.getDefaultSize(businessObject, di)
    const result: Attrs = { id: businessObject.id, ...size, ...attrs, businessObject, di }
    for (const key of SHORTCUT_KEYS) delete result[key]
    return super.create(elementType as 'shape', result) as unknown as CreatedElement
  }

  private createBusinessObject(attrs: Attrs): ModdleElement {
    if (typeof attrs.type !== 'string') throw new Error('Element-Typ fehlt (attrs.type)')
    return this.bpmnFactory.create(attrs.type)
  }

  private createDi(elementType: string, bo: ModdleElement, shortcut: Attrs | undefined): ModdleElement {
    const diAttrs = { ...(shortcut || {}) }
    if (elementType === 'root') return this.bpmnFactory.createDiPlane(bo, diAttrs)
    if (elementType === 'connection') return this.bpmnFactory.createDiEdge(bo, diAttrs)
    return this.bpmnFactory.createDiShape(bo, diAttrs)
  }

  /** Semantische Voreinstellungen; Vorgaben nur für neu angelegte Objekte (Import bleibt unberührt). */
  private applySemanticShortcuts(bo: ModdleElement, attrs: Attrs, createdBo: boolean): void {
    this.applyEventDefinition(bo, attrs)
    for (const [key, type, accepts] of SEMANTIC_SHORTCUTS) {
      if (key in attrs && accepts(attrs[key]) && is(bo, type)) bo.set(key, attrs[key])
    }
    if (createdBo) this.applyCreationDefaults(bo, attrs)
  }

  private applyCreationDefaults(bo: ModdleElement, attrs: Attrs): void {
    if (is(bo, 'bpmn:Group') && !bo.categoryValueRef) this.ensureCategoryValue(bo)
    if (is(bo, 'bpmn:DataObjectReference') && !bo.dataObjectRef) {
      bo.dataObjectRef = this.bpmnFactory.create('bpmn:DataObject', attrs.isCollection ? { isCollection: true } : {})
    }
    if (is(bo, 'bpmn:Participant') && attrs.isExpanded !== false && !bo.processRef) {
      bo.processRef = this.bpmnFactory.create('bpmn:Process', { isExecutable: false })
    }
  }

  private applyEventDefinition(bo: ModdleElement, attrs: Attrs): void {
    if (typeof attrs.eventDefinitionType !== 'string') return
    const definitions = bo.get<ModdleElement[]>('eventDefinitions')
    if (definitions.length > 0) return
    const definition = this.bpmnFactory.create(attrs.eventDefinitionType, (attrs.eventDefinitionAttrs as Attrs) || {})
    definition.$parent = bo
    definitions.push(definition)
  }

  /** DI-Voreinstellungen für neu angelegte DI. */
  private applyDiDefaults(bo: ModdleElement, di: ModdleElement, attrs: Attrs): void {
    if (!is(di, 'bpmndi:BPMNShape')) return
    if (attrs.isExpanded !== undefined) di.isExpanded = !!attrs.isExpanded
    else if (is(bo, 'bpmn:SubProcess') && di.isExpanded === undefined) di.isExpanded = false
    if (is(bo, 'bpmn:ExclusiveGateway') && di.isMarkerVisible === undefined) di.isMarkerVisible = true
    if (isAny(bo, ['bpmn:Participant', 'bpmn:Lane'])) {
      di.isHorizontal = attrs.isHorizontal !== undefined ? !!attrs.isHorizontal : (di.isHorizontal ?? true)
    }
  }

  private ensureCategoryValue(group: ModdleElement): void {
    const categoryValue = this.bpmnFactory.create('bpmn:CategoryValue')
    const category = this.bpmnFactory.create('bpmn:Category', { categoryValue: [categoryValue] })
    categoryValue.$parent = category
    group.categoryValueRef = categoryValue
  }

  /** Standardgröße je Elementtyp. */
  getDefaultSize(element: BpmnElement | ModdleElement, di?: ModdleElement): Size {
    const bo: ModdleElement = (element as BpmnElement).businessObject || (element as ModdleElement)
    const shapeDi = di || getDi(element as BpmnElement)
    if (is(bo, 'bpmn:SubProcess')) return shapeDi?.isExpanded ? { ...SIZES.subProcessExpanded } : { ...SIZES.task }
    if (is(bo, 'bpmn:Participant')) {
      const size = bo.processRef ? SIZES.participant : SIZES.participantCollapsed
      return shapeDi?.isHorizontal === false ? { width: size.height, height: size.width } : { ...size }
    }
    const entry = DEFAULT_SIZES.find(([types]) => isAny(bo, types))
    return { ...(entry ? entry[1] : SIZES.task) }
  }

  /** Kompatibilitätshilfe: Pool mit eigenem Prozess erzeugen. */
  createParticipantShape(attrs?: boolean | Attrs): CreatedElement {
    const options = typeof attrs === 'boolean' ? { isExpanded: attrs } : attrs || {}
    return this.createElement('shape', { type: 'bpmn:Participant', ...options })
  }
}
