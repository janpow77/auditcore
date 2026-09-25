/**
 * Farbmenü: vordefinierte Füll-/Linienfarben und „Standard“ (entfernt die
 * Färbung). Die Farbliste ist über `config.colorPicker.colors` ersetzbar.
 */

import type PopupMenu from 'diagram-js/lib/features/popup-menu/PopupMenu'
import type { PopupMenuEntries } from 'diagram-js/lib/features/popup-menu/PopupMenuProvider'
import type { Element } from 'diagram-js/lib/model/Types'

import type Modeling from '../modeling/Modeling'
import type { Translate } from '../types'

export interface ColorOption {
  label: string
  fill?: string
  stroke?: string
}

export const DEFAULT_COLORS: ColorOption[] = [
  { label: 'Default' },
  { label: 'Blue', fill: '#dbeafe', stroke: '#1d4ed8' },
  { label: 'Green', fill: '#dcfce7', stroke: '#15803d' },
  { label: 'Yellow', fill: '#fef9c3', stroke: '#a16207' },
  { label: 'Orange', fill: '#ffedd5', stroke: '#c2410c' },
  { label: 'Red', fill: '#fee2e2', stroke: '#b91c1c' },
  { label: 'Purple', fill: '#f3e8ff', stroke: '#7e22ce' },
  { label: 'Grey', fill: '#f3f4f6', stroke: '#4b5563' },
]

function swatch(option: ColorOption): string {
  const fill = option.fill || '#ffffff'
  const stroke = option.stroke || '#1f2328'
  return (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" aria-hidden="true">' +
    `<rect x="3" y="3" width="18" height="18" rx="4" fill="${fill}" stroke="${stroke}" stroke-width="2"/></svg>`
  )
}

export default class ColorMenuProvider {
  static $inject = ['popupMenu', 'modeling', 'translate', 'config.colorPicker']

  private readonly colors: ColorOption[]

  constructor(
    popupMenu: PopupMenu,
    private readonly modeling: Modeling,
    private readonly translate: Translate,
    config?: { colors?: ColorOption[] },
  ) {
    this.colors = config?.colors?.length ? config.colors : DEFAULT_COLORS
    popupMenu.registerProvider('bpmn-color', this)
  }

  getPopupMenuEntries(target: Element | Element[]): PopupMenuEntries {
    const elements = Array.isArray(target) ? target : [target]
    const entries: PopupMenuEntries = {}
    this.colors.forEach((option, index) => {
      entries[`color-${index}`] = {
        label: this.translate(option.label),
        imageHtml: swatch(option),
        action: () => this.modeling.setColor(elements, { fill: option.fill || null, stroke: option.stroke || null }),
      }
    })
    return entries
  }
}
