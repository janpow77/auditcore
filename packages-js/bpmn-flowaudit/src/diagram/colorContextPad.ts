/**
 * Context pad entry „Farbe festlegen“ directly at the element, ported from
 * `farbContextPad.ts` of the audit_designer. The entry only draws the icon
 * and reports the click through the event bus (`flowaudit.farbe.oeffnen`,
 * unchanged name); the picker itself is rendered by the UI. The colour is
 * set with `modeling.setColor` (`bioc:` and `color:` attributes).
 */

import { iconSvg } from '../icons/icons'
import type { PaletteColor } from '../export/colorPalette'
import type { ContextPad, ContextPadEntry, DiagramElement, EventBus, Modeling, Translate } from './services'

export const COLOR_PICKER_EVENT = 'flowaudit.farbe.oeffnen'

/** Elements without meaningful colour (root, labels). */
export function isColorable(element: DiagramElement | null | undefined): boolean {
  const type = element?.businessObject?.$type ?? ''
  if (!element || !type.startsWith('bpmn:')) return false
  if (type === 'bpmn:Process' || type === 'bpmn:Collaboration') return false
  return !element.labelTarget
}

export class ColorContextPadProvider {
  static $inject = ['contextPad', 'eventBus', 'translate']

  constructor(
    contextPad: ContextPad,
    private readonly eventBus: EventBus,
    private readonly translate: Translate,
  ) {
    // After the default entries so the order stays stable.
    contextPad.registerProvider(500, this)
  }

  getContextPadEntries(element: DiagramElement): (entries: Record<string, ContextPadEntry>) => Record<string, ContextPadEntry> {
    return (entries) => {
      if (!isColorable(element)) return entries
      return {
        ...entries,
        'flowaudit-farbe': {
          group: 'edit',
          className: 'flowaudit-farbe-eintrag',
          title: this.translate('Set color'),
          html: `<span class="fa-context-icon">${iconSvg('color', 18)}</span>`,
          action: {
            click: (event: Event) => {
              this.eventBus.fire(COLOR_PICKER_EVENT, { element, event })
              // false keeps diagram-js from treating the click as a drag.
              return false
            },
          },
        },
      }
    }
  }
}

export const colorContextPadModule = {
  __init__: ['flowauditColorContextPad'],
  flowauditColorContextPad: ['type', ColorContextPadProvider],
}

/** Sets a palette colour; `null` removes the colouring. */
export function setColor(modeling: Pick<Modeling, 'setColor'>, elements: DiagramElement[], color: Pick<PaletteColor, 'fill' | 'stroke'> | null): void {
  if (!elements.length) return
  modeling.setColor(elements, { fill: color ? color.fill : null, stroke: color ? color.stroke : null })
}
