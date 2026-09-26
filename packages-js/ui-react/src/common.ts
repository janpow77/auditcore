/**
 * Framework-freie Teile, die bis 0.1.0 nur in `@flowaudit/ui` lagen, jetzt aus
 * `@flowaudit/common` – mit denselben Namen wie in `@flowaudit/ui`, damit
 * React-Anwendungen sie ohne Vue-Import nutzen können. Die neue API
 * (Berliner Zeit, Ersatzwert „—“, strikte Zahleneingabe) steht direkt in
 * `@flowaudit/common`.
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
} from '@flowaudit/common'
export { saveFile } from '@flowaudit/common/browser'
