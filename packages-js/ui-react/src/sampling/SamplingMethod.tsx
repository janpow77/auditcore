import { methodGroups, methodStatusKey, methodTone, type MethodProfile, type SamplingCatalogue, type SamplingTranslate } from '@flowaudit/ui-core'
import { Badge } from '../base/Badge'
import { useElementId } from '../store'

export interface SamplingMethodProps {
  catalogue: SamplingCatalogue
  profile: MethodProfile | null
  methodId: string
  t: SamplingTranslate
  onMethodChange: (id: string) => void
}

/** Methodenwahl mit Status, Formel und Quelle (wie `SamplingMethod.vue`). */
export function SamplingMethod({ catalogue, profile, methodId, t, onMethodChange }: SamplingMethodProps) {
  const id = useElementId('fa-sampling-method')
  return (
    <section className="fa-sampling__card" aria-labelledby={`${id}-title`}>
      <h3 id={`${id}-title`} className="fa-sampling__heading">{t('method')}</h3>
      <label className="fa-sampling__field">
        <span className="fa-sampling__label">{t('method')}</span>
        <select className="fa-sampling__select" data-testid="sampling-method" aria-describedby={`${id}-hint`} value={methodId} onChange={(event) => onMethodChange(event.target.value)}>
          {methodGroups(catalogue).map((group) => (
            <optgroup key={group.kind} label={group.label}>
              {group.methods.map((method) => <option key={method.id} value={method.id}>{method.label}</option>)}
            </optgroup>
          ))}
        </select>
      </label>
      <p id={`${id}-hint`} className="fa-sampling__hint">{t('methodHint')}</p>
      {profile ? (
        <div className="fa-sampling__profile">
          <p><Badge tone={methodTone(profile)}>{t(methodStatusKey(profile))}</Badge>{' '}<code className="fa-sampling__id">{profile.id}</code></p>
          <p><span className="fa-sampling__label">{t('formula')}</span><br /><span className="fa-sampling__formula">{profile.formula}</span></p>
          <p className="fa-sampling__note">{profile.note}</p>
          <details className="fa-sampling__source">
            <summary>{t('source')}</summary>
            <code>{profile.source}</code>
          </details>
        </div>
      ) : null}
    </section>
  )
}
