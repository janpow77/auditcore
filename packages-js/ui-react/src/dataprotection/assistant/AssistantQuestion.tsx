import {
  needsJustification,
  questionFieldId,
  questionOptions,
  type AssistantQuestion as Question,
  type Draft,
} from '@auditcore/ui-core'
import { useDataProtectionText } from '../shared'
import { AssistantTable } from './AssistantTable'

export interface AssistantQuestionProps {
  question: Question
  draft: Draft
  error?: string
  busy: boolean
  onChange: (draft: Draft) => void
  onSave: () => void
  onConfirm: () => void
}

function Help({ question, id }: { question: Question; id: string }) {
  const { t } = useDataProtectionText()
  if (!question.hints.length && !question.reference) return null
  return (
    <details id={`${id}-help`} className="fa-assistant__hints">
      <summary>{t('whyAsked')}</summary>
      <ul>
        {question.reference ? <li>{t('reference', { reference: question.reference })}</li> : null}
        {question.hints.map((hint, index) => <li key={index}>{hint}</li>)}
      </ul>
    </details>
  )
}

function Input({ question, draft, id, onChange }: { question: Question; draft: Draft; id: string; onChange: (draft: Draft) => void }) {
  const { t } = useDataProtectionText()
  const options = question.kind === 'text' ? [] : questionOptions(t, question)
  if (question.kind === 'zahl' && !options.length) {
    return <input id={id} type="number" min="0" step="1" inputMode="numeric" value={draft.value} aria-label={`${question.text} ${t('numberInput')}`} onChange={(event) => onChange({ ...draft, value: event.target.value })} />
  }
  if (question.kind === 'tabelle' && !options.length) {
    return <AssistantTable question={question} value={draft.value} onChange={(value) => onChange({ ...draft, value })} />
  }
  if (!options.length) {
    return <textarea id={id} value={draft.value} rows={3} aria-label={question.text} onChange={(event) => onChange({ ...draft, value: event.target.value })} />
  }
  return (
    <div className="fa-assistant__choices" role="radiogroup" aria-label={question.text}>
      {options.map((option) => (
        <label key={option.key}>
          <input id={`${id}-${option.key}`} type="radio" name={id} value={option.key} checked={draft.value === option.key} onChange={() => onChange({ ...draft, value: option.key })} />{' '}
          {option.title}
        </label>
      ))}
    </div>
  )
}

function Suggestion({ question, busy, onConfirm }: { question: Question; busy: boolean; onConfirm: () => void }) {
  const { t } = useDataProtectionText()
  if (question.answer === null || question.answer.origin === 'bestaetigt') return null
  return (
    <p className="fa-dataprotection__alert fa-dataprotection__alert--warning">
      {t('suggestion', { origin: question.answer.origin })}{' '}
      <button type="button" disabled={busy} onClick={onConfirm}>{t('confirmSuggestion')}</button>
    </p>
  )
}

function Reason({ draft, onChange }: { draft: Draft; onChange: (draft: Draft) => void }) {
  const { t } = useDataProtectionText()
  return (
    <label>
      {t('answerJustification')}{' '}
      <textarea value={draft.justification} rows={2} onChange={(event) => onChange({ ...draft, justification: event.target.value })} />
    </label>
  )
}

export function AssistantQuestion({ question, draft, error, busy, onChange, onSave, onConfirm }: AssistantQuestionProps) {
  const { t } = useDataProtectionText()
  const id = questionFieldId(question)
  const showReason = needsJustification(question, draft.value) || draft.justification !== ''
  return (
    <fieldset className={['fa-assistant__question', question.depth ? `fa-assistant__question--depth-${Math.min(question.depth, 2)}` : ''].filter(Boolean).join(' ')} data-question={question.id} aria-describedby={`${id}-help`} aria-invalid={error ? 'true' : undefined}>
      <legend>
        <span className="fa-assistant__number">{question.number}</span> {question.text} <span className="fa-assistant__badge">{question.required ? t('requiredQuestion') : t('optionalQuestion')}</span>
      </legend>
      <Help question={question} id={id} />
      <Suggestion question={question} busy={busy} onConfirm={onConfirm} />
      <Input question={question} draft={draft} id={id} onChange={onChange} />
      {showReason ? <Reason draft={draft} onChange={onChange} /> : null}
      {error ? <p id={`${id}-error`} className="fa-dataprotection__alert" role="alert">{error}</p> : null}
      <button type="button" disabled={busy || draft.value === ''} onClick={onSave}>{t('saveAnswer')}</button>
    </fieldset>
  )
}
