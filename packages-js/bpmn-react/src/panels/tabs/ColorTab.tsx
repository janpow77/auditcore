/** Colour of the selected element: audit palette, removal and colour from markers. */

import { PALETTE_COLORS, type PaletteColor } from '@auditcore/bpmn-flowaudit'
import { colorFromMarkers } from '@auditcore/bpmn-flowaudit/ui'
import { ColorSwatches } from '../../base/ColorSwatches'
import { useEditorContext, useSelectionState } from '../../context'
import { useI18n } from '../../i18n'

export function ColorTab({ palette }: { palette?: readonly PaletteColor[] }) {
  const { t } = useI18n()
  const { editor, readonly } = useEditorContext()
  const { element, extensions } = useSelectionState()
  const fromMarkers = colorFromMarkers(extensions.markers)

  const apply = (color: { fill: string; stroke: string } | null) => {
    if (element) editor.services().modeling.setColor([element], { fill: color?.fill ?? null, stroke: color?.stroke ?? null })
  }

  return (
    <div className="fa-tab-color">
      <h3 className="fa-section__title">{t('props.color.palette')}</h3>
      <ColorSwatches colors={palette ?? PALETTE_COLORS} disabled={readonly()} onChoose={apply} />
      {fromMarkers ? (
        <button type="button" className="fa-btn fa-section" disabled={readonly()} onClick={() => apply(fromMarkers)}>
          <span className="fa-swatch" style={{ background: fromMarkers.fill, borderColor: fromMarkers.stroke }} />
          {t('props.color.fromMarkers')}
        </button>
      ) : null}
    </div>
  )
}
