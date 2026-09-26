import type { FormEvent } from 'react'
import { utmErrorKey } from '@auditcore/ui-core'
import { Button } from '../base/Button'
import { useElementId } from '../store'
import { useGeo } from './context'

/** Bezugspunkt aus UTM (Zone, Halbkugel, Ost-/Nordwert) über `POST /utm/geographisch` (wie `GeoUtmInput.vue`). */
export function GeoUtmInput() {
  const { state, selection, controller, t } = useGeo()
  const id = useElementId('fa-geo-utm')
  if (!selection.canFromUtm) return null
  const submit = (event: FormEvent): void => {
    event.preventDefault()
    void controller.applyUtm()
  }
  return (
    <details className="fa-geo__utm" data-testid="geo-utm-input">
      <summary>{t('utmInput')}</summary>
      <p id={`${id}-help`} className="fa-geo__muted">{t('utmInputHelp')}</p>
      <form className="fa-geo__row" noValidate aria-describedby={`${id}-help`} onSubmit={submit}>
        <label className="fa-geo__field">
          <span className="fa-geo__label">{t('utmZone')}</span>
          <input className="fa-geo__input fa-geo__input--short" inputMode="numeric" aria-invalid={state.utmError === 'zone'} data-testid="geo-utm-zone" value={state.zoneText} onChange={(event) => controller.setField('zoneText', event.target.value)} />
        </label>
        <label className="fa-geo__field">
          <span className="fa-geo__label">{t('utmHemisphere')}</span>
          <select value={state.northern ? 'N' : 'S'} className="fa-geo__input" data-testid="geo-utm-hemisphere" onChange={(event) => controller.setField('northern', event.target.value === 'N')}>
            <option value="N">{t('hemisphereNorth')}</option>
            <option value="S">{t('hemisphereSouth')}</option>
          </select>
        </label>
        <label className="fa-geo__field">
          <span className="fa-geo__label">{t('utmEast')}</span>
          <input className="fa-geo__input" inputMode="decimal" aria-invalid={state.utmError === 'east'} data-testid="geo-utm-east" value={state.eastText} onChange={(event) => controller.setField('eastText', event.target.value)} />
        </label>
        <label className="fa-geo__field">
          <span className="fa-geo__label">{t('utmNorth')}</span>
          <input className="fa-geo__input" inputMode="decimal" aria-invalid={state.utmError === 'north'} data-testid="geo-utm-north" value={state.northText} onChange={(event) => controller.setField('northText', event.target.value)} />
        </label>
        <Button type="submit" loading={state.busy === 'utm'} testId="geo-utm-apply">{t('apply')}</Button>
      </form>
      {state.utmError ? <p className="fa-geo__error" role="alert">{t(utmErrorKey(state.utmError))}</p> : null}
    </details>
  )
}
