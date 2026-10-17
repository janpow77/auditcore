/**
 * Schreibt eine `.xlsx`-Arbeitsmappe (Office Open XML) mit Zahlenformaten,
 * Schriftschnitt, Füllfarben, Spaltenbreiten und ausgeblendeten Blättern.
 * Bewusst klein gehalten: nur, was der Ergebnisexport braucht; gepackt wird
 * mit fflate. Texte stehen als Inline-Strings in den Zellen.
 */
import { strToU8, zipSync } from 'fflate'
import { columnName, escapeXml } from './xml'

/** Gestaltung einer Zelle. Farben als RGB-Hex ohne `#`. */
export interface CellStyle {
  /** Zahlenformat wie in Excel, z. B. `#,##0.00" €"`. */
  format?: string
  bold?: boolean
  color?: string
  fill?: string
  wrap?: boolean
}

export interface WorkbookCell {
  value: number | string | null
  style?: CellStyle
}

export interface WorkbookSheet {
  name: string
  hidden?: boolean
  /** Spaltenbreiten in Zeichen. */
  widths?: readonly number[]
  rows: readonly (readonly (WorkbookCell | null)[])[]
}

const XML = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
const MAIN = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
const REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
const PACKAGE_REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
/** Eingebaute Zahlenformate von Excel, die keine eigene Definition brauchen. */
const BUILT_IN: Readonly<Record<string, number>> = { General: 0, '0': 1, '0.00': 2, '#,##0': 3, '#,##0.00': 4, '0%': 9, '0.00%': 10, '@': 49 }
const FIRST_CUSTOM_FORMAT = 164

/** Sammelt die verwendeten Gestaltungen und vergibt die Indizes der Formatvorlage. */
class StyleSheet {
  private readonly formats: string[] = []
  private readonly fonts = ['<font><sz val="11"/><name val="Calibri"/></font>']
  private readonly fills = ['<fill><patternFill patternType="none"/></fill>', '<fill><patternFill patternType="gray125"/></fill>']
  private readonly xfs = ['<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>']
  private readonly index = new Map<string, number>()

  private formatId(format: string | undefined): number {
    if (!format) return 0
    const builtIn = BUILT_IN[format]
    if (builtIn !== undefined) return builtIn
    if (!this.formats.includes(format)) this.formats.push(format)
    return FIRST_CUSTOM_FORMAT + this.formats.indexOf(format)
  }

  private static intern(list: string[], entry: string): number {
    if (!list.includes(entry)) list.push(entry)
    return list.indexOf(entry)
  }

  /** Index der Zellformatierung (`s`-Attribut). */
  id(style: CellStyle | undefined): number {
    if (!style) return 0
    const key = JSON.stringify(style)
    const known = this.index.get(key)
    if (known !== undefined) return known
    const color = style.color ? `<color rgb="FF${style.color}"/>` : ''
    const font = StyleSheet.intern(this.fonts, `<font>${style.bold ? '<b/>' : ''}<sz val="11"/>${color}<name val="Calibri"/></font>`)
    const fill = style.fill ? StyleSheet.intern(this.fills, `<fill><patternFill patternType="solid"><fgColor rgb="FF${style.fill}"/></patternFill></fill>`) : 0
    const alignment = `<alignment vertical="top"${style.wrap ? ' wrapText="1"' : ''}/>`
    this.xfs.push(
      `<xf numFmtId="${this.formatId(style.format)}" fontId="${font}" fillId="${fill}" borderId="0" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1" applyAlignment="1">${alignment}</xf>`,
    )
    this.index.set(key, this.xfs.length - 1)
    return this.xfs.length - 1
  }

  xml(): string {
    const formats = this.formats.map((code, index) => `<numFmt numFmtId="${FIRST_CUSTOM_FORMAT + index}" formatCode="${escapeXml(code)}"/>`)
    const numFmts = formats.length ? `<numFmts count="${formats.length}">${formats.join('')}</numFmts>` : ''
    return (
      `${XML}<styleSheet xmlns="${MAIN}">${numFmts}` +
      `<fonts count="${this.fonts.length}">${this.fonts.join('')}</fonts>` +
      `<fills count="${this.fills.length}">${this.fills.join('')}</fills>` +
      '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>' +
      '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>' +
      `<cellXfs count="${this.xfs.length}">${this.xfs.join('')}</cellXfs>` +
      '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>'
    )
  }
}

function cellXml(cell: WorkbookCell | null, reference: string, styles: StyleSheet): string {
  if (!cell || cell.value === null || cell.value === '') return ''
  const style = styles.id(cell.style)
  const attributes = `r="${reference}"${style ? ` s="${style}"` : ''}`
  if (typeof cell.value === 'number') return `<c ${attributes}><v>${cell.value}</v></c>`
  return `<c ${attributes} t="inlineStr"><is><t xml:space="preserve">${escapeXml(cell.value)}</t></is></c>`
}

function sheetXml(sheet: WorkbookSheet, styles: StyleSheet): string {
  const widths = (sheet.widths ?? []).map((width, index) => `<col min="${index + 1}" max="${index + 1}" width="${width}" customWidth="1"/>`)
  const rows = sheet.rows.map((row, rowIndex) => {
    const cells = row.map((cell, columnIndex) => cellXml(cell, `${columnName(columnIndex + 1)}${rowIndex + 1}`, styles)).join('')
    return cells ? `<row r="${rowIndex + 1}">${cells}</row>` : ''
  })
  return `${XML}<worksheet xmlns="${MAIN}">${widths.length ? `<cols>${widths.join('')}</cols>` : ''}<sheetData>${rows.join('')}</sheetData></worksheet>`
}

function workbookXml(sheets: readonly WorkbookSheet[]): string {
  const entries = sheets.map(
    (sheet, index) => `<sheet name="${escapeXml(sheet.name)}" sheetId="${index + 1}"${sheet.hidden ? ' state="hidden"' : ''} r:id="rId${index + 1}"/>`,
  )
  return `${XML}<workbook xmlns="${MAIN}" xmlns:r="${REL}"><sheets>${entries.join('')}</sheets></workbook>`
}

function relationsXml(count: number): string {
  const sheets = Array.from({ length: count }, (_, index) => `<Relationship Id="rId${index + 1}" Type="${REL}/worksheet" Target="worksheets/sheet${index + 1}.xml"/>`)
  return `${XML}<Relationships xmlns="${PACKAGE_REL}">${sheets.join('')}<Relationship Id="rId${count + 1}" Type="${REL}/styles" Target="styles.xml"/></Relationships>`
}

function contentTypesXml(count: number): string {
  const type = 'application/vnd.openxmlformats-officedocument.spreadsheetml'
  const sheets = Array.from({ length: count }, (_, index) => `<Override PartName="/xl/worksheets/sheet${index + 1}.xml" ContentType="${type}.worksheet+xml"/>`)
  return (
    `${XML}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">` +
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>' +
    `<Override PartName="/xl/workbook.xml" ContentType="${type}.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="${type}.styles+xml"/>${sheets.join('')}</Types>`
  )
}

/** Medientyp einer `.xlsx`-Datei. */
export const XLSX_MEDIA_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

/** Arbeitsmappe als Bytes einer `.xlsx`-Datei. */
export function writeWorkbook(sheets: readonly WorkbookSheet[]): Uint8Array {
  const styles = new StyleSheet()
  const files: Record<string, Uint8Array> = {}
  sheets.forEach((sheet, index) => {
    files[`xl/worksheets/sheet${index + 1}.xml`] = strToU8(sheetXml(sheet, styles))
  })
  files['[Content_Types].xml'] = strToU8(contentTypesXml(sheets.length))
  files['_rels/.rels'] = strToU8(`${XML}<Relationships xmlns="${PACKAGE_REL}"><Relationship Id="rId1" Type="${REL}/officeDocument" Target="xl/workbook.xml"/></Relationships>`)
  files['xl/workbook.xml'] = strToU8(workbookXml(sheets))
  files['xl/_rels/workbook.xml.rels'] = strToU8(relationsXml(sheets.length))
  files['xl/styles.xml'] = strToU8(styles.xml())
  return zipSync(files, { level: 6 })
}
