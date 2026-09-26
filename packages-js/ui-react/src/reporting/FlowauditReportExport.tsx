import { reportingWorkbookText } from '@flowaudit/ui-core'
import { useElementId } from '../store'
import { ReportForm } from './ReportForm'
import { ReportPreview } from './ReportPreview'
import { useReportExport, type ReportExportInputs } from './useReportExport'

export type FlowauditReportExportProps = ReportExportInputs

/**
 * Tabellenexport nach Excel als native React-Komponente (Vertrag wie
 * `<flowaudit-report-export>`): Formatprofil wählen, Vorschau der
 * Spaltenformate und ersten Zeilen, XLSX-Export. Ereignisse:
 * `onPreviewCompleted`, `onExportCompleted`, `onError`.
 */
export function FlowauditReportExport(props: FlowauditReportExportProps) {
  const view = useReportExport(props)
  const { state, t, locale } = view
  const id = useElementId('fa-report')
  return (
    <div className="fa-report" lang={locale}>
      {props.port ? null : <p className="fa-report__muted" role="status">{t('noPort')}</p>}
      {state.busy === 'load' ? <p className="fa-report__muted" role="status">{t('loading')}</p> : null}
      {state.error ? <p className="fa-report__failure" role="alert">{t('failed', { message: state.error })}</p> : null}
      <ReportForm view={view} id={id} />
      {state.preview ? (
        <section className="fa-report__card" aria-labelledby={`${id}-p`} aria-live="polite">
          <h3 id={`${id}-p`} className="fa-report__heading">{t('preview')}</h3>
          {state.stale ? <p className="fa-report__notice" data-testid="report-stale">{t('previewStale')}</p> : null}
          <p className="fa-report__muted" data-testid="report-workbook">{reportingWorkbookText(state.preview, t, locale)}</p>
          <p className="fa-report__muted">{t('notice')}</p>
          {state.preview.tables.map((table, index) => <ReportPreview key={table.name} table={table} index={index} t={t} locale={locale} />)}
        </section>
      ) : null}
    </div>
  )
}
