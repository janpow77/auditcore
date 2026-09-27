import { schemaFields, textBlockRows, type ReporttemplatesMessageKey, type TemplateDetail, type Translate } from '@auditcore/ui-core'

/** Datenvertrag und Textbausteine einer Vorlage (Markup wie `TemplateContract.vue`). */
export function TemplateContract({ detail, t }: { detail: TemplateDetail; t: Translate<ReporttemplatesMessageKey> }) {
  const blocks = textBlockRows(detail)
  return (
    <details className="fa-reporttemplates__card" data-testid="template-contract">
      <summary className="fa-reporttemplates__heading">{t('contract')}</summary>
      <div className="fa-reporttemplates__scroll">
        <table className="fa-reporttemplates__table">
          <thead>
            <tr><th scope="col">{t('field')}</th><th scope="col">{t('fieldType')}</th><th scope="col">{t('fieldRequired')}</th></tr>
          </thead>
          <tbody>
            {schemaFields(detail).map((field) => (
              <tr key={field.name}>
                <td><code>{field.name}</code>{field.title ? <span> – {field.title}</span> : null}</td>
                <td>{field.type}</td>
                <td>{field.required ? t('yes') : t('no')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {blocks.length ? (
        <>
          <h4 className="fa-reporttemplates__heading">{t('textBlocks')}</h4>
          <ul className="fa-reporttemplates__blocks">
            {blocks.map((block) => (
              <li key={block.id}>
                <strong>{block.title}</strong>
                {block.required ? <span> · {t('required')}</span> : null}
                {block.conditional ? <span> · {t('conditional')}</span> : null}
                {block.legalBasis ? <span className="fa-reporttemplates__muted"> · {t('legalBasis', { basis: block.legalBasis })}</span> : null}
              </li>
            ))}
          </ul>
        </>
      ) : null}
    </details>
  )
}
