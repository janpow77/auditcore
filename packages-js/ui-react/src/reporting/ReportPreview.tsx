import { reportCellText, reportingSampleNote, reportingSheetHeading, type Locale, type ReportingTranslate, type TablePreview } from '@auditcore/ui-core'

/** Ein Blatt der Vorschau: Spaltenformate und erste Zeilen (wie `ReportPreview.vue`). */
export function ReportPreview({ table, index, t, locale }: { table: TablePreview; index: number; t: ReportingTranslate; locale: Locale }) {
  const note = reportingSampleNote(table, t, locale)
  return (
    <section className="fa-report__sheet" data-testid={`report-sheet-${index}`}>
      <h4 className="fa-report__heading">{reportingSheetHeading(table, t, locale)}</h4>
      <div className="fa-report__scroll">
        <table className="fa-report__table" data-testid="report-columns">
          <caption>{t('columns')}</caption>
          <thead>
            <tr><th scope="col">{t('colName')}</th><th scope="col">{t('colType')}</th><th scope="col">{t('colFormat')}</th><th scope="col">{t('colSource')}</th></tr>
          </thead>
          <tbody>
            {table.columns.map((column) => (
              <tr key={column.name}>
                <th scope="row">{column.name}</th>
                <td>{column.type}</td>
                <td><code>{column.format}</code></td>
                <td>{t(column.source === 'override' ? 'sourceoverride' : 'sourceprofile')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="fa-report__scroll">
        <table className="fa-report__table" data-testid="report-sample">
          <caption>{t('sample')}</caption>
          <thead>
            <tr>{table.columns.map((column) => <th key={column.name} scope="col">{column.name}</th>)}</tr>
          </thead>
          <tbody>
            {table.sample.map((row, rowIndex) => (
              <tr key={rowIndex}>{row.map((cell, cellIndex) => <td key={cellIndex}>{reportCellText(cell, locale)}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
      {note ? <p className="fa-report__muted">{note}</p> : null}
    </section>
  )
}
