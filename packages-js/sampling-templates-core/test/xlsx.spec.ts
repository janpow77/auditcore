import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { strFromU8, strToU8, unzipSync, zipSync } from 'fflate'
import { describe, expect, it } from 'vitest'
import { sheet as sheet03 } from '../src/sheets/03_MUS_1Z/index'
import { computeWorkspace } from '../src/workspace/compute'
import { openWorkspace } from '../src/workspace/open'
import { emptyWorkspace, type WorkspaceState } from '../src/workspace/types'
import { WORKSPACE_SHEET, WorkbookError, compareWithWorkbook, exportWorkbook, importWorkbook, readWorkbook, writeWorkbook } from '../src/xlsx/index'
import { FOUNDATION_SHEETS } from './sheets'

const now = new Date('2026-10-13T09:30:00Z')
const state: WorkspaceState = { ...emptyWorkspace(), activeMethod: '03_MUS_1Z', sheets: { '03_MUS_1Z': sheet03.sample.inputs } }

function partOf(data: Uint8Array, name: string): string {
  return strFromU8(unzipSync(data)[name]!)
}

describe('Arbeitsmappe schreiben und lesen', () => {
  it('Zahlen, Texte mit Sonderzeichen und leere Zellen', () => {
    const data = writeWorkbook([{ name: 'Blatt & Co', rows: [[{ value: 1.5 }, { value: 'Prüfung <"A&B"> – ✔\nZeile 2' }, null, { value: null }], [], [{ value: 0 }]] }])
    const workbook = readWorkbook(data)
    expect(workbook.sheetNames).toEqual(['Blatt & Co'])
    const cells = workbook.cells('Blatt & Co')
    expect(cells.get('A1')).toEqual({ value: 1.5, formula: false, formulaText: '' })
    expect(cells.get('B1')?.value).toBe('Prüfung <"A&B"> – ✔\nZeile 2')
    expect(cells.get('A3')?.value).toBe(0)
    expect(cells.has('C1')).toBe(false)
    expect(workbook.cells('fehlt').size).toBe(0)
  })

  it('Zahlenformate, Schriftschnitt, Füllung und ausgeblendete Blätter stehen in der Datei', () => {
    const data = writeWorkbook([
      { name: 'A', widths: [12, 30], rows: [[{ value: 2.5, style: { format: '#,##0.00" €"', bold: true, fill: 'E2EFDA' } }, { value: 0.02, style: { format: '0.00%' } }]] },
      { name: 'B', hidden: true, rows: [[{ value: 'x' }]] },
    ])
    expect(partOf(data, 'xl/workbook.xml')).toContain('<sheet name="B" sheetId="2" state="hidden" r:id="rId2"/>')
    const styles = partOf(data, 'xl/styles.xml')
    expect(styles).toContain('formatCode="#,##0.00&quot; €&quot;"')
    expect(styles).toContain('<b/>')
    expect(styles).toContain('rgb="FFE2EFDA"')
    expect(styles).toContain('numFmtId="10"')
    expect(partOf(data, 'xl/worksheets/sheet1.xml')).toContain('<col min="2" max="2" width="30" customWidth="1"/>')
  })

  it('liest gemeinsame Strings, Formelzellen und Namensraumpräfixe (Datei aus Excel oder LibreOffice)', () => {
    const main = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    const data = zipSync({
      'xl/workbook.xml': strToU8(`<workbook ${main}><sheets><sheet name="03_MUS_1Z" sheetId="1" r:id="rId7"/></sheets></workbook>`),
      'xl/_rels/workbook.xml.rels': strToU8('<Relationships><Relationship Id="rId7" Type="t" Target="/xl/worksheets/blatt.xml"/></Relationships>'),
      'xl/sharedStrings.xml': strToU8('<sst><si><t>mittel</t></si><si><r><t>zwei</t></r><r><t xml:space="preserve">seitig</t></r><rPh><t>x</t></rPh></si></sst>'),
      'xl/worksheets/blatt.xml': strToU8(
        '<worksheet><sheetData><row r="9"><c r="C9" t="s"><v>0</v></c><c r="C11" t="s"><v>1</v></c><c r="C7"><f>\'02_Grundgesamtheit\'!$C$51</f><v>0</v></c>' +
          '<c r="C10" s="3"><v>0.7</v></c><c r="C12" t="e"><v>#N/A</v></c><c r="C13" t="str"><f>A1</f><v>a &amp; b</v></c><c r="C14" t="b"><v>1</v></c><c r="C15"/></row></sheetData></worksheet>',
      ),
    })
    const cells = readWorkbook(data).cells('03_MUS_1Z')
    expect(cells.get('C9')?.value).toBe('mittel')
    expect(cells.get('C11')?.value).toBe('zweiseitig')
    expect(cells.get('C7')).toEqual({ value: 0, formula: true, formulaText: "'02_Grundgesamtheit'!$C$51" })
    expect(cells.get('C10')).toMatchObject({ value: 0.7, formula: false })
    expect(cells.get('C12')?.value).toBeNull()
    expect(cells.get('C13')).toMatchObject({ value: 'a & b', formula: true, formulaText: 'A1' })
    expect(cells.get('C14')?.value).toBe(true)
    expect(cells.get('C15')?.value).toBeNull()
  })

  it('lehnt Dateien ab, die keine Arbeitsmappe sind', () => {
    expect(() => readWorkbook(strToU8('kein zip'))).toThrow(WorkbookError)
    expect(() => readWorkbook(zipSync({ 'a.txt': strToU8('x') }))).toThrow(WorkbookError)
  })
})

describe('Ergebnisexport', () => {
  it('Blatt „Ergebnis“ mit Kopfblock, Zeilen je Feld und ausgeblendetem Arbeitsstand', async () => {
    const exported = await exportWorkbook(state, { now })
    expect(exported.fileName).toBe('Stichprobe_03_MUS_1Z_2025_2026_Ergebnis.xlsx')
    const workbook = readWorkbook(exported.data)
    expect(workbook.sheetNames).toEqual(['Ergebnis', WORKSPACE_SHEET])
    const cells = workbook.cells('Ergebnis')
    const column = (letter: string): unknown[] => [...cells.entries()].filter(([address]) => address.startsWith(letter)).map(([, cell]) => cell.value)
    expect(column('A')).toContain('Rechtsgrundlage')
    expect(column('A')).toContain('Die Berechnung bildet die Stichprobenvorlagen 2021–2027 nach. Sie ersetzt nicht die fachliche Würdigung der Prüfbehörde und ist kein Dokument der Europäischen Kommission.')
    expect(column('A')).toContain('Grundlage ist der Arbeitsentwurf der Stichprobenvorlagen 2021–2027, Fassung 4, Stand Oktober 2026. Die Vorlage ist keine amtliche Fassung.')
    expect(column('B')).toContain('Anzuwendender Stichprobenumfang (mind. 30; ggf. begrenzt)')
    expect(column('B').join('\n')).toContain('sha256:')
    expect(column('C')).toEqual(expect.arrayContaining([92, 48500000, 'mittel', 0.7, '✔ TE > AE']))
    expect(column('D')).toEqual(expect.arrayContaining(['Eingabe', 'Verknüpfung', 'Formel', 'Ergebnis', 'Prüfhinweis']))
    expect(column('F')).toContain('C27')
    expect(partOf(exported.data, 'xl/workbook.xml')).toContain(`name="${WORKSPACE_SHEET}" sheetId="2" state="hidden"`)
  })

  it('Rundlauf Export → Öffnen ergibt denselben Arbeitsstand ohne Hinweise', async () => {
    const imported = importWorkbook((await exportWorkbook(state, { now })).data)
    expect(imported.kind).toBe('workspace')
    if (imported.kind !== 'workspace') return
    const opened = await openWorkspace(imported.text)
    expect(opened).toMatchObject({ ok: true, notices: [] })
    expect(opened.ok && opened.state).toEqual(state)
    expect(opened.ok && computeWorkspace(opened.state)).toEqual(computeWorkspace(state))
  })

  it('ein langer Arbeitsstand wird auf mehrere Zellen verteilt und wieder zusammengesetzt', async () => {
    const rows = Array.from({ length: 900 }, (_, index) => ({ C5: `Vorhaben-${index}-${'x'.repeat(40)}`, C6: index + 1, W5: 'Zufallsschicht', W6: 'Variante 1' }))
    const large: WorkspaceState = { ...state, sheets: { ...state.sheets, '17_Unterstichprobe': rows } }
    const exported = await exportWorkbook(large, { now })
    expect(readWorkbook(exported.data).cells(WORKSPACE_SHEET).size).toBeGreaterThan(1)
    const imported = importWorkbook(exported.data)
    const opened = imported.kind === 'workspace' ? await openWorkspace(imported.text) : null
    expect(opened).toMatchObject({ ok: true, notices: [] })
    expect(opened?.ok && opened.state.sheets['17_Unterstichprobe']).toEqual(rows)
  })

  it('Hinweise der Webfassung stehen gekennzeichnet im Export', async () => {
    const hinted: WorkspaceState = { ...state, sheets: { '03_MUS_1Z': { ...sheet03.sample.inputs, C8: 50 } } }
    const cells = readWorkbook((await exportWorkbook(hinted, { now })).data).cells('Ergebnis')
    const values = [...cells.values()].map((cell) => cell.value)
    expect(values).toContain('Hinweis der Webfassung')
    expect(values).toContain('Stichprobenumfang übersteigt die Anzahl der Einheiten der Grundgesamtheit')
  })

  it('ohne gewähltes Verfahren entsteht eine lesbare Datei mit Arbeitsstand', async () => {
    const exported = await exportWorkbook(emptyWorkspace(), { now })
    expect(importWorkbook(exported.data).kind).toBe('workspace')
  })
})

describe('Import der ausgefüllten Vorlage (Gerüst)', () => {
  const cell = (value: number | string) => ({ value })
  function templateRows(values: Record<number, number | string>): ({ value: number | string } | null)[][] {
    return Array.from({ length: 45 }, (_, index) => [null, null, values[index + 1] === undefined ? null : cell(values[index + 1]!)])
  }

  it('übernimmt Eingabezellen der Blätter mit Rechenkern und nennt die befüllten Blätter', () => {
    const data = writeWorkbook([
      { name: '05_MUS_2Z', rows: [[cell('x')]] },
      { name: '03_MUS_1Z', rows: templateRows({ 5: '2025/2026', 7: 48500000, 9: 'mittel', 10: 0.7, 11: 'zweiseitig', 14: 0.02, 22: 2, 23: 'Nein', 24: 'Nein', 27: 999, 29: 'vier' }) },
    ])
    const imported = importWorkbook(data, FOUNDATION_SHEETS)
    expect(imported).toMatchObject({
      kind: 'template',
      sheets: { '03_MUS_1Z': { C5: '2025/2026', C7: 48500000, C9: 'mittel', C10: 0.7, C11: 'zweiseitig', C14: 0.02, C22: 2, C23: 'Nein', C24: 'Nein' } },
      filled: ['03_MUS_1Z'],
      pending: ['05_MUS_2Z'],
      issues: [{ sheet: '03_MUS_1Z', cell: 'C29', found: 'vier', reason: 'not-a-number', used: null }],
    })
    expect(imported.kind === 'template' && imported.sheets['03_MUS_1Z']).not.toHaveProperty('C27')
  })

  it('ein Blatt nur mit den Vorgaben der Vorlage gilt als leer', () => {
    const imported = importWorkbook(writeWorkbook([{ name: '03_MUS_1Z', rows: templateRows({ 11: 'zweiseitig', 14: 0.02, 23: 'Nein', 24: 'Nein' }) }]))
    expect(imported).toMatchObject({ kind: 'template', filled: [], pending: [] })
  })

  it('fremde Arbeitsmappen werden als unbekannt gemeldet', () => {
    expect(importWorkbook(writeWorkbook([{ name: 'Tabelle1', rows: [[cell(1)]] }]))).toEqual({ kind: 'unknown' })
  })
})

/** Arbeitsmappe aus rohem XML, wie sie Excel oder LibreOffice schreiben (und wie sie beschädigt sein kann). */
function rawWorkbook(sheetXml: string, name = '03_MUS_1Z', shared = ''): Uint8Array {
  return zipSync({
    'xl/workbook.xml': strToU8(`<workbook><sheets><sheet name="${name}" sheetId="1" r:id="rId1"/></sheets></workbook>`),
    'xl/_rels/workbook.xml.rels': strToU8('<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>'),
    ...(shared ? { 'xl/sharedStrings.xml': strToU8(shared) } : {}),
    'xl/worksheets/sheet1.xml': strToU8(sheetXml),
  })
}
const text = (cell: string, value: string): string => `<c r="${cell}" t="inlineStr"><is><t>${value}</t></is></c>`
const number = (cell: string, value: number | string): string => `<c r="${cell}"><v>${value}</v></c>`

describe('Leser gegen fremde und beschädigte Mappen', () => {
  it('leere und selbstschließende Einträge verschieben die gemeinsamen Zeichenketten nicht', () => {
    const shared = '<sst><si><t>eins</t></si><si/><si><r><t/></r><r><rPr><b/></rPr><t>abc</t></r></si><si><t>vier</t></si></sst>'
    const cells = readWorkbook(rawWorkbook('<worksheet><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="A2" t="s"><v>1</v></c><c r="A3" t="s"><v>2</v></c><c r="A4" t="s"><v>3</v></c></row></sheetData></worksheet>', 'T', shared)).cells('T')
    expect(['A1', 'A2', 'A3', 'A4'].map((cell) => cells.get(cell)?.value)).toEqual(['eins', '', 'abc', 'vier'])
  })

  it('ungültige Zeichenreferenzen, unbekannte Entitäten und Excel-Maskierungen', () => {
    const xml = `<worksheet><sheetData><row r="1">${text('A1', 'a&#x110000;b&#xD800;c')}${text('B1', '&constructor; &amp; &unbekannt;')}${text('C1', 'Zeile_x000D_Ende _x005F_x0041_')}</row></sheetData></worksheet>`
    const cells = readWorkbook(rawWorkbook(xml, 'T')).cells('T')
    expect(cells.get('A1')?.value).toBe('a\uFFFDb\uFFFDc')
    expect(cells.get('B1')?.value).toBe('&constructor; & &unbekannt;')
    expect(cells.get('C1')?.value).toBe('Zeile\rEnde _x0041_')
  })

  it('leere und nicht dezimale Werte sind keine Zahlen; einfache Anführungszeichen und Zellen ohne Adresse werden gelesen', () => {
    const xml = "<worksheet><sheetData><row r='2'><c r='A2'><v></v></c><c r='B2'><v>0x10</v></c><c r='C2'><v> 12.5 </v></c><c><v>7</v></c><c t='b'><v>1</v></c></row><row><c><v>9</v></c></row></sheetData></worksheet>"
    const cells = readWorkbook(rawWorkbook(xml, 'T')).cells('T')
    expect([cells.get('A2')?.value, cells.get('B2')?.value, cells.get('C2')?.value, cells.get('D2')?.value, cells.get('E2')?.value, cells.get('A3')?.value]).toEqual([null, null, 12.5, 7, true, 9])
  })

  it('nicht geschlossene Elemente kosten lineare Zeit', () => {
    const open = (count: number): string => `<worksheet><sheetData><row r="1">${'<c r="A1" t="inlineStr"><is><t>'.repeat(count)}`
    const measure = (count: number): number => {
      const data = rawWorkbook(open(count), 'T', `<sst>${'<si><t>'.repeat(count)}`)
      const start = performance.now()
      expect(readWorkbook(data).cells('T').size).toBe(1)
      return performance.now() - start
    }
    measure(2000)
    const small = measure(40000)
    const large = measure(160000)
    expect(large).toBeLessThan(Math.max(400, small * 12))
    expect(large).toBeLessThan(3000)
  })

  it('eine beschädigte Mappe ergibt einen Lesefehler, keinen anderen Fehler', () => {
    const broken = zipSync({ 'xl/workbook.xml': strToU8('<workbook>'), 'xl/_rels/workbook.xml.rels': strToU8('<x') })
    expect(readWorkbook(broken).sheetNames).toEqual([])
    expect(() => importWorkbook(strToU8('PK\u0003\u0004kaputt'))).toThrow(WorkbookError)
  })
})

describe('Schreiber: Randfälle des eingebetteten Arbeitsstands', () => {
  it('Zeichen außerhalb der Grundebene auf der Stückgrenze und Texte der Form _x0041_ überstehen den Rundlauf', async () => {
    for (const filler of [29990, 29995, 29999, 30000, 30001]) {
      const programme = `${'a'.repeat(filler)}😀𝜎_x0041_ _x000D_ Prüfbehörde`
      const tricky: WorkspaceState = { ...state, sheets: { '03_MUS_1Z': { ...sheet03.sample.inputs, C4: programme.slice(0, 1990) }, '17_Unterstichprobe': [{ C5: programme.slice(filler - 1000, filler + 40) }] } }
      const padded: WorkspaceState = { ...tricky, header: { ...tricky.header, programm: 'x'.repeat(filler % 1900) + '😀𝜎' } }
      const exported = await exportWorkbook(padded, { now })
      const imported = importWorkbook(exported.data)
      const opened = imported.kind === 'workspace' ? await openWorkspace(imported.text) : null
      expect(opened, String(filler)).toMatchObject({ ok: true, notices: [] })
      expect(opened?.ok && opened.state).toEqual(padded)
    }
  })

  it('der eingebettete Arbeitsstand besteht nur aus ASCII-Zeichen', async () => {
    const exported = await exportWorkbook({ ...state, header: { ...state.header, programm: 'Prüfbehörde 😀' } }, { now })
    const imported = importWorkbook(exported.data)
    expect(imported.kind === 'workspace' && /^[\x20-\x7e]*$/.test(imported.text)).toBe(true)
    expect(imported.kind === 'workspace' && (JSON.parse(imported.text) as { kopf: { programm: string } }).kopf.programm).toBe('Prüfbehörde 😀')
  })
})

describe('Import der ausgefüllten Vorlage: nichts wird stillschweigend verworfen', () => {
  const base = `${number('C7', 48500000)}${number('C8', 420)}${number('C10', 0.7)}${number('C14', 0.02)}${number('C17', 0.007)}${number('C20', 0.12)}${number('C22', 2)}`
  const wrap = (cells: string): Uint8Array => rawWorkbook(`<worksheet><sheetData><row r="1">${cells}</row></sheetData></worksheet>`)
  const issuesOf = (cells: string) => {
    const imported = importWorkbook(wrap(cells))
    if (imported.kind !== 'template') throw new Error('keine Vorlage')
    return { inputs: imported.sheets['03_MUS_1Z'] as Record<string, unknown>, issues: imported.issues.map((issue) => [issue.cell, issue.found, issue.reason, issue.used]) }
  }

  it('Auswahlwerte in anderer Schreibweise werden dem Listeneintrag zugeordnet und gemeldet', () => {
    const { inputs, issues } = issuesOf(`${base}${text('C9', 'Mittel')}${text('C11', ' Einseitig ')}${text('C23', 'NEIN')}${text('C24', 'ja')}${text('C10', '70 %')}`)
    expect(inputs).toMatchObject({ C9: 'mittel', C11: 'einseitig', C23: 'Nein', C24: 'Ja', C10: 0.7 })
    expect(issues).toEqual(expect.arrayContaining([
      ['C9', 'Mittel', 'normalized', 'mittel'],
      ['C11', ' Einseitig ', 'normalized', 'einseitig'],
      ['C23', 'NEIN', 'normalized', 'Nein'],
      ['C24', 'ja', 'normalized', 'Ja'],
      ['C10', '70 %', 'normalized', 0.7],
    ]))
  })

  it('Zahlen als Text werden gelesen, Unlesbares wird mit Grund genannt', () => {
    const { inputs, issues } = issuesOf(`${base}${text('C20', '0,12')}${text('C38', 'k. A.')}${text('C9', 'sehr hoch')}<c r="C29" t="b"><v>1</v></c>${number('C5', 46203)}${text('C30', '6.200.000,50')}`)
    expect(inputs).toMatchObject({ C20: 0.12, C5: '46203', C30: 6200000.5 })
    expect(inputs).not.toHaveProperty('C38')
    expect(inputs).not.toHaveProperty('C9')
    expect(issues).toEqual(expect.arrayContaining([
      ['C20', '0,12', 'number-from-text', 0.12],
      ['C38', 'k. A.', 'not-a-number', null],
      ['C9', 'sehr hoch', 'not-in-list', null],
      ['C29', 'true', 'unsupported', null],
      ['C5', '46203', 'number-as-text', '46203'],
      ['C30', '6.200.000,50', 'number-from-text', 6200000.5],
    ]))
  })

  it('eigene Formeln: berechneter Wert wird übernommen und gemeldet; die unberührte Verknüpfung bleibt Verknüpfung', () => {
    const own = issuesOf(`${base.replace(number('C7', 48500000), '')}<c r="C7"><f>40000000+8500000</f><v>48500000</v></c><c r="C8"><f>'02_Grundgesamtheit'!$C$52</f><v>0</v></c><c r="C30"><f>SUM(A1:A2)</f><v>6200000</v></c>`)
    expect(own.inputs).toMatchObject({ C7: 48500000, C30: 6200000 })
    expect(own.inputs).not.toHaveProperty('C8')
    expect(own.issues).toEqual([
      ['C7', '=40000000+8500000', 'formula-value', 48500000],
      ['C30', '=SUM(A1:A2)', 'formula-value', 6200000],
    ])
  })

  it('Gegenprobe: Ergebnisse der Webfassung gegen die Rechenwerte der Mappe', () => {
    const filled = `${base}${text('C9', 'mittel')}${text('C11', 'zweiseitig')}${text('C23', 'Nein')}${text('C24', 'Nein')}`
    const imported = importWorkbook(wrap(`${filled}${number('C27', 92)}${number('C21', 92)}${number('C16', 970000)}${text('C19', '✔ TE &gt; AE')}`))
    if (imported.kind !== 'template') throw new Error('keine Vorlage')
    expect(imported.cached['03_MUS_1Z']).toMatchObject({ C27: 92, C16: 970000, C19: '✔ TE > AE', C42: null })
    const candidate: WorkspaceState = { ...emptyWorkspace(), activeMethod: '03_MUS_1Z', sheets: imported.sheets }
    expect(compareWithWorkbook(candidate, imported.cached).filter((entry) => ['C27', 'C21', 'C16', 'C19'].includes(entry.cell))).toEqual([])
    const wrong = importWorkbook(wrap(`${filled}${number('C27', 30)}`))
    if (wrong.kind !== 'template') throw new Error('keine Vorlage')
    expect(compareWithWorkbook({ ...candidate, sheets: wrong.sheets }, wrong.cached)).toContainEqual({ sheet: '03_MUS_1Z', cell: 'C27', label: 'Anzuwendender Stichprobenumfang (mind. 30; ggf. begrenzt)', workbook: 30, computed: 92 })
  })
})

/**
 * Nur lokal: von LibreOffice gespeicherte, ausgefüllte Originalvorlagen (nicht im Repository).
 * `AUDITCORE_SAMPLING_FILLED_TEMPLATES=/pfad/mit/tpl_*.xlsx npm test`
 */
const filledDirectory = process.env.AUDITCORE_SAMPLING_FILLED_TEMPLATES ?? ''
describe.skipIf(!filledDirectory || !existsSync(filledDirectory))('Import ausgefüllter Originalvorlagen (lokal)', () => {
  const read = (name: string) => {
    const imported = importWorkbook(new Uint8Array(readFileSync(join(filledDirectory, name))))
    if (imported.kind !== 'template') throw new Error(`${name}: keine Vorlage`)
    const candidate: WorkspaceState = { ...emptyWorkspace(), activeMethod: '03_MUS_1Z', sheets: imported.sheets }
    return { imported, differences: compareWithWorkbook(candidate, { '03_MUS_1Z': imported.cached['03_MUS_1Z'] ?? {} }) }
  }

  it('Standardbelegung: alle Eingaben, keine Meldung, Ergebnisse wie in der Mappe', () => {
    const { imported, differences } = read('tpl_standard.xlsx')
    expect(imported.filled).toContain('03_MUS_1Z')
    expect(imported.issues.filter((issue) => issue.sheet === '03_MUS_1Z')).toEqual([])
    expect(differences).toEqual([])
  })

  it('abweichende Schreibweise: zugeordnet, gemeldet, Ergebnisse wie in der Mappe', () => {
    const { imported, differences } = read('tpl_schreibweise.xlsx')
    expect(imported.issues.filter((issue) => issue.reason === 'normalized').map((issue) => issue.cell).sort()).toEqual(['C11', 'C23', 'C24', 'C9'])
    expect(differences).toEqual([])
  })

  it('Zahl als Text und eigene Formel: gelesen und gemeldet', () => {
    const texts = read('tpl_text_in_zahl.xlsx')
    expect(texts.imported.issues.map((issue) => [issue.cell, issue.reason])).toEqual(expect.arrayContaining([['C20', 'number-from-text'], ['C38', 'not-a-number']]))
    const formula = read('tpl_formel_in_eingabe.xlsx')
    expect(formula.imported.issues.map((issue) => [issue.cell, issue.reason])).toContainEqual(['C7', 'formula-value'])
    expect(formula.differences).toEqual([])
  })
})
