import type { FormEvent } from 'react'
import { saveFile } from '@flowaudit/common/browser'
import { reportingErrorKey, reportingTablesText } from '@flowaudit/ui-core'
import { Button } from '../base/Button'
import type { UseReportExport } from './useReportExport'

/** Profil, Dateiname, Herkunft, Vorschau und Export (Formular aus `ReportExportPanel.vue`). */
export function ReportForm({ view, id }: { view: UseReportExport; id: string }) {
  const { state, controller, t, profile, locale } = view
  const catalogue = state.catalogue
  if (!catalogue) return null
  const submit = (event: FormEvent): void => {
    event.preventDefault()
    void controller.preview()
  }
  const runExport = async (): Promise<void> => {
    const file = await controller.exportWorkbook()
    if (file && typeof URL.createObjectURL === 'function') saveFile(file)
  }
  return (
    <form className="fa-report__card" aria-labelledby={`${id}-h`} noValidate onSubmit={submit}>
      <h3 id={`${id}-h`} className="fa-report__heading">{t('title')}</h3>
      <p className="fa-report__muted" data-testid="report-tables">{reportingTablesText(view.tables, t, locale)}</p>
      <div className="fa-report__form">
        <label className="fa-report__field">
          <span className="fa-report__label">{t('profile')}</span>
          <select value={state.profileId ?? ''} className="fa-report__input" data-testid="report-profile" onChange={(event) => controller.setProfile(event.target.value || null)}>
            <option value="">{t('choose')}</option>
            {catalogue.profiles.map((entry) => <option key={entry.id} value={entry.id}>{entry.label}</option>)}
          </select>
        </label>
        <label className="fa-report__field">
          <span className="fa-report__label">{t('filename')}</span>
          <input value={state.filename} className="fa-report__input" autoComplete="off" placeholder="bericht.xlsx" data-testid="report-filename" onChange={(event) => controller.setFilename(event.target.value)} />
        </label>
      </div>
      {profile ? (
        <details className="fa-report__source">
          <summary>{t('profileSource')}</summary>
          <p>{profile.description}</p>
          <p>{t('profileVersion', { version: profile.version, status: profile.status })}</p>
          {profile.source ? <p>{profile.source}</p> : null}
        </details>
      ) : null}
      {catalogue.excel_available ? null : <p className="fa-report__muted">{t('excelMissing')}</p>}
      {state.validation ? <p className="fa-report__error" role="alert">{t(reportingErrorKey(state.validation))}</p> : null}
      <div className="fa-report__actions">
        <Button type="submit" loading={state.busy === 'preview'} testId="report-preview">{t('preview')}</Button>
        <Button variant="primary" disabled={!catalogue.excel_available} loading={state.busy === 'export'} testId="report-export" onClick={() => void runExport()}>{t('export')}</Button>
      </div>
      <p className="fa-report__muted" aria-live="polite" data-testid="report-status">{state.exportedName ? t('exported', { filename: state.exportedName }) : ''}</p>
    </form>
  )
}
