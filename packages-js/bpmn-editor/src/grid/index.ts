import GridSnappingModule from 'diagram-js/lib/features/grid-snapping'

import GridDisplay from './GridDisplay'
import GridSnapping from './GridSnapping'

export default {
  __depends__: [GridSnappingModule],
  __init__: ['gridSnapping', 'gridDisplay'],
  gridSnapping: ['type', GridSnapping],
  gridDisplay: ['type', GridDisplay],
}
