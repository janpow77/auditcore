// Known helper bugs (test fixture): the parser of the original BeleglisteGrid.
export function BeleglisteGrid({ rows }: { rows: Array<Record<string, unknown>> }) {
  const parseDecimal = (value: unknown): number => {
    if (value === null || value === undefined) return 0
    const strVal = String(value).replace(',', '.')
    const num = parseFloat(strVal)
    return isNaN(num) ? 0 : num
  }
  const exportCsv = () => {
    const text = rows.map((row) => [row.name, parseDecimal(row.amount)].join(';')).join('\n')
    return new Blob([text], { type: 'text/csv' })
  }
  return <button onClick={exportCsv}>{rows.length}</button>
}
