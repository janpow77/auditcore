/** Small dialog asking for one name (replaces `window.prompt`). */

import { useEffect, useState } from 'react'
import { useI18n } from '../i18n'
import { BaseDialog } from './BaseDialog'

export interface PromptDialogProps {
  open: boolean
  title: string
  label: string
  value?: string
  onOpenChange: (open: boolean) => void
  onConfirm: (value: string) => void
}

export function PromptDialog({ open, title, label, value, onOpenChange, onConfirm }: PromptDialogProps) {
  const { t } = useI18n()
  const [text, setText] = useState(value ?? '')

  useEffect(() => {
    if (open) setText(value ?? '')
  }, [open, value])

  const confirm = () => {
    if (!text.trim()) return
    onConfirm(text.trim())
    onOpenChange(false)
  }

  const footer = (
    <>
      <button type="button" className="fa-btn" onClick={() => onOpenChange(false)}>{t('common.cancel')}</button>
      <button type="button" className="fa-btn fa-btn--primary" disabled={!text.trim()} onClick={confirm}>{t('common.apply')}</button>
    </>
  )

  return (
    <BaseDialog open={open} title={title} width="420px" onOpenChange={onOpenChange} footer={footer}>
      <label className="fa-field">
        <span className="fa-label">{label}</span>
        <input className="fa-input" value={text} onChange={(event) => setText(event.target.value)} onKeyDown={(event) => event.key === 'Enter' && (event.preventDefault(), confirm())} />
      </label>
    </BaseDialog>
  )
}
