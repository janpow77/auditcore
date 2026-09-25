import ContextPadModule from 'diagram-js/lib/features/context-pad'
import ConnectModule from 'diagram-js/lib/features/connect'
import CreateModule from 'diagram-js/lib/features/create'
import SelectionModule from 'diagram-js/lib/features/selection'

import AutoPlaceModule from '../auto-place'
import PopupMenuModule from '../popup-menu'
import ContextPadProvider from './ContextPadProvider'

export default {
  __depends__: [ContextPadModule, ConnectModule, CreateModule, SelectionModule, AutoPlaceModule, PopupMenuModule],
  __init__: ['contextPadProvider'],
  contextPadProvider: ['type', ContextPadProvider],
}
