import { reporttemplatesIsEmpty } from '@auditcore/ui-core'
import { useElementId } from '../store'
import { TemplateContract } from './TemplateContract'
import { TemplateForm } from './TemplateForm'
import { TemplatePreviewPane } from './TemplatePreviewPane'
import { useReportTemplates, type ReportTemplatesInputs } from './useReportTemplates'

export type FlowauditReportTemplatesProps = ReportTemplatesInputs

/**
 * Berichtsvorlagen als native React-Komponente (Vertrag wie
 * `<flowaudit-report-templates>`): Vorlage wählen, Datenvertrag und
 * Textbausteine sehen, Vorschau, Bericht als DOCX/PDF/HTML. Ereignisse:
 * `onTemplateSelect`, `onPreviewCompleted`, `onReportRendered`, `onError`.
 */
export function FlowauditReportTemplates(props: FlowauditReportTemplatesProps) {
  const view = useReportTemplates(props)
  const { state, t, locale } = view
  const id = useElementId('fa-reporttemplates')
  return (
    <div className="fa-reporttemplates" lang={locale}>
      {props.port ? null : <p className="fa-reporttemplates__muted" role="status">{t('noPort')}</p>}
      {state.busy === 'load' ? <p className="fa-reporttemplates__muted" role="status">{t('loading')}</p> : null}
      {state.error ? <p className="fa-reporttemplates__failure" role="alert">{t('failed', { message: state.error })}</p> : null}
      {reporttemplatesIsEmpty(state) ? <p className="fa-reporttemplates__muted">{t('empty')}</p> : null}
      <TemplateForm view={view} id={id} />
      {state.detail ? <TemplateContract detail={state.detail} t={t} /> : null}
      {state.preview ? <TemplatePreviewPane preview={state.preview} stale={state.stale} t={t} /> : null}
    </div>
  )
}
