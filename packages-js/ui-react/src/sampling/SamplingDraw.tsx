import type { FormEvent } from 'react'
import {
  selectionErrorKey,
  type AllocationMethod,
  type MethodProfile,
  type NamedOption,
  type SamplingTranslate,
  type SelectionError,
  type SelectionVariant,
} from '@flowaudit/ui-core'
import { Button } from '../base/Button'
import { useElementId } from '../store'

export interface SamplingDrawProps {
  profile: MethodProfile
  variants: readonly NamedOption<SelectionVariant>[]
  allocations: readonly NamedOption<AllocationMethod>[]
  stratified: boolean
  error: SelectionError | null
  busy?: boolean
  canRedraw?: boolean
  sampleSize: string
  seed: string
  variant: SelectionVariant | null
  allocation: AllocationMethod | null
  t: SamplingTranslate
  onSampleSizeChange: (value: string) => void
  onSeedChange: (value: string) => void
  onVariantChange: (value: SelectionVariant | null) => void
  onAllocationChange: (value: AllocationMethod | null) => void
  onDraw: (fresh: boolean) => void
}

function Choices(props: SamplingDrawProps) {
  const { t } = props
  return (
    <>
      {props.profile.kind === 'mus' ? (
        <label className="fa-sampling__field">
          <span className="fa-sampling__label">{t('variant')}</span>
          <select className="fa-sampling__select" data-testid="sampling-variant" value={props.variant ?? ''} onChange={(event) => props.onVariantChange(event.target.value as SelectionVariant)}>
            {props.variants.map((option) => <option key={option.id} value={option.id} title={option.description}>{option.label}</option>)}
          </select>
        </label>
      ) : null}
      {props.stratified ? (
        <label className="fa-sampling__field">
          <span className="fa-sampling__label">{t('allocation')}</span>
          <select className="fa-sampling__select" data-testid="sampling-allocation" value={props.allocation ?? ''} onChange={(event) => props.onAllocationChange(event.target.value === '' ? null : (event.target.value as AllocationMethod))}>
            <option value="">{t('choose')}</option>
            {props.allocations.map((option) => <option key={option.id} value={option.id}>{`${option.label} (${option.formula})`}</option>)}
          </select>
        </label>
      ) : null}
    </>
  )
}

/** Auswahl mit Umfang, Variante, Aufteilung und Seed (wie `SamplingDraw.vue`). */
export function SamplingDraw(props: SamplingDrawProps) {
  const { t } = props
  const id = useElementId('fa-sampling-draw')
  const submit = (event: FormEvent): void => {
    event.preventDefault()
    props.onDraw(false)
  }
  return (
    <form className="fa-sampling__form" noValidate aria-labelledby={`${id}-title`} onSubmit={submit}>
      <h3 id={`${id}-title`} className="fa-sampling__heading">{t('selection')}</h3>
      <div className="fa-sampling__draw-fields">
        <label className="fa-sampling__field">
          <span className="fa-sampling__label">{t('sampleSize')}</span>
          <input className="fa-sampling__input" inputMode="numeric" data-testid="sampling-sample-size" value={props.sampleSize} onChange={(event) => props.onSampleSizeChange(event.target.value)} />
        </label>
        <Choices {...props} />
        <label className="fa-sampling__field">
          <span className="fa-sampling__label">{t('seed')}</span>
          <input className="fa-sampling__input fa-sampling__input--mono" inputMode="numeric" data-testid="sampling-seed" aria-describedby={`${id}-seed-hint`} value={props.seed} onChange={(event) => props.onSeedChange(event.target.value)} />
          <span id={`${id}-seed-hint`} className="fa-sampling__hint">{t('seedHint')}</span>
        </label>
      </div>
      {props.error ? <p className="fa-sampling__error" role="alert">{t(selectionErrorKey(props.error))}</p> : null}
      <div className="fa-sampling__actions">
        <Button variant="primary" type="submit" loading={props.busy} testId="sampling-draw">{t('draw')}</Button>
        {props.canRedraw ? <Button variant="secondary" disabled={props.busy} testId="sampling-redraw" onClick={() => props.onDraw(true)}>{t('redraw')}</Button> : null}
      </div>
    </form>
  )
}
