import { SCREENING_KINDS, kindProfiles, kindSources, profileKeyOf, selectedProfile, type RunRequest, type ScreeningKind, type SettingsView, type SourceView } from '@auditcore/ui-core'
import { Badge } from '../base/Badge'
import { ErrorList, codeKey, useScreeningText } from './shared'
import { useRunForm } from './useRunForm'

export interface ScreeningRunFormProps {
  settings: SettingsView
  sources: readonly SourceView[]
  busy: boolean
  onSubmit: (request: RunRequest) => void
}

function KindChoice({ kind, onKind }: { kind: ScreeningKind; onKind: (kind: ScreeningKind) => void }) {
  const { t } = useScreeningText()
  return (
    <fieldset className="fa-screening__field">
      <legend>{t('kind')}</legend>
      {SCREENING_KINDS.map((key) => (
        <label key={key} className="fa-screening__check">
          <input type="radio" name="fa-screening-kind" value={key} checked={kind === key} onChange={() => onKind(key)} />{t(codeKey('kind', key))}
        </label>
      ))}
    </fieldset>
  )
}

const scoreInput = (value: string): number | null => (value === '' || !Number.isFinite(Number(value)) ? null : Number(value))

/** Neuer Prüflauf: Prüfart, Profil, Listen, Namen (je Zeile), Mindestwert, Vorgangsbezug. */
export function ScreeningRunForm({ settings, sources, busy, onSubmit }: ScreeningRunFormProps) {
  const { t } = useScreeningText()
  const { form, errors, update, setKind, toggleList, submit } = useRunForm(settings, sources, onSubmit)
  const profile = selectedProfile(settings, form)
  return (
    <section className="fa-screening__panel" aria-labelledby="fa-screening-run-form-title">
      <h3 id="fa-screening-run-form-title">{t('newRun')}</h3>
      <form noValidate onSubmit={(event) => { event.preventDefault(); submit() }}>
        <KindChoice kind={form.kind} onKind={setKind} />
        <label className="fa-screening__field">
          <span>{t('profile')}</span>
          <select value={form.profileKey} onChange={(event) => update({ profileKey: event.target.value })}>
            {kindProfiles(settings, form.kind).map((p) => (
              <option key={profileKeyOf(p)} value={profileKeyOf(p)}>{p.id} {p.version}{p.recommended ? ` ${t('recommended')}` : ''}</option>
            ))}
          </select>
        </label>
        <fieldset className="fa-screening__field">
          <legend>{t('lists')}</legend>
          {kindSources(sources, form.kind).map((s) => (
            <label key={s.list.key} className="fa-screening__check">
              <input type="checkbox" value={s.list.key} checked={form.lists.includes(s.list.key)} onChange={(event) => toggleList(s.list.key, event.target.checked)} />
              <span>
                {s.list.name}
                {s.searchable ? null : <Badge tone="danger">{t('noStockRun')}</Badge>}
              </span>
            </label>
          ))}
        </fieldset>
        <label className="fa-screening__field">
          <span>{t('subjects')}</span>
          <textarea data-testid="screening-subjects" placeholder={t('subjectsPlaceholder')} value={form.subjectsText} onChange={(event) => update({ subjectsText: event.target.value })} />
        </label>
        <label className="fa-screening__field">
          <span>{t('minScore', { min: profile?.scale.min ?? 0, max: profile?.scale.max ?? 100 })}</span>
          <input
            type="number"
            min={profile?.scale.min}
            max={profile?.scale.max}
            step={profile && profile.scale.max <= 1 ? 0.01 : 1}
            value={form.minScore ?? ''}
            onChange={(event) => update({ minScore: scoreInput(event.target.value) })}
          />
        </label>
        <label className="fa-screening__field">
          <span>{t('caseReference')}</span>
          <input type="text" maxLength={500} data-testid="screening-case" value={form.caseReference} onChange={(event) => update({ caseReference: event.target.value })} />
        </label>
        <ErrorList texts={errors.map((error) => t(error.key, error.params))} />
        <button className="fa-screening__btn fa-screening__btn--primary" type="submit" disabled={busy} data-testid="screening-start">{t('startRun')}</button>
      </form>
    </section>
  )
}
