import { comparisonRows, indicatorLabels, type HitView, type MatchState, type ScreeningKey, type SubjectView } from '@auditcore/ui-core'
import { useScreeningText } from './shared'

const SYMBOLS: Record<MatchState, string> = { match: '✓', conflict: '✗', not_compared: '–', info: '' }
const STATE_KEYS: Record<MatchState, ScreeningKey | null> = { match: 'stateMatch', conflict: 'stateConflict', not_compared: 'stateNotCompared', info: null }

/** Gegenüberstellung Eingabe ↔ Listeneintrag mit Abgleich je Merkmal (wie `ScreeningComparison.vue`). */
export function ScreeningComparison({ subject, hit }: { subject: SubjectView; hit: HitView }) {
  const { t } = useScreeningText()
  const rows = comparisonRows(subject, hit, t)
  const hints = indicatorLabels(hit, t)
  const stateText = (state: MatchState): string => {
    const key = STATE_KEYS[state]
    return key ? t(key) : ''
  }
  return (
    <section className="fa-screening__panel" aria-labelledby="fa-screening-cmp-title">
      <h3 id="fa-screening-cmp-title">{t('comparison')}</h3>
      <table className="fa-screening__table fa-screening__cmp">
        <thead>
          <tr>
            <th scope="col">{t('attribute')}</th>
            <th scope="col">{t('input')}</th>
            <th scope="col">{t('listEntry')}</th>
            <th scope="col"><span className="fa-screening__sr">{t('matchColumn')}</span></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label} className={`fa-screening__cmp--${row.state}`}>
              <th scope="row">{row.label}</th>
              <td>{row.input}</td>
              <td>{row.entry}</td>
              <td className="fa-screening__state" title={stateText(row.state)}>
                <span aria-hidden="true">{SYMBOLS[row.state]}</span>
                <span className="fa-screening__sr">{stateText(row.state)}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {hints.length ? <p className="fa-screening__muted">{t('hints', { hints: hints.join(' · ') })}</p> : null}
    </section>
  )
}
