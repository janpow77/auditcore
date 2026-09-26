import type { FormEvent } from 'react'
import { displayName, formatDistance } from '@flowaudit/ui-core'
import { Button } from '../base/Button'
import { useElementId } from '../store'
import { numberInput, useGeo } from './context'

function RadiusResultView() {
  const { state, points, t, locale } = useGeo()
  const result = state.radiusResult
  if (!result) return null
  const names = new Map(points.map((point) => [point.id, displayName(point)]))
  return (
    <div aria-live="polite" data-testid="geo-radius-result">
      <p className="fa-geo__summary">{t('radiusSummary', { hits: result.treffer.length, checked: result.geprueft, radius: formatDistance(result.radius_m, locale) })}</p>
      {result.treffer.length ? (
        <table className="fa-geo__table">
          <thead>
            <tr>
              <th scope="col">{t('colName')}</th>
              <th scope="col" className="fa-geo__num">{t('colDistance')}</th>
            </tr>
          </thead>
          <tbody>
            {result.treffer.map((hit) => (
              <tr key={hit.id}>
                <td>{names.get(hit.id) ?? hit.id}</td>
                <td className="fa-geo__num">{formatDistance(hit.abstand_m, locale)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </div>
  )
}

/** Umkreissuche um den Bezugspunkt mit wählbarem Erdmodell. */
export function GeoRadius() {
  const { state, controller, t } = useGeo()
  const id = useElementId('fa-geo-radius')
  const run = (event: FormEvent): void => {
    event.preventDefault()
    void controller.searchRadius()
  }
  return (
    <section className="fa-geo__card" aria-labelledby={`${id}-h`}>
      <h3 id={`${id}-h`} className="fa-geo__heading">{t('radius')}</h3>
      <form className="fa-geo__row" noValidate onSubmit={run}>
        <label className="fa-geo__field">
          <span className="fa-geo__label">{t('radiusMetres')}</span>
          <input className="fa-geo__input" type="number" min="0" step="100" data-testid="geo-radius" value={state.radiusMetres} onChange={(event) => numberInput(event.target.value, (value) => controller.setField('radiusMetres', value))} />
        </label>
        {state.catalogue ? (
          <label className="fa-geo__field fa-geo__grow">
            <span className="fa-geo__label">{t('earthModel')}</span>
            <select className="fa-geo__input" data-testid="geo-earth-model" value={state.earthModel ?? ''} onChange={(event) => controller.setField('earthModel', event.target.value)}>
              {state.catalogue.erdmodelle.map((model) => (
                <option key={model.id} value={model.id} title={model.beschreibung}>{model.empfohlen ? t('recommended', { label: model.id }) : model.id}</option>
              ))}
            </select>
          </label>
        ) : null}
        <Button variant="primary" type="submit" loading={state.busy === 'radius'} testId="geo-radius-run">{t('radiusRun')}</Button>
      </form>
      <RadiusResultView />
    </section>
  )
}
