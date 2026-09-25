import PopupMenuModule from 'diagram-js/lib/features/popup-menu'
import AlignElementsModule from 'diagram-js/lib/features/align-elements'
import DistributeElementsModule from 'diagram-js/lib/features/distribute-elements'

import ReplaceModule from '../replace'
import AlignMenuProvider from './AlignMenuProvider'
import ColorMenuProvider from './ColorMenuProvider'
import ReplaceMenuProvider from './ReplaceMenuProvider'

export default {
  __depends__: [PopupMenuModule, ReplaceModule, AlignElementsModule, DistributeElementsModule],
  __init__: ['replaceMenuProvider', 'colorMenuProvider', 'alignMenuProvider'],
  replaceMenuProvider: ['type', ReplaceMenuProvider],
  colorMenuProvider: ['type', ColorMenuProvider],
  alignMenuProvider: ['type', AlignMenuProvider],
}
