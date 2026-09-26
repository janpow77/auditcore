import { useState, type FormEvent } from 'react'
import { displayName, formatDegrees, formatMetres, type LatLon } from '@flowaudit/ui-core'
import { Button } from '../base/Button'
import { useElementId } from '../store'
import { useGeo } from './context'

const submit = (action: () => void) => (event: FormEvent) => {
  event.preventDefault()
  action()
}

function Coordinates() {
  const { state, controller, t } = useGeo()
  return (
    <>
      <form className="fa-geo__row" noValidate onSubmit={submit(() => void controller.applyTexts())}>
        <label className="fa-geo__field">
          <span className="fa-geo__label">{t('lat')}</span>
          <input className="fa-geo__input" inputMode="decimal" aria-invalid={state.coordinateError === 'lat'} data-testid="geo-lat" value={state.latText} onChange={(event) => controller.setField('latText', event.target.value)} />
        </label>
        <label className="fa-geo__field">
          <span className="fa-geo__label">{t('lon')}</span>
          <input className="fa-geo__input" inputMode="decimal" aria-invalid={state.coordinateError === 'lon'} data-testid="geo-lon" value={state.lonText} onChange={(event) => controller.setField('lonText', event.target.value)} />
        </label>
        <Button type="submit" testId="geo-apply">{t('apply')}</Button>
      </form>
      {state.coordinateError ? <p className="fa-geo__error" role="alert">{t(state.coordinateError === 'lat' ? 'errorlat' : 'errorlon')}</p> : null}
    </>
  )
}

function FromPoint() {
  const { points, controller, t } = useGeo()
  const [pointId, setPointId] = useState('')
  if (!points.length) return null
  const take = (): void => {
    const point = points.find((entry) => entry.id === pointId)
    if (point) void controller.setReference({ lat: point.lat, lon: point.lon })
  }
  return (
    <div className="fa-geo__row">
      <label className="fa-geo__field fa-geo__grow">
        <span className="fa-geo__label">{t('fromPoint')}</span>
        <select className="fa-geo__input" data-testid="geo-point-select" value={pointId} onChange={(event) => setPointId(event.target.value)}>
          <option value="">{t('choose')}</option>
          {points.map((point) => <option key={point.id} value={point.id}>{displayName(point)}</option>)}
        </select>
      </label>
      <Button disabled={!pointId} testId="geo-point-take" onClick={take}>{t('apply')}</Button>
    </div>
  )
}

function Geocode() {
  const { state, selection, controller, t } = useGeo()
  const [address, setAddress] = useState('')
  if (!selection.canGeocode) return null
  const result = state.geocodeResult
  const pick = (point: LatLon) => () => void controller.setReference(point)
  return (
    <>
      <form className="fa-geo__row" noValidate onSubmit={submit(() => void controller.geocode(address))}>
        <label className="fa-geo__field fa-geo__grow">
          <span className="fa-geo__label">{t('geocode')}</span>
          <input className="fa-geo__input" type="search" autoComplete="off" data-testid="geo-address" value={address} onChange={(event) => setAddress(event.target.value)} />
        </label>
        <Button type="submit" loading={state.busy === 'geocode'}>{t('geocodeRun')}</Button>
      </form>
      <p className="fa-geo__muted">{t('geocodeHelp')}</p>
      {result ? (
        <ul className="fa-geo__list" aria-live="polite">
          {result.treffer.length ? null : <li>{t('geocodeNone')}</li>}
          {result.treffer.map((hit) => (
            <li key={hit.rang}>
              <button type="button" className="fa-geo__link" onClick={pick({ lat: hit.lat, lon: hit.lon })}>{hit.anzeigename ?? `${hit.lat}, ${hit.lon}`}</button>
            </li>
          ))}
          <li className="fa-geo__muted">{result.namensnennung}</li>
        </ul>
      ) : null}
    </>
  )
}

function Facts() {
  const { state, t, locale } = useGeo()
  const { reference, utm } = state
  if (!reference) return null
  const utmText = utm
    ? t('utmValue', { zone: utm.zone, hemisphere: utm.nordhalbkugel ? 'N' : 'S', east: formatMetres(utm.ost, locale), north: formatMetres(utm.nord, locale) })
    : ''
  return (
    <dl className="fa-geo__facts" aria-live="polite" data-testid="geo-reference">
      <dt>{t('reference')}</dt>
      <dd>{`${formatDegrees(reference.lat, locale)}, ${formatDegrees(reference.lon, locale)}`}</dd>
      <dt>{t('utm')}</dt>
      <dd data-testid="geo-utm">
        {utmText} {utm?.epsg ? <span className="fa-geo__muted">({t('utmEpsg', { epsg: utm.epsg })})</span> : null}
      </dd>
    </dl>
  )
}

function Ellipsoid() {
  const { state, controller, t } = useGeo()
  if (!state.catalogue || !state.reference) return null
  return (
    <label className="fa-geo__field">
      <span className="fa-geo__label">{t('ellipsoid')}</span>
      <select
        className="fa-geo__input"
        data-testid="geo-ellipsoid"
        value={state.ellipsoid}
        onChange={(event) => {
          controller.setField('ellipsoid', event.target.value)
          void controller.refreshUtm()
        }}
      >
        {state.catalogue.ellipsoide.map((entry) => <option key={entry} value={entry}>{entry}</option>)}
      </select>
    </label>
  )
}

/** Bezugspunkt: Koordinaten, Übernahme eines Punktes, Adresssuche (nur freigegeben), UTM. */
export function GeoReference() {
  const { state, t } = useGeo()
  const id = useElementId('fa-geo-ref')
  return (
    <section className="fa-geo__card" aria-labelledby={`${id}-h`}>
      <h3 id={`${id}-h`} className="fa-geo__heading">{t('reference')}</h3>
      <p className="fa-geo__muted">{t('referenceHelp')}</p>
      <Coordinates />
      <FromPoint />
      <Geocode />
      <Facts />
      <Ellipsoid />
      {state.utm ? <p className="fa-geo__muted">{t('utmNote')}</p> : null}
    </section>
  )
}
