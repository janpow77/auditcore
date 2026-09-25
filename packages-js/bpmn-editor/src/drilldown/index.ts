import OverlaysModule from 'diagram-js/lib/features/overlays'

import SubProcessPlanes from './SubProcessPlanes'

export default {
  __depends__: [OverlaysModule],
  __init__: ['subProcessPlanes'],
  subProcessPlanes: ['type', SubProcessPlanes],
}
