/**
 * Eigener SVG-Renderer für alle BPMN-2.0-Formen und -Kanten.
 *
 * Die Zeichenfunktionen liegen je Elementfamilie in `./shapes`; dieser
 * Renderer wählt anhand einer Tabelle aus und stellt Farben und
 * Pfeilspitzen bereit. Farben kommen aus der DI (`color:`/`bioc:`), sonst
 * aus der Konfiguration `bpmnRenderer`.
 */

import BaseRenderer from 'diagram-js/lib/draw/BaseRenderer'
import type { Connection, Element, Shape } from 'diagram-js/lib/model/Types'

import { is, isAny } from '../util/ModelUtil'
import type { BpmnElement, Canvas, EventBus } from '../types'
import { getFillColor, getLabelColor, getStrokeColor, type ColorDefaults } from './colors'
import { MarkerFactory } from './markers'
import { svgRect } from './svg'
import { drawCallActivity, drawSubProcess, drawTask } from './shapes/activities'
import { drawGroup, drawLabel, drawTextAnnotation } from './shapes/artifacts'
import { drawConnection } from './shapes/connections'
import type { DrawContext, ShapeDrawer } from './shapes/context'
import { drawDataObject, drawDataStore } from './shapes/data'
import { drawEvent } from './shapes/events'
import { drawGateway } from './shapes/gateways'
import { getConnectionPath, getShapePath } from './shapes/outline'
import { drawLane, drawParticipant } from './shapes/pools'

export { TASK_BORDER_RADIUS } from './shapes/activities'
export { LANE_LABEL_BAND } from './shapes/pools'

export interface BpmnRendererConfig {
  defaultFillColor?: string
  defaultStrokeColor?: string
  defaultLabelColor?: string
}

/** Zeichenfunktion je BPMN-Typ (erste passende gewinnt). */
const SHAPE_DRAWERS: [string[], ShapeDrawer][] = [
  [['bpmn:Event'], drawEvent],
  [['bpmn:Gateway'], drawGateway],
  [['bpmn:SubProcess'], drawSubProcess],
  [['bpmn:CallActivity'], drawCallActivity],
  [['bpmn:Task'], drawTask],
  [['bpmn:Participant'], drawParticipant],
  [['bpmn:Lane'], drawLane],
  [['bpmn:DataObjectReference', 'bpmn:DataObject', 'bpmn:DataInput', 'bpmn:DataOutput'], drawDataObject],
  [['bpmn:DataStoreReference'], drawDataStore],
  [['bpmn:TextAnnotation'], drawTextAnnotation],
  [['bpmn:Group'], drawGroup],
]

/** Rückfall für unbekannte Typen: gestricheltes Rechteck, damit nichts verschwindet. */
const drawUnknown: ShapeDrawer = (parent, context) => {
  const shape = context.element as unknown as { width: number; height: number }
  return svgRect(parent, shape.width, shape.height, 0, {
    fill: context.fill,
    stroke: context.stroke,
    'stroke-width': 1,
    'stroke-dasharray': '4,2',
  })
}

export default class BpmnRenderer extends BaseRenderer {
  static $inject = ['config.bpmnRenderer', 'eventBus', 'canvas']

  readonly defaults: ColorDefaults
  private readonly markers: MarkerFactory

  constructor(config: BpmnRendererConfig | undefined, eventBus: EventBus, canvas: Canvas) {
    super(eventBus, 1500)
    const stroke = config?.defaultStrokeColor || '#1f2328'
    this.defaults = {
      fill: config?.defaultFillColor || '#ffffff',
      stroke,
      label: config?.defaultLabelColor || stroke,
    }
    this.markers = new MarkerFactory(() => (canvas as unknown as { _svg: SVGSVGElement })._svg)
  }

  canRender(element: Element): boolean {
    return is(element, 'bpmn:BaseElement')
  }

  getFillColor(element: BpmnElement): string {
    return getFillColor(element, this.defaults.fill)
  }

  getStrokeColor(element: BpmnElement): string {
    return getStrokeColor(element, this.defaults.stroke)
  }

  private context(element: BpmnElement): DrawContext {
    const colorSource = (element.labelTarget as BpmnElement | undefined) || element
    return {
      element,
      fill: getFillColor(colorSource, this.defaults.fill),
      stroke: getStrokeColor(colorSource, this.defaults.stroke),
      labelColor: getLabelColor(colorSource, this.defaults),
      markers: this.markers,
    }
  }

  drawShape(parentGfx: SVGElement, shape: Shape): SVGElement {
    const element = shape as BpmnElement
    const context = this.context(element)
    if (element.type === 'label') return drawLabel(parentGfx, context)
    const entry = SHAPE_DRAWERS.find(([types]) => isAny(element, types))
    return (entry ? entry[1] : drawUnknown)(parentGfx, context)
  }

  drawConnection(parentGfx: SVGElement, connection: Connection): SVGElement {
    return drawConnection(parentGfx, this.context(connection as BpmnElement))
  }

  getShapePath(shape: Shape): string {
    return getShapePath(shape as BpmnElement)
  }

  getConnectionPath(connection: Connection): string {
    return getConnectionPath(connection as BpmnElement)
  }
}
