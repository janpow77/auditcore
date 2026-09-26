import { STATE_ICONS, STATE_KEYS, riskMessages, stateTone, type FlagState, type Locale } from '@flowaudit/ui-core'
import { useTranslation } from '../i18n'
import { classes } from '../store'

export interface RiskFlagStateProps {
  state: FlagState
  /** Code für die Beschriftung (Tabellenzelle), sonst nur der Zustand. */
  code?: string
  /** Nur Symbol sichtbar, Text für Screenreader und Tooltip. */
  compact?: boolean
  locale?: Locale
}

/** Zustand eines Merkmals mit Symbol (Farbe ist nie der einzige Bedeutungsträger), wie `RiskFlagState`. */
export function RiskFlagState({ state, code = '', compact = false, locale }: RiskFlagStateProps) {
  const { t } = useTranslation(riskMessages, locale)
  const text = t(STATE_KEYS[state])
  const label = code ? t('stateCell', { code, state: text }) : text
  return (
    <span
      className={classes('fa-risk-state', `fa-risk-state--${state}`, `fa-risk-state--${stateTone(state)}`, compact && 'fa-risk-state--compact')}
      title={compact ? label : undefined}
      aria-label={compact ? label : undefined}
      role={compact ? 'img' : undefined}
    >
      <span className="fa-risk-state__icon" aria-hidden="true">{STATE_ICONS[state]}</span>
      {compact ? null : <span className="fa-risk-state__text">{text}</span>}
    </span>
  )
}
