import type { ReporttemplatesMessageKey, TemplatePreview, Translate } from '@auditcore/ui-core'

interface Props {
  preview: TemplatePreview
  stale: boolean
  t: Translate<ReporttemplatesMessageKey>
}

/** Ergebnis der Vorlagenvorschau (Markup wie `TemplatePreviewPane.vue`). */
export function TemplatePreviewPane({ preview, stale, t }: Props) {
  return (
    <section className="fa-reporttemplates__card" aria-live="polite" data-testid="template-preview">
      <h3 className="fa-reporttemplates__heading">{t('preview')}</h3>
      {stale ? <p className="fa-reporttemplates__notice">{t('previewStale')}</p> : null}
      {preview.valid ? (
        <>
          <p className="fa-reporttemplates__muted">{t('valid')}</p>
          <p className="fa-reporttemplates__muted">{preview.text_blocks.length ? t('usedBlocks', { blocks: preview.text_blocks.join(', ') }) : t('noBlocks')}</p>
          {preview.html ? <iframe className="fa-reporttemplates__frame" sandbox="" referrerPolicy="no-referrer" title={t('previewFrame')} srcDoc={preview.html} /> : null}
        </>
      ) : (
        <>
          <p className="fa-reporttemplates__failure" role="alert">{t('invalid', { count: preview.issues.length })}</p>
          <ul className="fa-reporttemplates__issues">
            {preview.issues.map((issue) => <li key={issue.path + issue.message}><code>{issue.path}</code>: {issue.message}</li>)}
          </ul>
        </>
      )}
      <p className="fa-reporttemplates__muted">{t('notice')}</p>
    </section>
  )
}
