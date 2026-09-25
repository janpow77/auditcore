import SnappingModule from 'diagram-js/lib/features/snapping'

import BpmnCreateMoveSnapping from './BpmnCreateMoveSnapping'

export default {
  __depends__: [SnappingModule],
  __init__: ['createMoveSnapping'],
  createMoveSnapping: ['type', BpmnCreateMoveSnapping],
}
