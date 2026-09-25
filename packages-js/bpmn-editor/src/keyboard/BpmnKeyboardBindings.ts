/**
 * Tastenkürzel (zusätzlich zu Rückgängig, Wiederholen, Kopieren, Einfügen,
 * Löschen und Zoom aus diagram-js):
 *
 * Strg+A alles auswählen · Strg+F suchen · E Beschriftung bearbeiten ·
 * R Element ersetzen · S Raumwerkzeug · L Lasso · H Hand ·
 * C Verbinden · M Übersichtskarte · 1 Einpassen
 */

import { isCmd, isKey, isShift } from 'diagram-js/lib/features/keyboard/KeyboardUtil'

import type { EventBus } from '../types'

interface KeyboardService {
  addListener(priority: number, listener: (context: { keyEvent: KeyboardEvent }) => boolean | void): void
}
interface EditorActionsService {
  isRegistered(action: string): boolean
  trigger(action: string, options?: unknown): unknown
}

interface Binding {
  action: string
  keys: string[]
  cmd?: boolean
  shift?: boolean
  options?: unknown
}

export const BINDINGS: Binding[] = [
  { action: 'selectElements', keys: ['a', 'A'], cmd: true },
  { action: 'find', keys: ['f', 'F'], cmd: true },
  { action: 'directEditing', keys: ['e', 'E'] },
  { action: 'replaceElement', keys: ['r', 'R'] },
  { action: 'spaceTool', keys: ['s', 'S'] },
  { action: 'lassoTool', keys: ['l', 'L'] },
  { action: 'handTool', keys: ['h', 'H'] },
  { action: 'globalConnectTool', keys: ['c', 'C'] },
  { action: 'toggleMinimap', keys: ['m', 'M'] },
  { action: 'zoomFit', keys: ['1'] },
]

export default class BpmnKeyboardBindings {
  static $inject = ['eventBus', 'keyboard']

  constructor(eventBus: EventBus, keyboard: KeyboardService) {
    eventBus.on('editorActions.init', 400, (event: { editorActions: EditorActionsService }) => {
      const editorActions = event.editorActions
      for (const binding of BINDINGS) {
        if (!editorActions.isRegistered(binding.action)) continue
        keyboard.addListener(900, (context) => {
          const keyEvent = context.keyEvent
          if (!isKey(binding.keys, keyEvent)) return
          if (!!binding.cmd !== isCmd(keyEvent)) return
          if (binding.shift !== undefined && binding.shift !== isShift(keyEvent)) return
          editorActions.trigger(binding.action, binding.options)
          return true
        })
      }
    })
  }
}
