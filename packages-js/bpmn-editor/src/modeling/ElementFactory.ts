/**
 * Erzeugt Diagrammelemente (Formen, Kanten, Beschriftungen) samt
 * semantischem Objekt und DI. Bekannte Kurzattribute:
 *
 * - `type`: BPMN-Typ, z. B. `bpmn:UserTask`
 * - `eventDefinitionType`: z. B. `bpmn:TimerEventDefinition`
 * - `eventDefinitionAttrs`: Attribute der Ereignisdefinition
 * - `isExpanded`, `isInterrupting`, `cancelActivity`, `triggeredByEvent`,
 *   `isHorizontal`, `isForCompensation`, `associationDirection`
 */

import BaseElementFactory from 'diagram-js/lib/core/ElementFactory'

import { getDi, is, isAny } from '../util/ModelUtil'
import { DEFAULT_LABEL_SIZE } from '../util/LabelUtil'

/* eslint-disable @typescript-eslint/no-explicit-any */

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
}

export default class ElementFactory extends (BaseElementFactory as any) {
  static $inject = ['bpmnFactory', 'moddle', 'translate']

  _bpmnFactory: any
  _moddle: any
  _translate: (text: string) => string

  constructor(bpmnFactory: any, moddle: any, translate: (text: string) => string) {
    super()
    this._bpmnFactory = bpmnFactory
    this._moddle = moddle
    this._translate = translate
  }

  create(elementType: string, attrs: Record<string, any> = {}): any {
    if (elementType === 'label') {
      const di = attrs.di || getDi(attrs.labelTarget) || this._bpmnFactory.createDiShape(attrs.businessObject)
      return super.create(elementType, { ...DEFAULT_LABEL_SIZE, ...attrs, di })
    }
    return this.createElement(elementType, attrs)
  }

  createElement(elementType: string, attrs: Record<string, any> = {}): any {
    attrs = { ...attrs }
    let businessObject = attrs.businessObject
    const createdBo = !businessObject
    const createdDi = !attrs.di || !attrs.di.$type
    if (!businessObject) {
      if (!attrs.type) throw new Error('Element-Typ fehlt (attrs.type)')
      businessObject = this._bpmnFactory.create(attrs.type)
    }
    if (!is(businessObject, 'bpmn:BaseElement') && !is(businessObject, 'bpmn:Definitions')) {
      throw new Error(`Kein BPMN-Element: ${businessObject?.$type}`)
    }

    let di = attrs.di
    if (!di || !di.$type) {
      // Fehlt die DI oder liegt sie als Kurzform vor ({ isExpanded: true }), neu anlegen.
      const diAttrs = di && !di.$type ? { ...di } : {}
      if (elementType === 'root') {
        di = this._bpmnFactory.createDiPlane(businessObject, diAttrs)
      } else if (elementType === 'connection') {
        di = this._bpmnFactory.createDiEdge(businessObject, diAttrs)
      } else {
        di = this._bpmnFactory.createDiShape(businessObject, diAttrs)
      }
    }

    if (createdBo && is(businessObject, 'bpmn:Group') && !businessObject.categoryValueRef) {
      this._ensureCategoryValue(businessObject)
    }

    if (attrs.colors) {
      applyColors(di, attrs.colors)
      delete attrs.colors
    }

    this._applyShortcuts(businessObject, di, attrs, createdBo, createdDi)

    const size = elementType === 'root' ? {} : this.getDefaultSize(businessObject, di)
    const result = {
      id: businessObject.id,
      ...size,
      ...attrs,
      businessObject,
      di,
    }
    delete (result as any).eventDefinitionType
    delete (result as any).eventDefinitionAttrs
    delete (result as any).isExpanded
    delete (result as any).isInterrupting
    delete (result as any).isHorizontal
    delete (result as any).cancelActivity
    delete (result as any).triggeredByEvent
    delete (result as any).isForCompensation
    delete (result as any).associationDirection
    delete (result as any).processRef
    return super.create(elementType, result)
  }

  private _applyShortcuts(bo: any, di: any, attrs: Record<string, any>, createdBo: boolean, createdDi: boolean): void {
    if (attrs.eventDefinitionType) {
      const definitions = bo.get('eventDefinitions')
      if (definitions.length === 0) {
        const definition = this._bpmnFactory.create(attrs.eventDefinitionType, attrs.eventDefinitionAttrs || {})
        definition.$parent = bo
        definitions.push(definition)
      }
    }
    if (attrs.isExpanded !== undefined && is(di, 'bpmndi:BPMNShape')) {
      di.isExpanded = !!attrs.isExpanded
    } else if (createdDi && is(bo, 'bpmn:SubProcess') && is(di, 'bpmndi:BPMNShape') && di.isExpanded === undefined) {
      di.isExpanded = false
    }
    if (attrs.isInterrupting === false && is(bo, 'bpmn:StartEvent')) bo.isInterrupting = false
    if (attrs.cancelActivity === false && is(bo, 'bpmn:BoundaryEvent')) bo.cancelActivity = false
    if (attrs.triggeredByEvent && is(bo, 'bpmn:SubProcess')) bo.triggeredByEvent = true
    if (attrs.isForCompensation && is(bo, 'bpmn:Activity')) bo.isForCompensation = true
    if (attrs.associationDirection && is(bo, 'bpmn:Association')) bo.associationDirection = attrs.associationDirection
    if (createdDi && is(bo, 'bpmn:ExclusiveGateway') && is(di, 'bpmndi:BPMNShape') && di.isMarkerVisible === undefined) {
      di.isMarkerVisible = true
    }
    if (isAny(bo, ['bpmn:Participant', 'bpmn:Lane']) && is(di, 'bpmndi:BPMNShape')) {
      if (attrs.isHorizontal !== undefined) di.isHorizontal = !!attrs.isHorizontal
      else if (createdDi && di.isHorizontal === undefined) di.isHorizontal = true
    }
    if (createdBo && is(bo, 'bpmn:DataObjectReference') && !bo.dataObjectRef) {
      bo.dataObjectRef = this._bpmnFactory.create('bpmn:DataObject', { isCollection: !!attrs.isCollection })
    }
    delete attrs.isCollection
    if (is(bo, 'bpmn:Participant')) {
      if (attrs.processRef) {
        bo.processRef = attrs.processRef
      } else if (createdBo && attrs.isExpanded !== false && !bo.processRef) {
        bo.processRef = this._bpmnFactory.create('bpmn:Process', { isExecutable: false })
      }
    }
  }

  private _ensureCategoryValue(group: any): void {
    const categoryValue = this._bpmnFactory.create('bpmn:CategoryValue')
    const category = this._bpmnFactory.create('bpmn:Category', { categoryValue: [categoryValue] })
    categoryValue.$parent = category
    group.categoryValueRef = categoryValue
  }

  /** Standardgröße je Elementtyp. */
  getDefaultSize(element: any, di?: any): { width: number; height: number } {
    const bo = element.businessObject || element
    di = di || getDi(element)
    if (is(bo, 'bpmn:SubProcess')) {
      return di && di.isExpanded ? { ...SIZES.subProcessExpanded } : { ...SIZES.task }
    }
    if (is(bo, 'bpmn:Task') || is(bo, 'bpmn:CallActivity')) return { ...SIZES.task }
    if (is(bo, 'bpmn:Gateway')) return { ...SIZES.gateway }
    if (is(bo, 'bpmn:Event')) return { ...SIZES.event }
    if (is(bo, 'bpmn:Participant')) {
      const horizontal = !di || di.isHorizontal !== false
      const size = bo.processRef ? SIZES.participant : SIZES.participantCollapsed
      return horizontal ? { ...size } : { width: size.height, height: size.width }
    }
    if (is(bo, 'bpmn:Lane')) return { ...SIZES.lane }
    if (isAny(bo, ['bpmn:DataObjectReference', 'bpmn:DataInput', 'bpmn:DataOutput'])) return { ...SIZES.dataObject }
    if (is(bo, 'bpmn:DataStoreReference')) return { ...SIZES.dataStore }
    if (is(bo, 'bpmn:TextAnnotation')) return { ...SIZES.textAnnotation }
    if (is(bo, 'bpmn:Group')) return { ...SIZES.group }
    return { ...SIZES.task }
  }

  /** Kompatibilitätshilfe: Pool mit eigenem Prozess erzeugen. */
  createParticipantShape(attrs?: boolean | Record<string, any>): any {
    const options = typeof attrs === 'boolean' ? { isExpanded: attrs } : attrs || {}
    return this.createShape({ type: 'bpmn:Participant', ...options })
  }
}

export function applyColors(di: any, colors: { fill?: string | null; stroke?: string | null }): void {
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
