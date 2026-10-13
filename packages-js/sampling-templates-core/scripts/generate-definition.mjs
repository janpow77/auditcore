#!/usr/bin/env node
/**
 * Erzeugt aus der Zellbeschreibung der Vorlage (`vorlage_zellen.json`) den ersten
 * Entwurf einer Methodendefinition bzw. das Inventar der Excel-Funktionen.
 *
 *   node packages-js/sampling-templates-core/scripts/generate-definition.mjs 04_MUS_1Z_S > entwurf.ts
 *   node packages-js/sampling-templates-core/scripts/generate-definition.mjs --inventory
 *
 * Die Zellbeschreibung ist nicht Teil des Repositorys. Sie wird im Verzeichnis
 * `AUDITCORE_SAMPLING_TEMPLATES_DIR` gesucht, sonst in `.vorlage/` des Pakets
 * (von git ausgeschlossen). Der Entwurf wird von Hand geprüft und als
 * `src/sheets/<Blatt>/definition.ts` abgelegt: Aliasnamen vergeben, eingebettete
 * Formeln nach `formula` ziehen, Auswahllisten und Ergebnisspalte ergänzen.
 */
import { existsSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import process from 'node:process'
import { fileURLToPath } from 'node:url'

const PACKAGE = join(dirname(fileURLToPath(import.meta.url)), '..')
const DIRECTORY = process.env.AUDITCORE_SAMPLING_TEMPLATES_DIR ?? join(PACKAGE, '.vorlage')
const LISTS = {
  '01_Parameter!$B$24:$B$26': 'reliability',
  '01_Parameter!$B$5:$B$9': 'confidence',
  '01_Parameter!$C$24:$C$25': 'testType',
  '01_Parameter!$D$24:$D$25': 'yesNo',
  '01_Parameter!$E$24:$E$27': 'category',
  '01_Parameter!$F$24:$F$27': 'recalculation',
  '01_Parameter!$G$24:$G$26': 'article80',
  '01_Parameter!$H$24:$H$25': 'negativePopulation',
  '01_Parameter!$I$24:$I$37': 'methodSheets',
}
const KINDS = { eingabe: 'input', verknuepfung: 'link', formel: 'formula', ergebnis: 'result' }
/** Spalten der Ergebnisübersicht für Blatt 18; sie gehören nicht ins Formular. */
const SUMMARY_COLUMNS = new Set(['M', 'N'])

function loadCells() {
  const path = join(DIRECTORY, 'vorlage_zellen.json')
  if (!existsSync(path)) {
    process.stderr.write(`vorlage_zellen.json fehlt in ${DIRECTORY}. AUDITCORE_SAMPLING_TEMPLATES_DIR setzen oder die Datei nach .vorlage/ kopieren.\n`)
    process.exit(1)
  }
  return JSON.parse(readFileSync(path, 'utf8'))
}

const isFormula = (cell) => typeof cell.wert === 'string' && cell.wert.startsWith('=')
const split = (address) => {
  const [, column, row] = /^([A-Z]+)(\d+)$/.exec(address)
  return { column, row: Number(row) }
}
const columnOrder = (a, b) => a.length - b.length || a.localeCompare(b)

/** Vorkommende Excel-Funktionen über alle Blätter als Markdown-Tabelle. */
function inventory(workbook) {
  const counts = new Map()
  for (const cells of Object.values(workbook)) {
    for (const cell of cells.filter(isFormula)) {
      for (const [, name] of cell.wert.matchAll(/([A-Z][A-Z0-9.]*)\(/g)) counts.set(name, (counts.get(name) ?? 0) + 1)
    }
  }
  const formulas = Object.values(workbook).flat().filter(isFormula).length
  const rows = [...counts].sort((a, b) => b[1] - a[1]).map(([name, count]) => `| \`${name}\` | ${count} |`)
  return [`Formeln gesamt: ${formulas}`, '', '| Funktion | Vorkommen |', '|---|---:|', ...rows].join('\n')
}

function typeOf(cell) {
  if (isFormula(cell) && /[✔✖⚠]/.test(cell.wert)) return 'check'
  if (cell.auswahlliste) return 'choice'
  const format = cell.format ?? ''
  if (format.includes('€')) return 'amount'
  if (format.includes('%')) return 'percent'
  if (/0\.0/.test(format)) return 'decimal'
  if (format.includes('#,##0')) return 'integer'
  if (cell.wert === 'Ja' || cell.wert === 'Nein') return 'choice'
  return format === '@' || !format ? 'text' : 'decimal'
}

/** Schichtzeile: Zellen in den Spalten D–J; eine Zelle in Spalte C daneben ist die Summe der Zeile. */
function strataOf(row, values) {
  const strata = values.filter((column) => column !== 'C')
  return strata.length > 1 ? { first: strata[0], total: values.includes('C') ? row.C.zelle : undefined } : null
}

function fieldOf(row, values, label, hint) {
  const strata = strataOf(row, values)
  const cell = row[strata ? strata.first : values[0]]
  const field = { cell: cell.zelle, alias: `cell${cell.zelle}`, kind: KINDS[cell.art], type: typeOf(cell), label }
  if (hint) field.hint = hint
  if (cell.format) field.format = cell.format
  if (cell.auswahlliste) field.list = LISTS[cell.auswahlliste] ?? `UNBEKANNT ${cell.auswahlliste}`
  else if (field.type === 'choice') field.list = 'yesNo'
  if (cell.art === 'eingabe' && cell.wert !== null) field.default = cell.wert
  const link = cell.art === 'verknuepfung' ? /^='?([^'!]+)'?!\$?([A-Z]+)\$?(\d+)$/.exec(cell.wert) : null
  if (link) field.link = { sheet: link[1], cell: `${link[2]}${link[3]}` }
  if (strata) field.columns = 'STRATA_COLUMNS'
  if (strata?.total) field.total = strata.total
  return field
}

/** Zeilen des Blatts zu Abschnitten und Feldern ordnen. */
function draft(sheet, cells) {
  const rows = new Map()
  for (const cell of cells) {
    const { column, row } = split(cell.zelle)
    if (SUMMARY_COLUMNS.has(column)) continue
    rows.set(row, { ...(rows.get(row) ?? {}), [column]: cell })
  }
  const text = (row, column) => (row[column]?.art === 'text' ? String(row[column].wert) : '')
  const sections = []
  let title = ''
  let legalBasis = ''
  for (const number of [...rows.keys()].sort((a, b) => a - b)) {
    const row = rows.get(number)
    const heading = /^([A-Z])\. (.*?)(?: \(([^()]*)\))?$/.exec(text(row, 'A'))
    if (heading) sections.push({ id: heading[1], title: heading[2], ...(heading[3] ? { reference: heading[3] } : {}), fields: [] })
    else if (number === 1) title = text(row, 'A')
    else if (number === 2) legalBasis = text(row, 'A')
    const values = Object.keys(row).filter((column) => column !== 'A' && column !== 'B' && row[column].art !== 'text').sort(columnOrder)
    if (values.length === 0 || sections.length === 0) continue
    const hintColumn = Object.keys(row).filter((column) => row[column].art === 'text' && columnOrder(column, values.at(-1)) > 0).sort(columnOrder)[0]
    sections.at(-1).fields.push(fieldOf(row, values, text(row, 'B'), hintColumn ? text(row, hintColumn) : ''))
  }
  const [, number, name] = /^(\S+)\s+(.*)$/.exec(title) ?? [null, sheet.split('_')[0], title]
  return { sheet, number, title: name, shortTitle: 'KURZNAME', legalBasis, sections, summary: { primary: { cell: 'ZELLE', label: 'BEZEICHNUNG', unit: 'Einheiten' }, rows: [] } }
}

/** Quelltext der Definition: je Feld eine Zeile, damit sich der Entwurf gut prüfen lässt. */
function render(definition) {
  const { sections, summary, ...head } = definition
  const lines = Object.entries(head).map(([key, value]) => `  ${key}: ${JSON.stringify(value)},`)
  const blocks = sections.map(({ fields, ...section }) => {
    const rows = fields.map((field) => `      ${JSON.stringify(field)},`).join('\n')
    return `    {\n      ...${JSON.stringify(section)},\n      fields: [\n${rows.replace(/^ {6}/gm, '        ')}\n      ],\n    },`
  })
  return `{\n${lines.join('\n')}\n  sections: [\n${blocks.join('\n')}\n  ],\n  summary: ${JSON.stringify(summary)},\n}`
}

const print = (text) => process.stdout.write(`${text}\n`)

function main() {
  const [argument] = process.argv.slice(2)
  const workbook = loadCells()
  if (argument === '--inventory') return print(inventory(workbook))
  if (!argument || !workbook[argument]) {
    process.stderr.write(`Aufruf: generate-definition.mjs <Blatt> | --inventory\nBlätter: ${Object.keys(workbook).join(', ')}\n`)
    process.exit(1)
  }
  const definition = draft(argument, workbook[argument])
  print('/** ENTWURF – erzeugt aus der Zellbeschreibung der Vorlage; von Hand prüfen (docs/blatt-ergaenzen.md). */')
  print("import type { MethodDefinition } from '../../model/definition'\n")
  print(`export const definition: MethodDefinition = ${render(definition)}`)
}

main()
