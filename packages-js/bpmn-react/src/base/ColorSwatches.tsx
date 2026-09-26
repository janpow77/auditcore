/** List of palette colours with meaning plus „remove colour“ (legacy colour menu). */

import type { PaletteColor } from '@flowaudit/bpmn-flowaudit'
import { useI18n } from '../i18n'

export interface ColorSwatchesProps {
  colors: readonly PaletteColor[]
  disabled?: boolean
  onChoose: (color: PaletteColor | null) => void
}

export function ColorSwatches({ colors, disabled, onChoose }: ColorSwatchesProps) {
  const { t } = useI18n()
  return (
    <div className="fa-swatches" role="menu">
      {colors.map((color) => (
        <button key={color.id} type="button" role="menuitem" className="fa-menu-item" title={color.meaning} disabled={disabled} onClick={() => onChoose(color)}>
          <span className="fa-swatch" style={{ background: color.fill, borderColor: color.stroke }} />
          <span>
            {color.label}
            <span className="fa-menu-hint">{color.meaning}</span>
          </span>
        </button>
      ))}
      <button type="button" role="menuitem" className="fa-menu-item" disabled={disabled} onClick={() => onChoose(null)}>
        <span className="fa-swatch fa-swatch--empty" />
        {t('toolbar.colorRemove')}
      </button>
    </div>
  )
}
