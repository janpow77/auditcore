import { breakdownRows, formatScore, type Breakdown } from '@flowaudit/ui-core'
import { Badge } from '../base/Badge'
import { useScreeningText } from './shared'

/** Nachvollziehbare Aufschlüsselung des Scores eines Treffers. */
export function ScreeningScoreBreakdown({ breakdown }: { breakdown: Breakdown }) {
  const { t, locale } = useScreeningText()
  const rows = breakdownRows(breakdown, locale)
  const scale = breakdown.scale
  const score = (value: number): string => formatScore(value, scale, locale)
  return (
    <section className="fa-screening__panel" aria-labelledby="fa-screening-breakdown-title">
      <h3 id="fa-screening-breakdown-title">
        {t('breakdown')}
        <span className="fa-screening__muted">{t('method', { method: breakdown.method, min: scale.min, max: scale.max })}</span>
      </h3>
      {breakdown.consistent ? null : <p className="fa-screening__alert fa-screening__alert--warning" role="status">{t('inconsistent')}</p>}
      <table className="fa-screening__table fa-screening__steps">
        <tbody>
          {rows.map((row, index) => (
            <tr key={index} className={`fa-screening__steps--${row.tone}`}>
              <td>
                {row.label}
                {row.value ? <div className="fa-screening__muted">{row.value}</div> : null}
              </td>
              <td className="fa-screening__points">{row.points}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="fa-screening__classes">
        <Badge tone="accent">{t('level', { label: breakdown.class_label })}</Badge>
        <Badge>{t('minScoreBadge', { value: score(breakdown.min_score) })}</Badge>
        {breakdown.classes.map((c) => <Badge key={c.class}>{t('classFrom', { label: c.label, value: score(c.from) })}</Badge>)}
      </div>
    </section>
  )
}
