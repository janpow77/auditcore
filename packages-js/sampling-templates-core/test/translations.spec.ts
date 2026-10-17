/**
 * Englische Arbeitsübersetzung: Vollständigkeit je Blatt und einheitliche
 * Fachbegriffe nach der englischen Fassung der Delegierten Verordnung (EU)
 * 2023/67. Geprüft wird, was die Anzeige braucht: Bezeichnungen, Texte des
 * Rechenkerns aus den Golden-Fällen, Hinweise der Webfassung, Meldungen der
 * Oberfläche. Ausnahmen stehen als ausdrückliche Listen am Anfang.
 */
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { CATALOG_TEXTS } from '../src/catalog/catalog'
import { samplingTemplatesMessages } from '../src/i18n/messages'
import { fieldsOf, findField } from '../src/model/definition'
import type { AvailableSheet } from '../src/model/sheet'
import type { SheetTexts } from '../src/model/texts'
import type { CellMap } from '../src/model/types'
import { SHARED_TEXTS } from '../src/sheets/01_Parameter/index'
import { REPORT_LAYOUT } from '../src/sheets/20_Druck_KOM/layout'
import { SHEETS, availableSheets } from '../src/sheets/registry'
import { LEGACY_NOTICE } from '../src/sheets/shared/legacy'
import { computeWorkspace, contextFor } from '../src/workspace/compute'
import { emptyWorkspace, type WorkspaceState } from '../src/workspace/types'
import { caseState, caseWorkspace, loadGolden } from './golden'
import { officialWording } from '../src/model/terms'

const sheets = availableSheets()
const SHEET_IDS = new Set(SHEETS.map((sheet) => sheet.id))

/** Altvorlagen von 2017: Ihre deutsche Seite ist der englische Wortlaut der Vorlage; übersetzt sind nur Titel, Hinweis der Vorlage und Hinweise der Webfassung. */
const isLegacy = (sheet: AvailableSheet): boolean => sheet.id.startsWith('X')

/** Vermerke im Kopf jeder Übersetzungsdatei. */
const NOTICE = 'nicht amtliche Arbeitsübersetzung; maßgeblich ist der deutsche Wortlaut der Vorlage'
const TERMS_NOTICE = 'Fachbegriffe nach der englischen Fassung der Delegierten Verordnung (EU) 2023/67'

/**
 * Texte des Rechenkerns, die bewusst nicht übersetzt werden:
 * Zahlen und Daten, Blattnamen der Vorlage (Eigennamen) und die zusammengesetzte
 * Kopfzeile des Blatts 20 mit dem festen Programmnamen der Vorlage.
 */
const UNTRANSLATED: readonly { reason: string; matches: (text: string) => boolean }[] = [
  { reason: 'Datum', matches: (text) => /^\d{2}\.\d{2}\.\d{4}$/.test(text) },
  { reason: 'Blattname der Vorlage', matches: (text) => SHEET_IDS.has(text) },
  { reason: 'Kopfzeile Blatt 20 (Zelle A6): aus Angaben zusammengesetzt; die Berichtsansicht bildet sie in der Sprache des Blatts', matches: (text) => text.includes('CCI ') && text.includes(' · Geschäftsjahr ') },
]

/** Formeln ohne Wörter (nur Formelzeichen) brauchen keine Übersetzung. */
const hasWords = (text: string): boolean => /[a-zäöüß]{3,}/.test(text)

/** Deutsche Wortlaute, die die Vorlage in zwei Bedeutungen verwendet (Blatt 20: „Stand“ als Datum und als Bearbeitungsstand). */
const AMBIGUOUS_GERMAN = new Set(['Stand'])

/**
 * Alte Varianten der vereinheitlichten Fachbegriffe; rechts der Begriff der
 * Verordnung (Fundstelle). „cut-off value“ kennt die Verordnung nicht; die
 * Übersetzung verwendet ihn einheitlich für den Grenzwert der Vorlage.
 */
const OLD_VARIANTS: readonly (readonly [pattern: RegExp, term: string])[] = [
  [/\bproject(ed|ion|ing)\b/i, 'extrapolated error / extrapolation (Art. 2(19), Art. 8)'],
  [/\bsampling interval\b/i, 'interval of selection (Art. 5(2))'],
  [/\b(high|low)-value\b/i, 'high value / low value units (Art. 5(2))'],
  [/\b(two|one)-sided\b/i, 'bilateral / unilateral testing (Art. 2(17), (18))'],
  [/\blimited sample size\b|\blimited:/i, 'capped sample size (Art. 5(7))'],
  [/\bsub-sampl/i, 'subsampling / subsample (Art. 2(12), Art. 7)'],
  [/\bnot stratified\b|\bunstratified\b/i, 'non-stratified (Annex II)'],
  [/\bpopulation to be audited\b/i, 'audit population (Art. 2(16), Art. 3)'],
  [/\bprecision of the sample\b/i, 'sampling precision (Art. 2(22))'],
  [/\bmedium\b/i, 'average (Annex I point 2)'],
  [/\bcut-off(?! (value|date)\b)/i, 'cut-off value (nicht in der Verordnung; einheitlich)'],
  [/\bstandard-deviation\b/i, 'standard deviation (Annex I point 4)'],
  [/\bexpected error\b/i, 'anticipated error (Annex I point 4)'],
  [/\b(sampling|top) stratum\b/i, 'random stratum / exhaustive stratum (Art. 2(10), (11))'],
  [/\bsystematic errors?\b/i, 'systemic errors (Art. 2(20))'],
  [/\bfinancial year\b/i, 'accounting year (Art. 3(1))'],
  [/\bready-to-use\b/i, 'off-the-shelf sampling methodology (Art. 1)'],
  [/\bat most 2 %/i, 'maximum 2 % (Annex I point 1, Annex II)'],
]

/** Englische Texte, die eine alte Variante bewusst enthalten dürfen: keine. */
const OLD_VARIANT_ALLOWED: ReadonlySet<string> = new Set()

const source = (path: string): string => readFileSync(fileURLToPath(new URL(`../src/${path}`, import.meta.url)), 'utf8')
const textsOf = (sheet: AvailableSheet): SheetTexts => sheet.translations?.en ?? {}
const translated = (texts: SheetTexts, text: string): boolean => text in (texts.values ?? {}) || text in SHARED_TEXTS.en

/** Alle englischen Texte einer Blattübersetzung. */
function englishTexts(texts: SheetTexts): string[] {
  const fields = Object.values(texts.fields ?? {}).flatMap((field) => [field.label, field.hint, field.formula, field.interpretation])
  const sections = Object.values(texts.sections ?? {}).flatMap((section) => [section.title, section.reference])
  const summary = [texts.summary?.primary, texts.summary?.unit, ...Object.values(texts.summary?.rows ?? {})]
  return [texts.title, texts.shortTitle, texts.legalBasis, ...sections, ...fields, ...summary, ...Object.values(texts.values ?? {}), ...Object.values(texts.webHints ?? {})].filter((text): text is string => typeof text === 'string')
}

/** Deutsch-englische Textpaare eines Blatts: Bezeichnungen, Fundstellen, Abschnitte, Ergebnisspalte, Werte. */
function pairsOf(sheet: AvailableSheet): [german: string, english: string | undefined][] {
  const texts = textsOf(sheet)
  const definition = sheet.definition
  const fields = fieldsOf(definition).flatMap((field): [string | undefined, string | undefined][] => {
    const own = texts.fields?.[field.cell]
    return [[field.label, own?.label], [field.hint, own?.hint], [field.formula, own?.formula], [field.interpretation, own?.interpretation]]
  })
  const sections = definition.sections.flatMap((section): [string | undefined, string | undefined][] => [[section.title, texts.sections?.[section.id]?.title], [section.reference, texts.sections?.[section.id]?.reference]])
  const rows = definition.summary.rows.map((row): [string, string | undefined] => [row.label, texts.summary?.rows?.[row.cell]])
  const all: [string | undefined, string | undefined][] = [[definition.title, texts.title], [definition.shortTitle, texts.shortTitle], [definition.legalBasis, texts.legalBasis], ...sections, ...fields, [definition.summary.primary.label, texts.summary?.primary], ...rows, ...Object.entries(texts.values ?? {})]
  return all.filter((pair): pair is [string, string | undefined] => typeof pair[0] === 'string' && pair[0] !== '')
}

/** Methodenblätter der Auswahlliste der Vorlage (Blätter 03 bis 16). */
const METHOD_SHEETS = new Set(sheets.filter((sheet) => /^(0[3-9]|1[0-6])_/.test(sheet.id)).map((sheet) => sheet.id))

/** Arbeitsstand mit den Beispielwerten aller Blätter bzw. als leeres Formular; ohne eigenes Verfahren ist Blatt 03 aktiv. */
function stateOf(sheet: AvailableSheet, filled: boolean): WorkspaceState {
  const inputs = Object.fromEntries(sheets.map((other) => [other.id, other.definition.layout === 'list' ? [] : filled ? other.sample.inputs : {}]))
  const isMethod = METHOD_SHEETS.has(sheet.id) || isLegacy(sheet)
  return { ...emptyWorkspace(), activeMethod: filled ? (isMethod ? sheet.id : '03_MUS_1Z') : null, sheets: inputs }
}

/** Kennungen der Hinweise der Webfassung, die das Blatt im Arbeitsstand liefert. */
function hintIds(sheet: AvailableSheet, state: WorkspaceState, results: Readonly<Record<string, CellMap>>): string[] {
  const own = state.sheets[sheet.id]
  const inputs = (Array.isArray(own) ? {} : (own ?? {})) as CellMap
  return (sheet.webHints?.(inputs, results[sheet.id] ?? {}, contextFor(sheet.id, state, results)) ?? []).map((hint) => hint.id)
}

describe('Englische Arbeitsübersetzung der Blätter', () => {
  for (const sheet of sheets) {
    const texts = textsOf(sheet)
    const definition = sheet.definition

    it(`${sheet.id}: es gibt eine Übersetzung mit Titel, Kurztitel, Rechtsgrundlage und Vermerk`, () => {
      expect(sheet.translations?.en).toBeDefined()
      expect([texts.title, texts.shortTitle].every((text) => typeof text === 'string' && text !== '')).toBe(true)
      if (definition.legalBasis) expect(texts.legalBasis).toBeTruthy()
      const head = source(`sheets/${sheet.id}/texts.en.ts`)
      expect(head).toContain(NOTICE)
      expect(head).toContain(TERMS_NOTICE)
    })

    it(`${sheet.id}: Felder, Abschnitte und Ergebnisspalte haben englische Texte`, () => {
      if (isLegacy(sheet)) {
        // Bezeichnungen der Vorlage von 2017 sind englisch; übersetzt ist nur die Hinweiszeile der Vorlage.
        const notice = fieldsOf(definition).filter((field) => !/^[\x20-\x7e–·σΣ√²≤≥×−]*$/.test(field.label))
        expect(notice.filter((field) => !texts.fields?.[field.cell]?.label).map((field) => field.cell)).toEqual([])
        expect(texts.values?.[LEGACY_NOTICE]).toBeTruthy()
        return
      }
      const fields = fieldsOf(definition)
      expect(fields.filter((field) => !texts.fields?.[field.cell]?.label).map((field) => field.cell)).toEqual([])
      expect(fields.filter((field) => field.hint && !texts.fields?.[field.cell]?.hint).map((field) => field.cell)).toEqual([])
      expect(fields.filter((field) => field.interpretation && !texts.fields?.[field.cell]?.interpretation).map((field) => field.cell)).toEqual([])
      expect(fields.filter((field) => field.formula && hasWords(field.formula) && !texts.fields?.[field.cell]?.formula).map((field) => field.cell)).toEqual([])
      expect(definition.sections.filter((section) => !texts.sections?.[section.id]?.title || (section.reference && !texts.sections[section.id]?.reference)).map((section) => section.id)).toEqual([])
      expect(texts.summary?.primary).toBeTruthy()
      expect(definition.summary.rows.filter((row) => !texts.summary?.rows?.[row.cell]).map((row) => row.cell)).toEqual([])
      // Übersetzt sind nur Zellen, die es im Blatt gibt.
      expect(Object.keys(texts.fields ?? {}).filter((cell) => !findField(definition, cell))).toEqual([])
    })

    it(`${sheet.id}: jeder Text des Rechenkerns aus den Golden-Fällen hat eine Übersetzung`, () => {
      const values = loadGolden(sheet.id).flatMap((golden) => Object.entries(golden.erwartet))
      // Fehlerwerte von Excel (`#DIV/0!`) zeigt die Webfassung nicht (Blatt 20 E20–E27, `adapted`); sie sind kein Text des Rechenkerns.
      const strings = new Set(values.filter(([reference, value]) => reference.startsWith(`${sheet.id}!`) && typeof value === 'string' && value !== '' && !value.startsWith('#')).map(([, value]) => officialWording(String(value))))
      expect([...strings].filter((text) => !translated(texts, text) && !UNTRANSLATED.some((entry) => entry.matches(text)))).toEqual([])
    })

    it(`${sheet.id}: jeder Hinweis der Webfassung hat eine Übersetzung (Beispielwerte, leeres Formular, Golden-Fälle)`, () => {
      const ids = new Set<string>()
      for (const filled of [true, false]) {
        const state = stateOf(sheet, filled)
        for (const id of hintIds(sheet, state, computeWorkspace(state))) ids.add(id)
      }
      if (definition.layout !== 'list') for (const golden of loadGolden(sheet.id)) for (const id of hintIds(sheet, caseState(sheet, golden), caseWorkspace(sheet, golden))) ids.add(id)
      expect([...ids].filter((id) => !texts.webHints?.[id])).toEqual([])
    }, 240_000)
  }

  it('Blatt 20: jeder Text der Seitenaufteilung und der Zahlenformate hat eine Übersetzung', () => {
    const report = sheets.find((sheet) => sheet.id === '20_Druck_KOM') as AvailableSheet
    const tables = REPORT_LAYOUT.sections.flatMap((section) => section.blocks.flatMap((block) => (block.kind === 'table' ? [...block.columns, ...block.rows.map((row) => row.label), block.foot?.label] : [])))
    const formats = fieldsOf(report.definition).flatMap((field) => [/^"([^"]*)"/.exec(field.format ?? '')?.[1], /;"([^"]*)"$/.exec(field.format ?? '')?.[1]])
    const layout = [...REPORT_LAYOUT.cofinanced, REPORT_LAYOUT.title, REPORT_LAYOUT.controls.title, REPORT_LAYOUT.controls.note, 'Geschäftsjahr', 'vorläufig', 'endgültig', ...REPORT_LAYOUT.sections.map((section) => section.title), ...tables, ...formats]
    const open = layout.filter((text): text is string => typeof text === 'string' && text !== '').filter((text) => !translated(textsOf(report), text))
    // „FÖPG“ ist ein Kürzel der Vorlage ohne englische Entsprechung.
    expect(open).toEqual(['FÖPG'])
  })
})

describe('Einheitliche Fachbegriffe', () => {
  const catalog = CATALOG_TEXTS.en
  const catalogTexts = [...Object.values(catalog.families), ...Object.values(catalog.variants)].flatMap((entry) => Object.values(entry)).concat(Object.values(catalog.notes))
  const english: [origin: string, text: string][] = [
    ...sheets.flatMap((sheet) => englishTexts(textsOf(sheet)).map((text): [string, string] => [sheet.id, text])),
    ...Object.values(SHARED_TEXTS.en).map((text): [string, string] => ['01_Parameter', text]),
    ...catalogTexts.filter((text): text is string => typeof text === 'string').map((text): [string, string] => ['Katalog', text]),
    ...Object.values(samplingTemplatesMessages.en).map((text): [string, string] => ['Meldungen', text]),
  ]

  it('kein englischer Text enthält eine alte Variante eines vereinheitlichten Begriffs', () => {
    const found = english.flatMap(([origin, text]) => OLD_VARIANTS.filter(([pattern]) => pattern.test(text) && !OLD_VARIANT_ALLOWED.has(text)).map(([, term]) => `${origin}: „${text}“ → ${term}`))
    expect(found).toEqual([])
  })

  it('derselbe deutsche Text ist in allen Blättern gleich übersetzt', () => {
    const renderings = new Map<string, Set<string>>()
    for (const sheet of sheets.filter((entry) => !isLegacy(entry))) {
      for (const [german, englishText] of pairsOf(sheet)) {
        if (englishText === undefined || AMBIGUOUS_GERMAN.has(german)) continue
        renderings.set(german, (renderings.get(german) ?? new Set()).add(englishText))
      }
    }
    for (const [german, englishText] of Object.entries(SHARED_TEXTS.en)) renderings.set(german, (renderings.get(german) ?? new Set()).add(englishText))
    expect([...renderings].filter(([, texts]) => texts.size > 1).map(([german, texts]) => `${german}: ${[...texts].join(' | ')}`)).toEqual([])
  })

  it('Vermerk auch im Katalog, in Blatt 01 und in den Meldungen', () => {
    for (const path of ['catalog/texts.en.ts', 'sheets/01_Parameter/texts.en.ts', 'i18n/messages.en.ts']) {
      expect(source(path), path).toContain(NOTICE)
      expect(source(path), path).toContain(TERMS_NOTICE)
    }
  })

  it('die englischen Meldungen der Oberfläche haben jeden Schlüssel der deutschen und keinen weiteren', () => {
    const german = Object.keys(samplingTemplatesMessages.de)
    const own = Object.keys(samplingTemplatesMessages.en)
    expect(german.filter((key) => !own.includes(key))).toEqual([])
    expect(own.filter((key) => !german.includes(key))).toEqual([])
    expect(Object.entries(samplingTemplatesMessages.en).filter(([, text]) => text === '').map(([key]) => key)).toEqual([])
  })
})
