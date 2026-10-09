import { tableRows, tableValue, type AssistantQuestion, type TableRow } from '@auditcore/ui-core'
import { useDataProtectionText } from '../shared'

export function AssistantTable({ question, value, onChange }: { question: AssistantQuestion; value: string; onChange: (value: string) => void }) {
  const { t } = useDataProtectionText()
  const rows = tableRows(question, value)
  const update = (next: TableRow[]): void => onChange(tableValue(next) || JSON.stringify(next))
  const setCell = (index: number, key: string, cell: string): void => update(rows.map((row, i) => (i === index ? { ...row, [key]: cell } : row)))
  const addRow = (): void => update([...rows, Object.fromEntries(question.columns.map((c) => [c.key, '']))])
  return (
    <>
      <table className="fa-assistant__table">
        <caption>{t('tableCaption', { question: question.text })}</caption>
        <thead>
          <tr>
            {question.columns.map((column) => (
              <th key={column.key} scope="col">{column.title}{column.required ? ' *' : ''}</th>
            ))}
            <th scope="col"><span className="fa-dataprotection__muted">–</span></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {question.columns.map((column) => (
                <td key={column.key}>
                  {column.choices.length ? (
                    <select value={row[column.key]} aria-label={`${column.title} ${index + 1}`} onChange={(event) => setCell(index, column.key, event.target.value)}>
                      <option value="">{t('chooseValue')}</option>
                      {column.choices.map((choice) => (
                        <option key={choice} value={choice}>{choice}</option>
                      ))}
                    </select>
                  ) : (
                    <input value={row[column.key]} type="text" aria-label={`${column.title} ${index + 1}`} onChange={(event) => setCell(index, column.key, event.target.value)} />
                  )}
                </td>
              ))}
              <td><button type="button" onClick={() => update(rows.filter((_, i) => i !== index))}>{t('removeRow', { row: index + 1 })}</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      <button type="button" onClick={addRow}>{t('addRow')}</button>
    </>
  )
}
