import { CARD_COLORS, MAX_CARD_IMAGE_BYTES } from '@auditcore/kanban-core'
import type { Locale } from '@auditcore/ui-core'
import { useState, type ChangeEvent } from 'react'
import { Button } from '../base/Button'
import { useKanbanDialogText } from './text'

export interface CardAppearanceProps {
  color: string | null
  image: string | null
  readOnly?: boolean
  locale?: Locale
  onChange: (patch: { color?: string; image?: string }) => void
}

const RAINBOW = { background: 'conic-gradient(red, yellow, lime, aqua, blue, magenta, red)' }

function Swatches({ color, readOnly = false, locale, onChange }: CardAppearanceProps) {
  const { t } = useKanbanDialogText(locale)
  return (
    <div className="fa-kanban-detail__row" role="group" aria-label={t('appearance')}>
      {CARD_COLORS.map((swatch) => (
        <button
          key={swatch.value}
          type="button"
          className="fa-kanban-detail__swatch"
          style={{ background: swatch.value }}
          title={swatch.label}
          aria-label={swatch.label}
          aria-pressed={color === swatch.value}
          disabled={readOnly}
          onClick={() => onChange({ color: color === swatch.value ? '' : swatch.value })}
        />
      ))}
      {readOnly ? null : (
        <label className="fa-kanban-detail__swatch" title={t('customColor')} style={RAINBOW}>
          <input type="color" className="fa-sr-only" value={color ?? '#7c3aed'} aria-label={t('customColor')} onChange={(event) => onChange({ color: event.target.value })} />
        </label>
      )}
      {color && !readOnly ? <Button size="sm" variant="ghost" icon="close" iconOnly label={t('clearColor')} onClick={() => onChange({ color: '' })} /> : null}
    </div>
  )
}

/** Kartendesign wie `CardAppearance.vue`: Farbe, eigene Farbe, Hintergrundbild (höchstens 2 MB). */
export function CardAppearance(props: CardAppearanceProps) {
  const { t } = useKanbanDialogText(props.locale)
  const [problem, setProblem] = useState('')
  const pickImage = (event: ChangeEvent<HTMLInputElement>): void => {
    const input = event.target
    const file = input.files?.[0]
    input.value = ''
    setProblem('')
    if (!file) return
    if (file.size > MAX_CARD_IMAGE_BYTES) {
      setProblem(t('imageTooLarge'))
      return
    }
    const reader = new FileReader()
    reader.onload = () => props.onChange({ image: String(reader.result) })
    reader.readAsDataURL(file)
  }
  return (
    <div className="fa-kanban-detail__section">
      <span className="fa-kanban-detail__label">{t('appearance')}</span>
      <Swatches {...props} />
      {props.image ? <img className="fa-kanban-detail__image" src={props.image} alt={t('image')} /> : null}
      {props.readOnly ? null : (
        <div className="fa-kanban-detail__row">
          <label className="fa-button fa-button--secondary fa-button--sm">
            {t('uploadImage')}
            <input type="file" accept="image/*" className="fa-sr-only" onChange={pickImage} />
          </label>
          {props.image ? <Button size="sm" variant="ghost" icon="trash" onClick={() => props.onChange({ image: '' })}>{t('removeImage')}</Button> : null}
        </div>
      )}
      {problem ? <p className="fa-field__note" role="alert">{problem}</p> : null}
    </div>
  )
}
