/** Sections of the diagram info dialog: scope (profile, funds), header colours, legal bases and lists. */

import type { Dispatch, SetStateAction } from 'react'
import { FUNDS, FUND_SHORT, label, type DiagramInfo, type LegalBasis, type ProfileSummary } from '@auditcore/bpmn-flowaudit'
import { DIAGRAM_LISTS, infoList, LISTS, toggleFund, type FieldDescriptor, type Option } from '@auditcore/bpmn-flowaudit/ui'
import { useEditorContext } from '../context'
import { useI18n } from '../i18n'
import { LegalBasisEditor } from '../panels/legal/LegalBasisEditor'
import { ListEditor } from '../panels/ListEditor'

interface DraftProps {
  draft: DiagramInfo
  setDraft: Dispatch<SetStateAction<DiagramInfo>>
}

export function ScopeFields({ draft, setDraft, profiles }: DraftProps & { profiles: ProfileSummary[] }) {
  const { t, locale } = useI18n()
  const readonly = useEditorContext().readonly()
  return (
    <>
      <label className="fa-field fa-section">
        <span className="fa-label">{t('info.field.profile')}</span>
        <select className="fa-select" value={draft.profile ?? ''} disabled={readonly} onChange={(event) => setDraft({ ...draft, profile: event.target.value || undefined })}>
          <option value="">{t('common.none')}</option>
          {profiles.map((entry) => <option key={entry.id} value={entry.id}>{entry.title} ({entry.version})</option>)}
        </select>
      </label>
      <fieldset className="fa-info-funds">
        <legend className="fa-label">{t('info.field.funds')}</legend>
        {Object.entries(FUNDS).map(([code, text]) => (
          <button key={code} type="button" className="fa-chip" title={label(text, locale)} aria-pressed={(draft.funds ?? []).includes(code)} disabled={readonly} onClick={() => setDraft(toggleFund(draft, code))}>
            {FUND_SHORT[code] ?? code}
          </button>
        ))}
      </fieldset>
    </>
  )
}

export function HeaderSection({ draft, setDraft, header }: DraftProps & { header: { color: string; textColor: string } }) {
  const { t } = useI18n()
  const readonly = useEditorContext().readonly()
  return (
    <section className="fa-info-section">
      <h3 className="fa-section__title">{t('info.section.header')}</h3>
      <div className="fa-grid-2">
        <label className="fa-field"><span className="fa-label">{t('info.field.headerColor')}</span><input type="color" className="fa-input" value={header.color} disabled={readonly} onChange={(event) => setDraft({ ...draft, headerColor: event.target.value })} /></label>
        <label className="fa-field"><span className="fa-label">{t('info.field.headerTextColor')}</span><input type="color" className="fa-input" value={header.textColor} disabled={readonly} onChange={(event) => setDraft({ ...draft, headerTextColor: event.target.value })} /></label>
      </div>
    </section>
  )
}

export function LegalSection({ draft, setDraft, optionsFor }: DraftProps & { optionsFor: (field: FieldDescriptor) => Option[] }) {
  const { t } = useI18n()
  const { ports, profile, readonly } = useEditorContext()
  return (
    <section className="fa-info-section">
      <h3 className="fa-section__title">{t('info.section.legal')}</h3>
      <LegalBasisEditor items={draft.legalBases ?? []} port={ports.legalSearch} profileId={profile()?.id} disabled={readonly()} onUpdate={(items: LegalBasis[]) => setDraft({ ...draft, legalBases: items })} />
      {DIAGRAM_LISTS.map((key) => (
        <ListEditor key={key} className="fa-section" descriptor={LISTS[key]} items={infoList(draft, key)} optionsFor={optionsFor} disabled={readonly()} onUpdate={(items: Record<string, unknown>[]) => setDraft({ ...draft, [key]: items })} />
      ))}
    </section>
  )
}
