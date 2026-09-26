import KeyboardModule from 'diagram-js/lib/features/keyboard'
import EditorActionsModule from 'diagram-js/lib/features/editor-actions'
import KeyboardMoveModule from 'diagram-js/lib/navigation/keyboard-move'
import KeyboardMoveSelectionModule from 'diagram-js/lib/features/keyboard-move-selection'

import BpmnEditorActions from './BpmnEditorActions'
import BpmnKeyboardBindings from './BpmnKeyboardBindings'

export default {
  __depends__: [EditorActionsModule, KeyboardModule, KeyboardMoveModule, KeyboardMoveSelectionModule],
  __init__: ['bpmnEditorActions', 'bpmnKeyboardBindings'],
  bpmnEditorActions: ['type', BpmnEditorActions],
  bpmnKeyboardBindings: ['type', BpmnKeyboardBindings],
}
