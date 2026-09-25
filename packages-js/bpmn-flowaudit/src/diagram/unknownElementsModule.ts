/**
 * Keeps unknown flowaudit elements across import and export of the editor
 * by hooking the `import.parse.start` and `saveXML.serialized` events of
 * the core (both may return a replacement text).
 */

import { protectUnknownElements, restoreUnknownElements } from '../model/unknownElements'
import type { EventBus } from './services'

export class UnknownElementsGuard {
  static $inject = ['eventBus']

  constructor(eventBus: EventBus) {
    eventBus.on('import.parse.start', 2000, (event) => (typeof event.xml === 'string' ? protectUnknownElements(event.xml) : undefined))
    eventBus.on('saveXML.serialized', 2000, (event) => (typeof event.xml === 'string' ? restoreUnknownElements(event.xml) : undefined))
  }
}

export const unknownElementsModule = {
  __init__: ['flowauditUnknownElements'],
  flowauditUnknownElements: ['type', UnknownElementsGuard],
}
