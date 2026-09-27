import type { FormEvent } from 'react'
import { saveFile } from '@auditcore/common/browser'
import { formatOptions, reporttemplatesCanRender, type TemplateDetail, type TemplateFormat } from '@auditcore/ui-core'
import { Button } from '../base/Button'
import type { UseReportTemplates } from './useReportTemplates'

/** Version, Art, Beschreibung und Datenherkunft der gewählten Vorlage. */
function TemplateInfo({ detail, hasData, t }: { detail: TemplateDetail; hasData: boolean; t: UseReportTemplates['t'] }) {
  return (
    <>
      <p className="fa-reporttemplates__muted" data-testid="template-version">{`${t('version', { version: detail.version, status: detail.status })} · ${t(`kind${detail.kind}`)}`}</p>
      <p className="fa-reporttemplates__muted">{detail.description}</p>
      <p className="fa-reporttemplates__muted" data-testid="template-data">{`${t('data')}: ${hasData ? t('dataGiven') : t('dataSample')}`}</p>
    </>
  )
}

/** Vorlage, Format, Gestaltung, Dateiname, Vorschau und Bericht (Formular aus `ReportTemplates.vue`). */
export function TemplateForm({ view, id }: { view: UseReportTemplates; id: string }) {
  const { state, controller, t, hasData } = view
  const catalogue = state.catalogue
  if (!catalogue?.templates.length) return null
  const formats = formatOptions(state)
  const missing = formats.find((entry) => entry.format === state.format && !entry.available)
  const detail = state.detail
  const submit = (event: FormEvent): void => {
    event.preventDefault()
    void controller.preview()
  }
  const runRender = async (): Promise<void> => {
    const file = await controller.render()
    if (file && typeof URL.createObjectURL === 'function') saveFile(file)
  }
  return (
    <form className="fa-reporttemplates__card" aria-labelledby={`${id}-h`} noValidate onSubmit={submit}>
      <h3 id={`${id}-h`} className="fa-reporttemplates__heading">{t('title')}</h3>
      <div className="fa-reporttemplates__form">
        <label className="fa-reporttemplates__field">
          <span className="fa-reporttemplates__label">{t('template')}</span>
          <select value={state.templateId ?? ''} className="fa-reporttemplates__input" data-testid="template-select" onChange={(event) => void controller.select(event.target.value || null)}>
            <option value="">{t('choose')}</option>
            {catalogue.templates.map((entry) => <option key={entry.id} value={entry.id}>{entry.title}</option>)}
          </select>
        </label>
        <label className="fa-reporttemplates__field">
          <span className="fa-reporttemplates__label">{t('format')}</span>
          <select value={state.format ?? ''} className="fa-reporttemplates__input" data-testid="template-format" onChange={(event) => controller.setFormat((event.target.value || null) as TemplateFormat | null)}>
            {formats.map((entry) => <option key={entry.format} value={entry.format}>{entry.format.toUpperCase()}</option>)}
          </select>
        </label>
        <label className="fa-reporttemplates__field">
          <span className="fa-reporttemplates__label">{t('design')}</span>
          <select value={state.designId ?? ''} className="fa-reporttemplates__input" data-testid="template-design" onChange={(event) => controller.setDesign(event.target.value || null)}>
            {catalogue.designs.map((entry) => <option key={entry.id} value={entry.id}>{entry.label}</option>)}
          </select>
        </label>
        <label className="fa-reporttemplates__field">
          <span className="fa-reporttemplates__label">{t('filename')}</span>
          <input value={state.filename} className="fa-reporttemplates__input" autoComplete="off" data-testid="template-filename" onChange={(event) => controller.setFilename(event.target.value)} />
        </label>
      </div>
      {state.busy === 'detail' ? <p className="fa-reporttemplates__muted" role="status">{t('loadingDetail')}</p> : null}
      {detail ? <TemplateInfo detail={detail} hasData={hasData} t={t} /> : null}
      {missing ? <p className="fa-reporttemplates__failure" role="alert">{t('formatMissing', { format: missing.format.toUpperCase() })}</p> : null}
      <div className="fa-reporttemplates__actions">
        <Button type="submit" disabled={!detail} loading={state.busy === 'preview'} testId="template-preview-button">{t('preview')}</Button>
        <Button variant="primary" disabled={!reporttemplatesCanRender(state)} loading={state.busy === 'render'} testId="template-render" onClick={() => void runRender()}>{t('render')}</Button>
      </div>
      <p className="fa-reporttemplates__muted" aria-live="polite" data-testid="template-status">{state.renderedName ? t('rendered', { filename: state.renderedName }) : ''}</p>
    </form>
  )
}
