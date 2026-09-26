import type { FormEvent } from 'react'
import { formatDistance, type BadgeTone, type GeoMessageKey, type LocateResult, type Translate, type Locale } from '@auditcore/ui-core'
import { Badge } from '../base/Badge'
import { Button } from '../base/Button'
import { useElementId } from '../store'
import { GeoAreaSelect } from './GeoAreaSelect'
import { numberInput, useGeo } from './context'

const TONES: Readonly<Record<string, BadgeTone>> = { innen: 'success', aussen: 'neutral', rand: 'warning' }

function boundaryText(found: LocateResult, t: Translate<GeoMessageKey>, locale: Locale): string {
  const how = found.lage === 'rand' ? t('boundaryExact') : t('boundaryTolerance', { tolerance: formatDistance(found.rand_toleranz_m, locale) })
  return t('boundaryCase', { how, rule: t(found.rand_gilt_als_innen ? 'ruleInside' : 'ruleOutside') })
}

function LocateResultView() {
  const { state, t, locale } = useGeo()
  const result = state.locateResult
  if (!result) return null
  return (
    <div className="fa-geo__stack" aria-live="polite" data-testid="geo-locate-result">
      <p className="fa-geo__summary">
        <Badge tone={TONES[result.lage_mit_toleranz]} testId="geo-position">{t(`position${result.lage_mit_toleranz}` as GeoMessageKey)}</Badge>{' '}
        <strong>{t(result.enthaelt ? 'contains' : 'notContains')}</strong>
      </p>
      {result.lage_mit_toleranz === 'rand' ? <p className="fa-geo__notice" data-testid="geo-boundary-case">{boundaryText(result, t, locale)}</p> : null}
      {result.lage === 'aussen' ? <p className="fa-geo__muted">{t('distance', { distance: formatDistance(result.abstand_m, locale) })}</p> : null}
      {result.hinweise.length ? (
        <details className="fa-geo__details">
          <summary>{t('notes')}</summary>
          <ul className="fa-geo__list">{result.hinweise.map((note) => <li key={note}>{note}</li>)}</ul>
        </details>
      ) : null}
    </div>
  )
}

/** Punkt in Fläche mit Randregel und Toleranz. */
export function GeoLocate() {
  const { state, controller, t } = useGeo()
  const id = useElementId('fa-geo-locate')
  const run = (event: FormEvent): void => {
    event.preventDefault()
    void controller.checkLocation()
  }
  return (
    <section className="fa-geo__card" aria-labelledby={`${id}-h`}>
      <h3 id={`${id}-h`} className="fa-geo__heading">{t('locate')}</h3>
      <form className="fa-geo__stack" noValidate onSubmit={run}>
        <GeoAreaSelect testid="geo-locate-area" />
        <label className="fa-geo__check">
          <input type="checkbox" data-testid="geo-boundary-inside" checked={state.boundaryInside} onChange={(event) => controller.setField('boundaryInside', event.target.checked)} /> {t('boundaryInside')}
        </label>
        <p className="fa-geo__muted">{t('boundaryHelp')}</p>
        <div className="fa-geo__row">
          <label className="fa-geo__field">
            <span className="fa-geo__label">{t('tolerance')}</span>
            <input className="fa-geo__input" type="number" min="0" step="1" data-testid="geo-tolerance" value={state.toleranceMetres} onChange={(event) => numberInput(event.target.value, (value) => controller.setField('toleranceMetres', value))} />
          </label>
          <Button variant="primary" type="submit" loading={state.busy === 'locate'} testId="geo-locate-run">{t('locateRun')}</Button>
        </div>
      </form>
      <LocateResultView />
    </section>
  )
}
