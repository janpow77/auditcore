import { Fragment } from 'react'
import {
  formatValue,
  pairs,
  parameterLabel,
  profileStatusText,
  riskMessages,
  severityTone,
  type FlagEntry,
  type JsonObject,
  type Locale,
  type ProfileReference,
} from '@auditcore/ui-core'
import { Badge } from '../base/Badge'
import { useTranslation } from '../i18n'
import { classes, useElementId } from '../store'
import { RiskFlagState } from './RiskFlagState'

export interface RiskFlagCardProps {
  entry: FlagEntry
  profile?: ProfileReference | null
  locale?: Locale
}

type Format = (value: Parameters<typeof formatValue>[0]) => string

/** Belegwerte bzw. Fundstelle als aufklappbare Liste. */
function MoreList({ title, value, format }: { title: string; value: JsonObject; format: Format }) {
  const entries = pairs(value)
  if (!entries.length) return null
  return (
    <details className="fa-risk-card__more">
      <summary>{title}</summary>
      <dl>
        {entries.map(([name, item]) => (
          <Fragment key={name}>
            <dt>{name}</dt>
            <dd>{format(item)}</dd>
          </Fragment>
        ))}
      </dl>
    </details>
  )
}

function InputTable({ entry, format, t }: { entry: FlagEntry; format: Format; t: (key: 'inputs' | 'field' | 'value') => string }) {
  const inputs = pairs(entry.inputs)
  if (!inputs.length) return null
  return (
    <table className="fa-risk-card__pairs">
      <caption>{t('inputs')}</caption>
      <thead><tr><th scope="col">{t('field')}</th><th scope="col">{t('value')}</th></tr></thead>
      <tbody>
        {inputs.map(([name, value]) => (
          <tr key={name}>
            <th scope="row"><code>{name}</code></th>
            <td className={classes((value === null || value === '') && 'fa-risk-card__empty') || undefined}>{format(value)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function ParameterTable({ entry, format, caption, locale }: { entry: FlagEntry; format: Format; caption: string; locale: Locale }) {
  const parameters = pairs(entry.parameters)
  if (!parameters.length) return null
  return (
    <table className="fa-risk-card__pairs">
      <caption>{caption}</caption>
      <tbody>
        {parameters.map(([name, value]) => (
          <tr key={name}>
            <th scope="row">{parameterLabel(name, locale)}</th>
            <td>{format(value)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

/** Treffer oder unbestimmtes Merkmal eines Datensatzes mit Begründung, Eingabewerten und Schwellen, wie `RiskFlagCard`. */
export function RiskFlagCard({ entry, profile = null, locale }: RiskFlagCardProps) {
  const { t, locale: active } = useTranslation(riskMessages, locale)
  const headingId = useElementId('fa-risk-card')
  const format: Format = (value) => formatValue(value, active, t('emptyValue'))
  return (
    <article className={`fa-risk-card fa-risk-card--${entry.state}`} aria-labelledby={headingId} data-code={entry.code}>
      <header className="fa-risk-card__head">
        <RiskFlagState state={entry.state} locale={locale} />
        <h4 id={headingId}><code>{entry.code}</code> {entry.label}</h4>
        {entry.severity ? <Badge tone={severityTone(entry.severity)}>{t('severity')}: {entry.severity}</Badge> : null}
      </header>
      {profile ? (
        <p className="fa-risk-card__profile">
          {t('profile')} <code>{profile.id}</code> · {t('version')} <code>{profile.version}</code> · {profileStatusText(profile, t)}
        </p>
      ) : null}
      <p className="fa-risk-card__reason"><strong>{t('reason')}:</strong> {entry.reason}</p>
      <div className="fa-risk-card__grid">
        <InputTable entry={entry} format={format} t={t} />
        <ParameterTable entry={entry} format={format} caption={t('parameters')} locale={active} />
      </div>
      {entry.note ? <p className="fa-risk-card__note"><strong>{t('note')}:</strong> {entry.note}</p> : null}
      <MoreList title={t('evidence')} value={entry.evidence} format={format} />
      <MoreList title={t('origin')} value={entry.origin} format={format} />
    </article>
  )
}
