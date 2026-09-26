/**
 * Menü „Ausrichten/Verteilen“ für Mehrfachauswahl.
 */

import type PopupMenu from 'diagram-js/lib/features/popup-menu/PopupMenu'
import type { PopupMenuEntries } from 'diagram-js/lib/features/popup-menu/PopupMenuProvider'
import type AlignElements from 'diagram-js/lib/features/align-elements/AlignElements'
import type DistributeElements from 'diagram-js/lib/features/distribute-elements/DistributeElements'
import type { Element } from 'diagram-js/lib/model/Types'

import { toolIcons } from '../icons/Icons'
import type { Translate } from '../types'

type Alignment = 'left' | 'center' | 'right' | 'top' | 'middle' | 'bottom'

const ALIGN_OPTIONS: { id: Alignment; label: string; icon: string }[] = [
  { id: 'left', label: 'Align left', icon: toolIcons.alignLeft },
  { id: 'center', label: 'Align center', icon: toolIcons.alignCenter },
  { id: 'right', label: 'Align right', icon: toolIcons.alignRight },
  { id: 'top', label: 'Align top', icon: toolIcons.alignTop },
  { id: 'middle', label: 'Align middle', icon: toolIcons.alignMiddle },
  { id: 'bottom', label: 'Align bottom', icon: toolIcons.alignBottom },
]

export default class AlignMenuProvider {
  static $inject = ['popupMenu', 'alignElements', 'distributeElements', 'translate']

  constructor(
    popupMenu: PopupMenu,
    private readonly alignElements: AlignElements,
    private readonly distributeElements: DistributeElements,
    private readonly translate: Translate,
  ) {
    popupMenu.registerProvider('bpmn-align', this)
  }

  getPopupMenuEntries(target: Element | Element[]): PopupMenuEntries {
    const elements = Array.isArray(target) ? target : [target]
    const entries: PopupMenuEntries = {}
    for (const option of ALIGN_OPTIONS) {
      entries[`align-${option.id}`] = {
        label: this.translate(option.label),
        imageHtml: option.icon,
        group: { id: 'align', name: this.translate('Align') },
        action: () => this.alignElements.trigger(elements, option.id),
      }
    }
    entries['distribute-horizontally'] = {
      label: this.translate('Distribute horizontally'),
      imageHtml: toolIcons.distributeHorizontal,
      group: { id: 'distribute', name: this.translate('Distribute') },
      action: () => this.distributeElements.trigger(elements, 'horizontal'),
    }
    entries['distribute-vertically'] = {
      label: this.translate('Distribute vertically'),
      imageHtml: toolIcons.distributeVertical,
      group: { id: 'distribute', name: this.translate('Distribute') },
      action: () => this.distributeElements.trigger(elements, 'vertical'),
    }
    return entries
  }
}
