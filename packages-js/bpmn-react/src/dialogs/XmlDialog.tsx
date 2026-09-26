/**
 * XML view (legacy XML mode). A plain text area with „apply“; an
 * application can render its own XML editor with `renderEditor`.
 */

import { useEffect, useState, type ReactNode } from 'react'
import { BaseDialog } from '../base/BaseDialog'
import { useI18n } from '../i18n'

export interface XmlDialogProps {
  open: boolean
  xml: string
  readonly?: boolean
  onOpenChange: (open: boolean) => void
  onApply: (xml: string) => void
  /** Vue slot `editor`: own editor for the draft. */
  renderEditor?: (xml: string, update: (value: string) => void) => ReactNode
}

export function XmlDialog({ open, xml, readonly, onOpenChange, onApply, renderEditor }: XmlDialogProps) {
  const { t } = useI18n()
  const [draft, setDraft] = useState(xml)

  useEffect(() => {
    if (open) setDraft(xml)
  }, [open, xml])

  const apply = () => {
    onApply(draft)
    onOpenChange(false)
  }

  const footer = (
    <>
      <button type="button" className="fa-btn" onClick={() => onOpenChange(false)}>{t('common.cancel')}</button>
      <button type="button" className="fa-btn fa-btn--primary" disabled={readonly || draft === xml} onClick={apply}>{t('common.apply')}</button>
    </>
  )

  return (
    <BaseDialog open={open} title={t('xml.title')} subtitle={t('xml.help')} width="900px" onOpenChange={onOpenChange} footer={footer}>
      {renderEditor ? renderEditor(draft, setDraft) : <textarea className="fa-textarea fa-xml" spellCheck={false} readOnly={readonly} aria-label={t('xml.title')} value={draft} onChange={(event) => setDraft(event.target.value)} />}
    </BaseDialog>
  )
}
