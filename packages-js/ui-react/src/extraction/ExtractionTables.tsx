import {
  extractionConfidenceText,
  extractionConfidenceTone,
  extractionDecisionText,
  extractionDecisionTone,
  extractionFieldLabel,
  extractionOutcomeTone,
  extractionProposalText,
  extractionRuleLabel,
  extractionValueText,
  splitExtractionFindings,
  type ExtractedField,
  type ExtractionFinding,
  type ExtractionTranslate,
  type Locale,
} from '@auditcore/ui-core'
import { Badge } from '../base/Badge'

interface FieldsProps {
  fields: readonly ExtractedField[]
  threshold: number | null
  t: ExtractionTranslate
  locale: Locale
}

function FieldRow({ field, threshold, t, locale }: Omit<FieldsProps, 'fields'> & { field: ExtractedField }) {
  const proposal = extractionProposalText(field, t, locale)
  return (
    <tr data-field={field.name}>
      <th scope="row">{extractionFieldLabel(field.name, t)}</th>
      <td>{extractionValueText(field.value, locale) || t('noValue')}</td>
      <td className="fa-extraction__number">
        {field.confidence !== null
          ? <Badge tone={extractionConfidenceTone(field.confidence, threshold)}>{extractionConfidenceText(field.confidence, locale)}</Badge>
          : t('noValue')}
      </td>
      <td>
        {field.decision ? <Badge tone={extractionDecisionTone(field)}>{extractionDecisionText(field, t)}</Badge> : t('noValue')}
        {proposal ? <div className="fa-extraction__muted">{proposal}</div> : null}
      </td>
    </tr>
  )
}

/** Erkannte Felder mit Wert, Konfidenz (nur Donut) und Übernahmeentscheidung. */
export function ExtractionFields(props: FieldsProps) {
  const { fields, t } = props
  return (
    <>
      <h4 className="fa-extraction__heading">{t('fields')}</h4>
      <p className="fa-extraction__muted">{t('confidenceHelp')}</p>
      {!fields.length ? <p className="fa-extraction__muted">{t('noFields')}</p> : (
        <div className="fa-extraction__scroll">
          <table className="fa-extraction__table" data-testid="extraction-fields">
            <thead>
              <tr>
                <th scope="col">{t('colField')}</th>
                <th scope="col">{t('colValue')}</th>
                <th scope="col">{t('colConfidence')}</th>
                <th scope="col">{t('colDecision')}</th>
              </tr>
            </thead>
            <tbody>
              {fields.map((field) => <FieldRow key={field.name} field={field} threshold={props.threshold} t={t} locale={props.locale} />)}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}

function OpenFindings({ findings, t }: { findings: readonly ExtractionFinding[]; t: ExtractionTranslate }) {
  if (!findings.length) return <p className="fa-extraction__muted">{t('findingsNone')}</p>
  return (
    <div className="fa-extraction__scroll">
      <table className="fa-extraction__table" data-testid="extraction-findings">
        <thead>
          <tr>
            <th scope="col">{t('colRule')}</th>
            <th scope="col">{t('colSeverity')}</th>
            <th scope="col">{t('colOutcome')}</th>
            <th scope="col">{t('colMessage')}</th>
          </tr>
        </thead>
        <tbody>
          {findings.map((finding) => (
            <tr key={finding.rule_id} data-rule={finding.rule_id}>
              <th scope="row">{extractionRuleLabel(finding, t)}</th>
              <td>{t(`severity${finding.severity}`)}</td>
              <td><Badge tone={extractionOutcomeTone(finding)}>{t(`outcome${finding.outcome}`)}</Badge></td>
              <td>{finding.message}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/** Validierungsbefunde: auffällige als Tabelle, bestandene aufklappbar, Kennzeichen. */
export function ExtractionFindings({ findings, flags, t }: { findings: readonly ExtractionFinding[]; flags: readonly string[]; t: ExtractionTranslate }) {
  const split = splitExtractionFindings(findings)
  return (
    <>
      <h4 className="fa-extraction__heading">{t('findings')}</h4>
      <OpenFindings findings={split.open} t={t} />
      {split.passed.length ? (
        <details className="fa-extraction__passed">
          <summary>{t('passed', { count: split.passed.length })}</summary>
          <ul>
            {split.passed.map((finding) => <li key={finding.rule_id}>{`${extractionRuleLabel(finding, t)}: ${finding.message}`}</li>)}
          </ul>
        </details>
      ) : null}
      {flags.length ? (
        <>
          <h4 className="fa-extraction__label">{t('flags')}</h4>
          <ul className="fa-extraction__flags" data-testid="extraction-flags">
            {flags.map((flag) => <li key={flag}><Badge>{flag}</Badge></li>)}
          </ul>
        </>
      ) : null}
    </>
  )
}
