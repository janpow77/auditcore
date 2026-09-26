/**
 * Framework-freie Teile, die bis 0.1.0 nur in `@auditcore/ui` lagen, jetzt aus
 * `@auditcore/common` – mit denselben Namen wie in `@auditcore/ui`, damit
 * React-Anwendungen sie ohne Vue-Import nutzen können. Die neue API
 * (Berliner Zeit, Ersatzwert „—“, strikte Zahleneingabe) steht direkt in
 * `@auditcore/common`.
 */
export {
  RestError,
  ariaSort,
  columnCells,
  compareValues,
  detectDecimal,
  detectDelimiter,
  guessNumberColumn,
  intlFormatDate as formatDate,
  intlFormatNumber as formatNumber,
  intlFormatPercent as formatPercent,
  localeTag,
  nextSort,
  numberColumn,
  parseNumber,
  parseTable,
  requestFile,
  requestJson,
  sortRows,
  splitLine,
  type CellValue,
  type DecimalSeparator,
  type Delimiter,
  type DownloadFile,
  type FetchLike,
  type NextSortOptions,
  type NumberColumn,
  type ParsedTable,
  type RestOptions,
  type SortDirection,
  type SortState,
  type TableColumn,
  type TableRow,
} from '@auditcore/common'
export { saveFile } from '@auditcore/common/browser'
