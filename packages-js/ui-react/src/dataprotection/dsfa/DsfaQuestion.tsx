import { ANSWER_VALUES, type AnswerInput, type AnswerValue, type BadgeTone, type QuestionView } from '@flowaudit/ui-core'
import { Badge } from '../../base/Badge'
import { classes, useElementId } from '../../store'
import { prefixedLabel, useDataProtectionText } from '../shared'

export interface DsfaQuestionProps {
  question: QuestionView
  answer?: AnswerInput | null
  readonly?: boolean
  onAnswer: (value: AnswerValue) => void
  onJustify: (text: string) => void
}

const TONES: Readonly<Record<string, BadgeTone>> = { hart: 'danger', fria: 'accent' }

function Justification({ id, answer, onJustify }: { id: string; answer: AnswerInput | null; onJustify: (text: string) => void }) {
  const { t } = useDataProtectionText()
  return (
    <div className="fa-dataprotection__field">
      <label htmlFor={`${id}-why`}>{t('justification')}</label>
      <input id={`${id}-why`} type="text" value={answer?.justification ?? ''} onChange={(event) => onJustify(event.target.value)} />
    </div>
  )
}

/** Eine Frage der Schwellwertanalyse: ja/nein/unbekannt, Begründung, Erläuterung. */
export function DsfaQuestion({ question, answer = null, readonly = false, onAnswer, onJustify }: DsfaQuestionProps) {
  const { t } = useDataProtectionText()
  const id = useElementId('fa-dsfa-q')
  const value = answer?.value ?? null
  return (
    <fieldset className={classes('fa-dsfa__question', value === 'ja' && 'fa-dsfa__question--yes')} disabled={readonly} data-question={question.key}>
      <legend>{question.text}</legend>
      <div className="fa-dsfa__meta">
        <Badge tone={TONES[question.effect] ?? 'neutral'}>{prefixedLabel(t, 'effect', question.effect)}</Badge>
        <span className="fa-dataprotection__ref">{question.reference}</span>
      </div>
      <div className="fa-dataprotection__choices">
        {ANSWER_VALUES.map((option) => (
          <label key={option} className="fa-dataprotection__choice">
            <input type="radio" name={id} value={option} checked={value === option} onChange={() => onAnswer(option)} /> {prefixedLabel(t, 'answer', option)}
          </label>
        ))}
      </div>
      {value === 'ja' || value === 'unbekannt' ? <Justification id={id} answer={answer} onJustify={onJustify} /> : null}
      {question.explanation ? (
        <details>
          <summary>{t('explanation')}</summary>
          <p>{question.explanation}</p>
        </details>
      ) : null}
    </fieldset>
  )
}
