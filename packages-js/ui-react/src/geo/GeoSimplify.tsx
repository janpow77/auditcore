import { useEffect, useRef, type FormEvent } from 'react'
import { intlFormatNumber } from '@flowaudit/common'
import { TOLERANCE_STEPS, vertexCount, type SimplifyUnit } from '@flowaudit/ui-core'
import { Button } from '../base/Button'
import { useElementId } from '../store'
import { GeoAreaSelect } from './GeoAreaSelect'
import { numberInput, useGeo } from './context'

const UNITS: readonly SimplifyUnit[] = ['meter', 'grad']

/** Natives `change` (Loslassen des Schiebers) wie `@change` der Vue-Fassung; React meldet sonst jede Bewegung. */
function useCommit(action: () => void) {
  const element = useRef<HTMLInputElement | null>(null)
  const latest = useRef(action)
  latest.current = action
  useEffect(() => {
    const node = element.current
    const listener = (): void => latest.current()
    node?.addEventListener('change', listener)
    return () => node?.removeEventListener('change', listener)
  }, [])
  return element
}

function SimplifyResultView() {
  const { state, t } = useGeo()
  const result = state.simplifyResult
  if (!result) return null
  return (
    <div className="fa-geo__stack" aria-live="polite" data-testid="geo-simplify-result">
      <p className="fa-geo__summary">{t('simplifyResult', { before: result.stuetzpunkte_vorher, after: result.stuetzpunkte_nachher })}</p>
      {result.entfallene_ringe.length ? <p className="fa-geo__muted">{t('simplifyDropped', { count: result.entfallene_ringe.length })}</p> : null}
      {result.geometrie ? null : <p className="fa-geo__notice">{t('simplifyGone')}</p>}
    </div>
  )
}

function Tolerance({ id, text }: { id: string; text: string }) {
  const { state, selection, controller, t } = useGeo()
  const steps = TOLERANCE_STEPS[state.simplifyUnit]
  const committed = useCommit(() => {
    if (selection.area) void controller.simplifyArea()
  })
  return (
    <label className="fa-geo__field">
      <span id={`${id}-tol`} className="fa-geo__label">{t('simplifyTolerance', { value: text })}</span>
      <input
        className="fa-geo__range"
        type="range"
        min="0"
        max={steps.length - 1}
        step="1"
        aria-labelledby={`${id}-tol`}
        aria-valuetext={text}
        data-testid="geo-simplify-tolerance"
        value={state.simplifyStep}
        onChange={(event) => numberInput(event.target.value, (value) => controller.setField('simplifyStep', value))}
        ref={committed}
      />
    </label>
  )
}

/** Vereinfachung einer Fläche mit Toleranz in Metern oder Grad. */
export function GeoSimplify() {
  const { state, selection, controller, t, locale } = useGeo()
  const id = useElementId('fa-geo-simplify')
  const value = selection.simplifyTolerance
  const text = state.simplifyUnit === 'meter' ? `${intlFormatNumber(value, locale)} m` : `${intlFormatNumber(value, locale, { maximumFractionDigits: 5 })}°`
  const run = (event: FormEvent): void => {
    event.preventDefault()
    void controller.simplifyArea()
  }
  return (
    <section className="fa-geo__card" aria-labelledby={`${id}-h`}>
      <h3 id={`${id}-h`} className="fa-geo__heading">{t('simplify')}</h3>
      <form className="fa-geo__stack" noValidate onSubmit={run}>
        <GeoAreaSelect testid="geo-simplify-area" />
        {selection.area ? <p className="fa-geo__muted">{t('simplifyVertices', { count: vertexCount(selection.area.geometry) })}</p> : null}
        <fieldset className="fa-geo__fieldset">
          <legend className="fa-geo__label">{t('unit')}</legend>
          {UNITS.map((unit) => (
            <label key={unit} className="fa-geo__check">
              <input type="radio" name={`${id}-unit`} value={unit} data-testid={`geo-unit-${unit}`} checked={state.simplifyUnit === unit} onChange={() => controller.setSimplifyUnit(unit)} /> {t(unit === 'meter' ? 'unitmeter' : 'unitgrad')}
            </label>
          ))}
        </fieldset>
        <Tolerance id={id} text={text} />
        <Button variant="primary" type="submit" loading={state.busy === 'simplify'} testId="geo-simplify-run">{t('simplifyRun')}</Button>
      </form>
      <SimplifyResultView />
    </section>
  )
}
