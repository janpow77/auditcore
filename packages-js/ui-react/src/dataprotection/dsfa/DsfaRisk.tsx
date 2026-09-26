import { addScenario, bandTone, removeScenario, withScenario, type DossierFieldView, type SurveyInput } from '@flowaudit/ui-core'
import { Badge } from '../../base/Badge'
import { Button } from '../../base/Button'
import { classes, useElementId } from '../../store'
import { useDataProtectionText } from '../shared'
import type { DsfaSurveyProps } from './DsfaScreening'
import { DsfaScenario } from './DsfaScenario'

function Scenarios(props: DsfaSurveyProps) {
  const { t } = useDataProtectionText()
  const { profile, survey, onSurveyChange } = props
  const risk = props.proposal?.risk ?? null
  return (
    <section className="fa-dataprotection__panel" aria-label={t('scenarios')}>
      <div className="fa-dataprotection__bar">
        <h3>{t('scenarios')}</h3>
        {risk && risk.scenarios.length ? (
          <>
            <Badge tone={bandTone(risk.net_band, profile.risk.bands)}>{risk.net_band}</Badge>
            <span aria-live="polite">{t('riskSummary', { gross: risk.gross_maximum, net: risk.net_maximum, band: risk.net_band })}</span>
          </>
        ) : null}
        {props.preview ? <Badge tone="accent">{t('preview')}</Badge> : null}
      </div>
      {survey.scenarios.length ? null : <p className="fa-dataprotection__muted">{t('noScenarios')}</p>}
      {survey.scenarios.map((scenario, index) => (
        <DsfaScenario
          key={index}
          profile={profile}
          scenario={scenario}
          index={index}
          result={risk?.scenarios[index] ?? null}
          readonly={props.readonly}
          onScenarioChange={(next) => onSurveyChange(withScenario(survey, index, next))}
          onRemove={() => onSurveyChange(removeScenario(survey, index))}
        />
      ))}
      {props.readonly ? null : <Button icon="plus" label={t('addScenario')} onClick={() => onSurveyChange(addScenario(survey, profile))} />}
    </section>
  )
}

function Necessity({ id, props }: { id: string; props: DsfaSurveyProps }) {
  const { t } = useDataProtectionText()
  const texts = [
    { key: 'necessity' as const, label: t('necessity') },
    { key: 'proportionality' as const, label: t('proportionality') },
  ]
  return (
    <section className="fa-dataprotection__panel" aria-label={t('necessityTitle')}>
      <h3>{t('necessityTitle')}</h3>
      {texts.map((entry) => (
        <div key={entry.key} className="fa-dataprotection__field">
          <label htmlFor={`${id}-${entry.key}`}>{entry.label}</label>
          <textarea id={`${id}-${entry.key}`} rows={3} readOnly={!!props.readonly} value={props.survey[entry.key]} onChange={(event) => props.onSurveyChange({ ...props.survey, [entry.key]: event.target.value })} />
        </div>
      ))}
    </section>
  )
}

function DossierField({ id, field, props }: { id: string; field: DossierFieldView; props: DsfaSurveyProps }) {
  const { t } = useDataProtectionText()
  const value = props.survey.dossier?.[field.key] ?? ''
  const set = (text: string): void => {
    const survey: SurveyInput = props.survey
    props.onSurveyChange({ ...survey, dossier: { ...(survey.dossier ?? {}), [field.key]: text } })
  }
  const fieldId = `${id}-d-${field.key}`
  return (
    <div className={classes('fa-dataprotection__field', field.required && 'fa-dataprotection__field--required')}>
      <label htmlFor={fieldId}>{field.title}</label>
      {field.kind === 'choice' ? (
        <select id={fieldId} disabled={!!props.readonly} value={value} onChange={(event) => set(event.target.value)}>
          <option value="">{t('empty')}</option>
          {field.choices.map((choice) => <option key={choice.key} value={choice.key}>{choice.title}</option>)}
        </select>
      ) : (
        <input id={fieldId} type={field.kind === 'date' ? 'date' : 'text'} readOnly={!!props.readonly} value={value} onChange={(event) => set(event.target.value)} />
      )}
    </div>
  )
}

function Dossier({ id, props }: { id: string; props: DsfaSurveyProps }) {
  const { t } = useDataProtectionText()
  if (!props.profile.dossier_fields.length) return null
  return (
    <section className="fa-dataprotection__panel" aria-label={t('dossierTitle')}>
      <h3>{t('dossierTitle')}</h3>
      <div className="fa-dataprotection__grid">
        {props.profile.dossier_fields.map((field) => <DossierField key={field.key} id={id} field={field} props={props} />)}
      </div>
    </section>
  )
}

/** Risikobetrachtung: Szenarien, Notwendigkeit und Verhältnismäßigkeit, Stammdaten (Schema 2). */
export function DsfaRisk(props: DsfaSurveyProps) {
  const id = useElementId('fa-dsfa-risk')
  return (
    <div data-testid="dsfa-risk">
      <Scenarios {...props} />
      <Necessity id={id} props={props} />
      <Dossier id={id} props={props} />
    </div>
  )
}
