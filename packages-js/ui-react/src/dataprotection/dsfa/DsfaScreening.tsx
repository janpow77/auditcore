import { blockProgress, screeningTone, withAnswer, withJustification, type BlockView, type DataProtectionProfile, type Proposal, type SurveyInput } from '@flowaudit/ui-core'
import { Badge } from '../../base/Badge'
import { prefixedLabel, useDataProtectionText } from '../shared'
import { DsfaQuestion } from './DsfaQuestion'

export interface DsfaSurveyProps {
  profile: DataProtectionProfile
  survey: SurveyInput
  proposal?: Proposal | null
  preview?: boolean
  readonly?: boolean
  onSurveyChange: (survey: SurveyInput) => void
}

function Result({ screening, preview }: { screening: Proposal['screening']; preview: boolean }) {
  const { t } = useDataProtectionText()
  const open = screening.unanswered.length + screening.unknown.length
  const summary = [
    t('hardTriggers', { count: screening.hard_triggers.length }),
    t('points', { points: screening.points, threshold: screening.points_threshold }),
    t('openAnswers', { count: open }),
  ].join(' · ')
  return (
    <section className="fa-dataprotection__panel" aria-label={t('screeningResult')}>
      <div className="fa-dataprotection__bar">
        <h3>{t('screeningResult')}</h3>
        <Badge tone={screeningTone(screening.outcome)}>{prefixedLabel(t, 'outcome', screening.outcome)}</Badge>
        {preview ? <Badge tone="accent">{t('preview')}</Badge> : null}
      </div>
      <p aria-live="polite">{screening.reasoning}</p>
      <p className="fa-dataprotection__muted">{summary}</p>
    </section>
  )
}

function Block({ block, props }: { block: BlockView; props: DsfaSurveyProps }) {
  const { t } = useDataProtectionText()
  const { survey, onSurveyChange } = props
  return (
    <section className="fa-dataprotection__panel" aria-label={block.title}>
      <div className="fa-dataprotection__bar">
        <h3>{block.title}</h3>
        <span className="fa-dataprotection__muted">{t('progress', { ...blockProgress(block, survey) })}</span>
      </div>
      {block.questions.map((question) => (
        <DsfaQuestion
          key={question.key}
          question={question}
          answer={survey.answers[question.key] ?? null}
          readonly={props.readonly}
          onAnswer={(value) => onSurveyChange(withAnswer(survey, question.key, value))}
          onJustify={(text) => onSurveyChange(withJustification(survey, question.key, text))}
        />
      ))}
    </section>
  )
}

/** Schwellwertanalyse: Ergebnis der Bibliothek und Fragen je Block. */
export function DsfaScreening(props: DsfaSurveyProps) {
  const screening = props.proposal?.screening ?? null
  return (
    <div data-testid="dsfa-screening">
      {screening ? <Result screening={screening} preview={!!props.preview} /> : null}
      {props.profile.screening.blocks.map((block) => <Block key={block.key} block={block} props={props} />)}
    </div>
  )
}
