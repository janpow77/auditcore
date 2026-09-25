/**
 * Automatisches Vergrößern von Pools und aufgeklappten Teilprozessen, wenn
 * Elemente an den Rand gezogen werden.
 */

import AutoResize from 'diagram-js/lib/features/auto-resize/AutoResize'
import type { Shape } from 'diagram-js/lib/model/Types'

import { is, isHorizontal } from '../util/ModelUtil'
import { LANE_BAND } from '../modeling/LaneUtil'

type Trbl = { top: number; bottom: number; left: number; right: number }

export default class BpmnAutoResize extends AutoResize {
  getPadding(shape: Shape): Trbl {
    if (is(shape, 'bpmn:Participant')) {
      return isHorizontal(shape)
        ? { top: 20, bottom: 20, left: LANE_BAND + 20, right: 20 }
        : { top: LANE_BAND + 20, bottom: 20, left: 20, right: 20 }
    }
    return { top: 20, bottom: 20, left: 20, right: 20 }
  }
}
