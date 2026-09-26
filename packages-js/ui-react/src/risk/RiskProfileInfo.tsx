import type { ReactNode } from 'react'
import type { TableColumn, TableRow } from '@flowaudit/common'
import {
  formatValue,
  pairs,
  parameterLabel,
  profileHintText,
  profileStatusText,
  requirementKey,
  riskMessages,
  whenMissingKey,
  type FieldEntry,
  type Locale,
  type ProfileDetail,
  type RiskTranslate,
  type RuleView,
} from '@flowaudit/ui-core'
import { Badge } from '../base/Badge'
import { useTranslation } from '../i18n'
import { FlowauditTable } from '../table/FlowauditTable'
import { displayValue } from './display'

export interface RiskProfileInfoProps {
  profile?: ProfileDetail | null
  locale?: Locale
}

function ruleColumns(t: RiskTranslate): TableColumn[] {
  return [
    { key: 'code', label: t('colCode') },
    { key: 'label', label: t('colLabel') },
    { key: 'inputs', label: t('inputs') },
    { key: 'parameters', label: t('parameters') },
    { key: 'when_missing_columns', label: t('colWhenMissing'), format: (value) => t(whenMissingKey(String(value))) },
  ]
}

function fieldColumns(t: RiskTranslate): TableColumn[] {
  return [
    { key: 'name', label: t('field'), sortable: true },
    { key: 'meaning', label: t('colMeaning') },
    { key: 'requirement', label: t('colRequirement'), sortable: true },
    { key: 'uses', label: t('colMissing') },
  ]
}

function ruleCell(column: TableColumn, row: TableRow, t: RiskTranslate, active: Locale): ReactNode {
  const rule = row as unknown as RuleView
  if (column.key === 'code') return <code>{rule.code}</code>
  if (column.key === 'inputs') return <span>{rule.inputs.map((name) => <code key={name} className="fa-risk-profile__chip">{name}</code>)}</span>
  if (column.key !== 'parameters') return undefined
  return (
    <span>
      {pairs(rule.parameters).map(([name, value]) => (
        <span key={name} className="fa-risk-profile__param">{parameterLabel(name, active)}: {formatValue(value, active, t('emptyValue'))}</span>
      ))}
    </span>
  )
}

function fieldCell(column: TableColumn, row: TableRow, t: RiskTranslate): ReactNode {
  const field = row as unknown as FieldEntry
  if (column.key === 'name') return <code>{field.name}</code>
  if (column.key === 'meaning') return field.meaning ?? t('undocumented')
  if (column.key === 'requirement') return <Badge tone={field.requirement === 'optional' ? 'neutral' : 'accent'}>{t(requirementKey(field.requirement))}</Badge>
  if (column.key !== 'uses') return undefined
  return (
    <span>
      {field.uses.map((use) => (
        <span key={use.code} className="fa-risk-profile__use"><code>{use.code}</code> ({use.role}): {use.absent} / {use.empty}</span>
      ))}
    </span>
  )
}

function Identity({ profile, t, status, hint }: { profile: ProfileDetail; t: RiskTranslate; status: string; hint: string }) {
  const source = profile.source
  return (
    <dl className="fa-risk-profile__identity">
      <dt>{t('profile')}</dt><dd><code>{profile.id}</code></dd>
      <dt>{t('version')}</dt><dd><code>{profile.version}</code></dd>
      <dt>{t('status')}</dt><dd><Badge tone={hint ? 'warning' : 'success'}>{status}</Badge></dd>
      <dt>{t('fingerprint')}</dt><dd><code className="fa-risk-profile__hash">{profile.fingerprint}</code></dd>
      {source.repository ? <dt>{t('source')}</dt> : null}
      {source.repository ? <dd>{displayValue(source.repository)} · {displayValue(source.path)} · {displayValue(source.commit)}</dd> : null}
    </dl>
  )
}

/** Profil, Regeln und Eingabefelder (Pflicht/optional, Folge bei Fehlen), wie `RiskProfileInfo`. */
export function RiskProfileInfo({ profile = null, locale }: RiskProfileInfoProps) {
  const { t, locale: active } = useTranslation(riskMessages, locale)
  if (!profile) return null
  const hint = profileHintText(profile, t)
  return (
    <section className="fa-risk-profile" aria-label={t('profileInfo')}>
      <Identity profile={profile} t={t} status={profileStatusText(profile, t)} hint={hint} />
      {hint ? <p className="fa-risk-profile__hint" role="note">{hint}</p> : null}
      <p className="fa-risk-profile__legal">{profile.legal_status}</p>
      {profile.open_decisions.length ? (
        <div>
          <h4>{t('openDecisions')}</h4>
          <ul>{profile.open_decisions.map((decision) => <li key={decision}>{decision}</li>)}</ul>
        </div>
      ) : null}
      <FlowauditTable columns={ruleColumns(t)} rows={profile.rules.map((rule) => ({ ...rule, id: rule.code }))} rowKey="code" caption={t('rulesTitle')} locale={locale} renderCell={(column, row) => ruleCell(column, row, t, active)} />
      <FlowauditTable columns={fieldColumns(t)} rows={profile.fields.map((field) => ({ ...field, id: field.name }))} rowKey="name" caption={t('fieldsTitle')} locale={locale} renderCell={(column, row) => fieldCell(column, row, t)} />
    </section>
  )
}
