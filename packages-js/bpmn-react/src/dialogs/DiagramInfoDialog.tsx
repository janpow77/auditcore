/**
 * Diagram info: all info fields incl. profile, funds, programming period,
 * status, validity, approval with hash, confidentiality and header colours.
 * Edits a copy; „apply“ writes one undo step.
 */

import { useEffect, useState } from 'react'
import { headerOf, type Approval, type DiagramInfo, type ProfileSummary } from '@flowaudit/bpmn-flowaudit'
import { cloneInfo, INFO_SECTIONS } from '@flowaudit/bpmn-flowaudit/ui'
import { BaseDialog } from '../base/BaseDialog'
import { FaIcon } from '../base/FaIcon'
import { useEditorContext } from '../context'
import { useI18n } from '../i18n'
import { FieldForm } from '../panels/FieldForm'
import { useOptions } from '../panels/useOptions'
import { HeaderSection, LegalSection, ScopeFields } from './infoSections'

export interface DiagramInfoDialogProps {
  open: boolean
  info: DiagramInfo | null
  profiles: ProfileSummary[]
  approvals?: Approval[]
  fallbackTitle: string
  onOpenChange: (open: boolean) => void
  onApply?: (info: DiagramInfo) => void
  onApprove?: (info: DiagramInfo) => void
  onNewVersion?: (info: DiagramInfo) => void
}

function ApprovalSection({ draft, approvals, onApprove, onNewVersion }: Pick<DiagramInfoDialogProps, 'approvals' | 'onApprove' | 'onNewVersion'> & { draft: DiagramInfo }) {
  const { t } = useI18n()
  const readonly = useEditorContext().readonly()
  const last = approvals?.[approvals.length - 1]
  return (
    <section className="fa-info-section">
      <h3 className="fa-section__title">{t('info.approval')}</h3>
      <p className="fa-help">{t('info.approveHelp')}</p>
      {last ? <p className="fa-info-hash"><FaIcon name="hash" size={14} />{t('info.approvedHash')} ({last.version}): <code>{last.sha256}</code></p> : null}
      <div className="fa-info-actions">
        <button type="button" className="fa-btn" disabled={readonly} onClick={() => onApprove?.(draft)}><FaIcon name="lock" size={16} />{t('info.approve')}</button>
        <button type="button" className="fa-btn" onClick={() => onNewVersion?.(draft)}><FaIcon name="new" size={16} />{t('info.newVersion')}</button>
      </div>
    </section>
  )
}

export function DiagramInfoDialog(props: DiagramInfoDialogProps) {
  const { open, info, profiles, fallbackTitle, onOpenChange, onApply } = props
  const { t } = useI18n()
  const readonly = useEditorContext().readonly()
  const optionsFor = useOptions()
  const [draft, setDraft] = useState<DiagramInfo>(() => cloneInfo(info))

  useEffect(() => {
    if (open) setDraft(cloneInfo(info))
  }, [open, info])

  const header = headerOf(draft, fallbackTitle)
  const apply = () => {
    onApply?.(draft)
    onOpenChange(false)
  }
  const footer = (
    <>
      <button type="button" className="fa-btn" onClick={() => onOpenChange(false)}>{t('common.cancel')}</button>
      <button type="button" className="fa-btn fa-btn--primary" disabled={readonly} onClick={apply}>{t('common.apply')}</button>
    </>
  )

  return (
    <BaseDialog open={open} title={t('info.title')} width="860px" onOpenChange={onOpenChange} footer={footer}>
      <div className="fa-info-preview" style={{ background: header.color, color: header.textColor }} aria-label={t('info.preview')}>
        <strong>{header.title}</strong><span>{header.subtitle}</span>
      </div>
      {INFO_SECTIONS.map((section) => (
        <section key={section.id} className="fa-info-section">
          <h3 className="fa-section__title">{t(section.title)}</h3>
          <FieldForm value={draft as Record<string, unknown>} fields={section.fields} optionsFor={optionsFor} disabled={readonly && section.id !== 'status'} onUpdate={(value) => setDraft({ ...(value as DiagramInfo) })} />
          {section.id === 'scope' ? <ScopeFields draft={draft} profiles={profiles} setDraft={setDraft} /> : null}
        </section>
      ))}
      <HeaderSection draft={draft} header={header} setDraft={setDraft} />
      <LegalSection draft={draft} setDraft={setDraft} optionsFor={optionsFor} />
      <ApprovalSection draft={draft} approvals={props.approvals} onApprove={props.onApprove} onNewVersion={props.onNewVersion} />
    </BaseDialog>
  )
}
