/**
 * `@auditcore/sampling-templates-core/xlsx`: Excel-Austausch, getrennt vom
 * Kern ladbar (zieht fflate nach). Oberflächen laden diesen Einstieg erst,
 * wenn exportiert oder eine `.xlsx`-Datei geöffnet wird.
 */
export { WORKSPACE_SHEET, exportWorkbook, type ExportOptions, type ExportedWorkbook } from './export'
export { compareWithWorkbook, type ImportDifference } from './compare'
export { importWorkbook, type ImportIssue, type ImportReason, type WorkbookImport } from './import'
export { MAX_WORKBOOK_CELLS, MAX_WORKBOOK_SIZE, WorkbookError, readWorkbook, type ReadWorkbook, type WorkbookCellValue } from './reader'
export { XLSX_MEDIA_TYPE, writeWorkbook, type CellStyle, type WorkbookCell, type WorkbookSheet } from './writer'
