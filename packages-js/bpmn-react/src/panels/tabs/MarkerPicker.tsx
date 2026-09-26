/**
 * Toggle chips for the domain markers of the selected element. Turning on a
 * colouring marker (e.g. finding) also reports its colour.
 */

import { label, MARKERS, type Marker } from '@auditcore/bpmn-flowaudit'
import { setMarkerText, toggleMarker } from '@auditcore/bpmn-flowaudit/ui'
import { FaIcon } from '../../base/FaIcon'
import { classes } from '../../hooks'
import { useI18n } from '../../i18n'
import { CommitField } from '../CommitField'

export interface MarkerPickerProps {
  markers: Marker[]
  disabled?: boolean
  className?: string
  onUpdate: (markers: Marker[]) => void
  onColor?: (color: { fill: string; stroke: string }) => void
}

export function MarkerPicker({ markers, disabled, className, onUpdate, onColor }: MarkerPickerProps) {
  const { t, locale } = useI18n()
  const has = (type: string) => markers.some((marker) => marker.type === type)

  const toggle = (type: string) => {
    const next = toggleMarker(markers, type)
    onUpdate(next.markers)
    if (next.color) onColor?.(next.color)
  }

  return (
    <fieldset className={classes('fa-markers', className)}>
      <legend className="fa-label">{t('props.markers')}</legend>
      <p className="fa-help">{t('props.markersHelp')}</p>
      <div className="fa-markers__chips">
        {Object.entries(MARKERS).map(([type, text]) => (
          <button key={type} type="button" className="fa-chip" aria-pressed={has(type)} disabled={disabled} onClick={() => toggle(type)}>
            <FaIcon name={`marker-${type}`} size={14} />
            {label(text, locale)}
          </button>
        ))}
      </div>
      {markers.map((marker) => (
        <label key={marker.type} className="fa-field fa-markers__text">
          <span className="fa-label">
            {label(MARKERS[marker.type], locale) || marker.type} – {t('field.text')}
          </span>
          <CommitField className="fa-input" value={marker.text ?? ''} disabled={disabled} onCommit={(text) => onUpdate(setMarkerText(markers, marker.type, text))} />
        </label>
      ))}
    </fieldset>
  )
}
