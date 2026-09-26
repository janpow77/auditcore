import { useState } from 'react'
import {
  canReleaseAssessment,
  decisionForm,
  decisionTitle,
  isDeviation,
  parseConditions,
  type AssessmentView,
  type DataProtectionProfile,
  type DecisionForm,
  type DecisionInput,
  type Proposal,
} from '@flowaudit/ui-core'
import { Button } from '../../base/Button'
import { classes, useElementId } from '../../store'
import { useDataProtectionText } from '../shared'

export interface DsfaDecisionProps {
  profile: DataProtectionProfile
  view: AssessmentView
  proposal: Proposal
  dirty?: boolean
  actor?: string
  busy?: string | null
  onDecide: (decision: DecisionInput) => void
  onDpoRequest: (from: string, on: string) => void
  onRelease: () => void
}

type Section = { id: string; props: DsfaDecisionProps }

function DecisionFields({ id, props, form, setForm }: Section & { form: DecisionForm; setForm: (form: DecisionForm) => void }) {
  const { t } = useDataProtectionText()
  const deviation = isDeviation(props.proposal, form.decision)
  const submit = (): void => props.onDecide({ decision: form.decision, justification: form.justification, conditions: parseConditions(form.conditions) })
  return (
    <>
      <div className="fa-dataprotection__field">
        <label htmlFor={`${id}-select`}>{t('decision')}</label>
        <select id={`${id}-select`} value={form.decision} onChange={(event) => setForm({ ...form, decision: event.target.value })}>
          <option value="" disabled>{t('chooseDecision')}</option>
          {props.profile.decisions.map((entry) => <option key={entry.key} value={entry.key}>{entry.title}</option>)}
        </select>
      </div>
      {deviation ? <p className="fa-dataprotection__note fa-dataprotection__note--blocking" role="status">{t('deviationHint')}</p> : null}
      <div className={classes('fa-dataprotection__field', deviation && 'fa-dataprotection__field--required')}>
        <label htmlFor={`${id}-why`}>{t('decisionJustification')}</label>
        <textarea id={`${id}-why`} rows={3} aria-required={deviation} value={form.justification} onChange={(event) => setForm({ ...form, justification: event.target.value })} />
      </div>
      {form.decision === 'freigabe_mit_auflagen' ? (
        <div className="fa-dataprotection__field fa-dataprotection__field--required">
          <label htmlFor={`${id}-cond`}>{t('conditions')}</label>
          <textarea id={`${id}-cond`} rows={3} value={form.conditions} onChange={(event) => setForm({ ...form, conditions: event.target.value })} />
        </div>
      ) : null}
      <Button variant="primary" disabled={!form.decision || !!props.dirty} loading={props.busy === 'decided'} label={t('decide')} onClick={submit} />
    </>
  )
}

function Decision({ id, props }: Section) {
  const { t, when } = useDataProtectionText()
  const { view, proposal } = props
  const [form, setForm] = useState<DecisionForm>(() => decisionForm(view, proposal))
  const [source, setSource] = useState(view)
  // Wie der Vue-watch auf `view`: nur eine neue Fassung belegt die Felder neu, eine neue Vorschau nicht.
  if (source !== view) {
    setSource(view)
    setForm(decisionForm(view, proposal))
  }
  return (
    <section className="fa-dataprotection__panel" aria-labelledby={`${id}-title`}>
      <h3 id={`${id}-title`}>{t('decisionTitle')}</h3>
      {view.decided_by ? (
        <p className="fa-dataprotection__muted">{t('decidedBy', { person: view.decided_by, date: when(view.decided_at), decision: decisionTitle(props.profile, view.decision) })}</p>
      ) : null}
      {props.dirty ? <p className="fa-dataprotection__alert fa-dataprotection__alert--warning">{t('saveFirst')}</p> : null}
      {view.locked ? null : <DecisionFields id={id} props={props} form={form} setForm={setForm} />}
    </section>
  )
}

function Dpo({ id, props }: Section) {
  const { t, when } = useDataProtectionText()
  const { view } = props
  const [from, setFrom] = useState('')
  const [on, setOn] = useState('')
  if (props.profile.profile.release_mode !== 'dokumentation') return null
  return (
    <section className="fa-dataprotection__panel" aria-labelledby={`${id}-dpo`}>
      <h3 id={`${id}-dpo`}>{t('dpoTitle')}</h3>
      {view.dpo_requested_from ? (
        <p className="fa-dataprotection__muted">{t('dpoRecorded', { person: view.dpo_requested_from, date: when(view.dpo_requested_on, false) })}</p>
      ) : null}
      {view.locked ? null : (
        <>
          <div className="fa-dataprotection__grid">
            <div className="fa-dataprotection__field">
              <label htmlFor={`${id}-from`}>{t('dpoFrom')}</label>
              <input id={`${id}-from`} type="text" value={from} onChange={(event) => setFrom(event.target.value)} />
            </div>
            <div className="fa-dataprotection__field">
              <label htmlFor={`${id}-on`}>{t('dpoOn')}</label>
              <input id={`${id}-on`} type="date" value={on} onChange={(event) => setOn(event.target.value)} />
            </div>
          </div>
          <Button disabled={!from.trim() || !on || !!props.dirty} loading={props.busy === 'dpo'} label={t('dpoRecord')} onClick={() => props.onDpoRequest(from.trim(), on)} />
        </>
      )}
    </section>
  )
}

function Released({ view }: { view: AssessmentView }) {
  const { t, when } = useDataProtectionText()
  return (
    <>
      <p>{t('releasedBy', { person: view.released_by ?? '', date: when(view.released_at) })}</p>
      {view.release_open_points.length ? <h4>{t('releaseOpenPoints')}</h4> : null}
      <ul className="fa-dataprotection__issues">
        {view.release_open_points.map((point) => <li key={point}>{point}</li>)}
      </ul>
    </>
  )
}

function Open({ props }: { props: DsfaDecisionProps }) {
  const { t } = useDataProtectionText()
  const { view, actor = '' } = props
  const info = view.open_points.length ? <p className="fa-dataprotection__muted">{t('releaseInfo')}</p> : null
  return (
    <>
      {view.release_blockers.length ? (
        <p className="fa-dataprotection__alert fa-dataprotection__alert--warning">{`${t('releaseBlockers')} ${view.release_blockers[0]}`}</p>
      ) : info}
      {actor && view.editors.includes(actor) ? <p className="fa-dataprotection__muted" data-testid="dsfa-four-eyes">{t('fourEyesHint')}</p> : null}
      <Button icon="lock" disabled={!canReleaseAssessment(view, actor, !!props.dirty)} loading={props.busy === 'released'} label={t('release')} onClick={props.onRelease} />
    </>
  )
}

/** Entscheidung, DSB-Stellungnahme (Dokumentationsmodus) und Freigabe nach dem Vier-Augen-Prinzip. */
export function DsfaDecision(props: DsfaDecisionProps) {
  const { t } = useDataProtectionText()
  const id = useElementId('fa-dsfa-decision')
  return (
    <div data-testid="dsfa-decision">
      <Decision id={id} props={props} />
      <Dpo id={id} props={props} />
      <section className="fa-dataprotection__panel" aria-labelledby={`${id}-release`}>
        <h3 id={`${id}-release`}>{t('releaseTitle')}</h3>
        {props.view.locked ? <Released view={props.view} /> : <Open props={props} />}
      </section>
    </div>
  )
}
