/**
 * Export dialog (legacy `BpmnExportDialog`, extended): SVG/PNG/PDF/BPMN/MyST,
 * process table CSV/MyST, RCM, findings list; header, legends, legal bases,
 * metadata, neutral mode and page format.
 */

import { useEffect, useState, type ReactNode } from 'react'
import { CONFIDENTIALITY, DEFAULT_EXPORT_CHOICE, label, type ExportChoice, type ExportData, type ExportFormat } from '@auditcore/bpmn-flowaudit'
import { EXPORT_FORMATS, FORMAT_ICONS, initialExportChoice, ORIENTATIONS } from '@auditcore/bpmn-flowaudit/ui'
import { BaseDialog } from '../base/BaseDialog'
import { FaIcon } from '../base/FaIcon'
import { useI18n } from '../i18n'

type Choice = Omit<ExportChoice, 'format'>
type Flag = 'showHeader' | 'showLegend' | 'showMarkerLegend' | 'showLegalBases' | 'showMetadata' | 'neutral'

export interface ExportDialogProps {
  open: boolean
  defaultTitle: string
  subtitle?: string
  data: ExportData
  confidentiality?: string
  excel?: boolean
  onOpenChange: (open: boolean) => void
  onExport: (choice: ExportChoice) => void
}

interface PartProps {
  choice: Choice
  set: (patch: Partial<Choice>) => void
}

function Check({ choice, set, flag, children }: PartProps & { flag: Flag; children: ReactNode }) {
  return (
    <label className="fa-check">
      <input type="checkbox" checked={Boolean(choice[flag])} onChange={(event) => set({ [flag]: event.target.checked })} />
      {children}
    </label>
  )
}

function ExportOptions({ choice, set, data, confidentiality }: PartProps & { data: ExportData; confidentiality?: string }) {
  const { t, locale } = useI18n()
  const part = { choice, set }
  return (
    <>
      <div className="fa-grid-2">
        <label className="fa-field fa-field--wide"><span className="fa-label">{t('export.docTitle')}</span><input className="fa-input" value={choice.title} onChange={(event) => set({ title: event.target.value })} /></label>
        <label className="fa-field fa-field--wide"><span className="fa-label">{t('export.subtitle')}</span><input className="fa-input" value={choice.subtitle} onChange={(event) => set({ subtitle: event.target.value })} /></label>
      </div>
      <fieldset className="fa-export__options">
        <legend className="fa-label">{t('export.attachments')}</legend>
        <Check {...part} flag="showHeader">{t('export.header')}</Check>
        <Check {...part} flag="showLegend">{t('export.legend')} <span className="fa-help">({t('export.legendCount', { count: data.colors.length })})</span></Check>
        <Check {...part} flag="showMarkerLegend">{t('export.markerLegend')}</Check>
        <Check {...part} flag="showLegalBases">{t('export.legalBases')} <span className="fa-help">({t('export.legalCount', { count: data.legalBases.length })})</span></Check>
        <Check {...part} flag="showMetadata">{t('export.metadata')}</Check>
      </fieldset>
      <div className="fa-export__neutral fa-card">
        <Check {...part} flag="neutral"><FaIcon name="neutral" size={16} /><strong>{t('export.neutral')}</strong></Check>
        <p className="fa-help">{t('export.neutralHelp')}</p>
        {confidentiality ? <p className="fa-badge fa-badge--warning">{t('export.confidentiality', { level: label(CONFIDENTIALITY[confidentiality], locale) || confidentiality })}</p> : null}
      </div>
    </>
  )
}

function PageOptions({ choice, set }: PartProps) {
  const { t } = useI18n()
  return (
    <div className="fa-grid-2 fa-section">
      <label className="fa-field">
        <span className="fa-label">{t('export.page')}</span>
        <select className="fa-select" value={choice.pageFormat} onChange={(event) => set({ pageFormat: event.target.value as Choice['pageFormat'] })}><option value="a4">DIN A4</option><option value="a3">DIN A3</option></select>
      </label>
      <label className="fa-field">
        <span className="fa-label">{' '}</span>
        <select className="fa-select" value={choice.orientation} onChange={(event) => set({ orientation: event.target.value as Choice['orientation'] })}>
          {ORIENTATIONS.map((option) => <option key={option} value={option}>{t(`export.orientation.${option}`)}</option>)}
        </select>
      </label>
    </div>
  )
}

export function ExportDialog({ open, defaultTitle, subtitle, data, confidentiality, excel, onOpenChange, onExport }: ExportDialogProps) {
  const { t } = useI18n()
  const [choice, setChoice] = useState<Choice>({ ...DEFAULT_EXPORT_CHOICE })

  useEffect(() => {
    if (open) setChoice(initialExportChoice(defaultTitle, subtitle, data, confidentiality))
  }, [open, defaultTitle, subtitle, data, confidentiality])

  const set = (patch: Partial<Choice>) => setChoice((current) => ({ ...current, ...patch }))
  const run = (format: ExportFormat) => {
    onExport({ ...choice, format })
    onOpenChange(false)
  }

  return (
    <BaseDialog open={open} title={t('export.title')} width="620px" onOpenChange={onOpenChange}>
      <ExportOptions choice={choice} set={set} data={data} confidentiality={confidentiality} />
      <PageOptions choice={choice} set={set} />
      <h3 className="fa-section__title fa-section">{t('export.formats')}</h3>
      <div className="fa-export__formats">
        {EXPORT_FORMATS.map((format) => (
          <button key={format} type="button" className="fa-btn" onClick={() => run(format)}>
            <FaIcon name={FORMAT_ICONS[format] ?? 'analysis'} size={16} />
            {t(`export.format.${format}`)}
          </button>
        ))}
        {excel ? <button type="button" className="fa-btn" onClick={() => run('excel')}><FaIcon name="analysis" size={16} />{t('export.format.excel')}</button> : null}
      </div>
    </BaseDialog>
  )
}
