/**
 * Abgleich der DI (Lage, Knickpunkte, Beschriftungen, Einbettung in die
 * Ebene) mit dem Diagramm.
 */

import { addToList, getRootOf, is, removeFromList } from '../../util/ModelUtil'
import type { BpmnElement, Bounds, ModdleElement, Point } from '../../types'
import type BpmnFactory from '../BpmnFactory'

function assignBounds(target: ModdleElement, bounds: Bounds): void {
  target.x = Math.round(bounds.x)
  target.y = Math.round(bounds.y)
  target.width = Math.round(bounds.width)
  target.height = Math.round(bounds.height)
}

function boundsOf(element: BpmnElement): Bounds {
  return { x: element.x as number, y: element.y as number, width: element.width as number, height: element.height as number }
}

export default class DiSync {
  constructor(private readonly bpmnFactory: BpmnFactory) {}

  updateBounds(shape: BpmnElement): void {
    const di = shape.di
    if (!di || !is(di, 'bpmndi:BPMNShape')) return
    if (di.bounds) assignBounds(di.bounds, boundsOf(shape))
    else di.bounds = this.bpmnFactory.createDiBounds(boundsOf(shape))
  }

  updateLabel(label: BpmnElement): void {
    const target = label.labelTarget as BpmnElement | undefined
    const di = target?.di
    if (!di) return
    if (!di.label) {
      di.label = this.bpmnFactory.createDiLabel()
      di.label.$parent = di
    }
    const labelDi = di.label
    if (labelDi.bounds) assignBounds(labelDi.bounds, boundsOf(label))
    else labelDi.bounds = this.bpmnFactory.createDiBounds(boundsOf(label))
  }

  removeLabel(target: BpmnElement): void {
    if (target.di) target.di.label = undefined
  }

  updateWaypoints(connection: BpmnElement): void {
    const di = connection.di
    const waypoints = connection.waypoints as Point[] | undefined
    if (!di || !waypoints) return
    const points = this.bpmnFactory.createDiWaypoints(waypoints)
    points.forEach((point) => (point.$parent = di))
    di.waypoint = points
  }

  /** Ebene (BPMNPlane) der Wurzel, unter der das Element liegt. */
  getPlane(element: BpmnElement): ModdleElement | undefined {
    const di = getRootOf(element).di
    return di && is(di, 'bpmndi:BPMNPlane') ? di : undefined
  }

  /** Hängt die DI in die Ebene der aktuellen Wurzel ein bzw. aus. */
  updateParent(element: BpmnElement): void {
    const di = element.di
    if (!di || is(di, 'bpmndi:BPMNPlane')) return
    const plane = element.parent ? this.getPlane(element) : undefined
    const oldPlane = di.$parent
    if (oldPlane && oldPlane !== plane) removeFromList(oldPlane.get<ModdleElement[]>('planeElement'), di)
    if (plane) {
      addToList(plane.get<ModdleElement[]>('planeElement'), di)
      di.$parent = plane
    } else {
      di.$parent = null
    }
  }
}
