import { describe, expect, it } from 'vitest'
import { defaultInputs } from '../src/model/definition'
import { createContext } from '../src/model/sheet'
import type { CellMap, MethodSummary, SheetContext } from '../src/model/types'
import { sheet } from '../src/sheets/18_GFQ_AnhIII/index'
import { en } from '../src/sheets/18_GFQ_AnhIII/texts.en'

/**
 * Belegrechnungen des KOM-Leitfadens EGESIF_16-0014-01, Abschnitt 7.10.3, zu
 * Anhang III DelVO (EU) 2023/67 (Entscheidung des Inhabers vom 17.10.2026:
 * „Es gelten die Vorgaben der KOM“). Die Zahlen sind die des Leitfadens; das
 * Methodenblatt ist durch seine Ergebnisübersicht ersetzt. Beispiel 7.10.3.3
 * (konservatives MUS) hat in der Vorlage kein Verfahren und fehlt daher.
 */
const defaults = defaultInputs(sheet.definition)
const EXCLUSION = 'Ausschluss (Art. 3 Abs. 6 Buchst. b)'
const REPLACEMENT = 'Ersetzung (Anh. III)'

function context(method: Partial<MethodSummary>, population: CellMap): SheetContext {
  const summary: MethodSummary = { sheet: '03_MUS_1Z', method: 'MUS', bookValue: 0, projectedError: 0, exhaustiveError: 0, precision: 0, systemicErrors: 0, anomalousErrors: 0, sampleSize: 0, totalErrorRate: 0 }
  return createContext({ sheets: { '02_Grundgesamtheit': { C20: 0, ...population } }, method: { ...summary, ...method } })
}

const run = (ctx: SheetContext, inputs: CellMap = {}): { cells: CellMap; hints: string[] } => {
  const cells = sheet.compute({ ...defaults, ...inputs }, ctx)
  return { cells, hints: (sheet.webHints?.({ ...defaults, ...inputs }, cells, ctx) ?? []).map((hint) => hint.id) }
}

/** 7.10.3.2: MUS, Ausschluss von 4 Einheiten (12.706.417 €) der Zufallsschicht; umfassende Schicht 6 Vorhaben, 586.837.081 €. */
const example2 = context(
  { bookValue: 4187175607, projectedError: 42459164 + 7616805, exhaustiveError: 7616805, precision: 52829067 },
  { C39: 4199882024, C47: 4, C48: 12706417, C49: EXCLUSION, C52: 1000 },
)

/** 7.10.3.4: einfache Zufallsstichprobe (Verhältnisschätzung), 6 Vorhaben (93.598.481 €) ausgeschlossen, davon 1 der umfassenden Schicht. */
const SE_EXAMPLE4 = 1000000
const example4 = context(
  { sheet: '08_SRS_1Z', method: 'SRS', bookValue: 2208284489, projectedError: 32426844.02 + 469301, exhaustiveError: 469301, precision: SE_EXAMPLE4 },
  { C39: 2301882970, C47: 6, C48: 93598481, C49: EXCLUSION, C52: 3520 },
)
const LOCATION4 = { C31: 3, C32: 295006242, C33: 1, C34: 295006242 - 203577481 }

describe('Anhang III nach KOM-Leitfaden 7.10.3: Belegrechnungen', () => {
  it('7.10.3.1 a: Ersetzung in der Zufallsschicht (MUS, Tabelle 1) – keine Anpassung, EE 52.294.628 € = 1,25 %', () => {
    const ctx = context({ bookValue: 4199882024, projectedError: 52294628, exhaustiveError: 0, precision: 50000000 }, { C39: 4199882024, C47: 1, C48: 5000000, C49: REPLACEMENT, C52: 1000 })
    const { cells } = run(ctx)
    expect(cells.C24).toBe(52294628)
    expect(cells.C25).toBe(50000000)
    expect(Number((cells.C26 as number).toFixed(4))).toBe(0.0125)
  })

  it('7.10.3.1 b: Ersetzung in der umfassenden Schicht (MUS) – EE_e = 420 · 1.987.446.254 / 1.697.136.654 = 492, EE = 50.020.779 € (1,19 %)', () => {
    const ctx = context(
      { bookValue: 4199882024, projectedError: 50020287 + 420, exhaustiveError: 420, precision: 50000000 },
      { C39: 4199882024, C47: 1, C48: 290309600, C49: REPLACEMENT, C52: 1000 },
    )
    const { cells, hints } = run(ctx, { C31: 8, C32: 1987446254, C33: 1, C34: 290309600 })
    expect(Math.round((420 * 1987446254) / 1697136654)).toBe(492)
    expect(Math.round(cells.C24 as number)).toBe(50020779)
    expect(cells.C25).toBe(50000000)
    expect(Number((cells.C26 as number).toFixed(4))).toBe(0.0119)
    expect(hints).not.toContain('exclusion-by-stratum')
  })

  it('7.10.3.2: Ausschluss (MUS) – Zufallsschicht 42.459.164 → 42.609.012 €, EE = 50.225.817 € (1,20 %), SE 52.829.067 → 53.015.513 €', () => {
    const { cells, hints } = run(example2, { C31: 6, C32: 586837081, C33: 0, C34: 0 })
    expect(cells).toMatchObject({ C35: 4, C36: 3613044943, C37: 3600338526 })
    expect(Math.round(42459164 * (cells.C38 as number))).toBe(42609012)
    expect(Math.round(cells.C24 as number)).toBe(50225817)
    expect(Math.round(cells.C25 as number)).toBe(53015513)
    expect(Number((cells.C26 as number).toFixed(4))).toBe(0.012)
    expect(Math.round((cells.C24 as number) + (cells.C25 as number))).toBe(103241330)
    expect(hints).toContain('exclusion-by-stratum')
  })

  it('7.10.3.4: Ausschluss (Verhältnisschätzung) – EE_e = 469.301 · 295.006.242 / 203.577.481 = 680.068,95, EE = 33.142.008,96 € (1,44 %), SE-Faktor 1,0011', () => {
    const { cells, hints } = run(example4, LOCATION4)
    expect(cells).toMatchObject({ C35: 5, C36: 2006876728, C37: 2004707008 })
    expect((cells.C38 as number).toFixed(4)).toBe('1.0011')
    expect(((cells.C24 as number) - 32426844.02 * (cells.C38 as number)).toFixed(2)).toBe('680068.95')
    expect((32426844.02 * (cells.C38 as number)).toFixed(2)).toBe('32461940.01')
    expect((cells.C24 as number).toFixed(2)).toBe('33142008.96')
    expect((cells.C26 as number).toFixed(4)).toBe('0.0144')
    expect(cells.C25).toBeCloseTo(SE_EXAMPLE4 * (cells.C38 as number), 6)
    expect(hints).toContain('exclusion-by-stratum')
  })

  it('7.10.3.4 ohne Lage der berührten Einheiten: wie die Vorlage mit dem Gesamtfaktor (1,50 % statt 1,44 %), Warnhinweis', () => {
    const { cells, hints } = run(example4)
    expect(cells.C35).toBeNull()
    expect((cells.C26 as number).toFixed(4)).toBe('0.0149')
    expect(hints).toContain('exclusion-location-missing')
    // Mit Abschnitt C (Anpassung der hochwertigen Schicht): nur der Zufallsteil mit dem Gesamtfaktor, EE_e über C21/C22.
    const sectionC = run(example4, { C20: 'Ja', C21: 295006242, C22: 203577481 })
    expect((sectionC.cells.C23 as number).toFixed(2)).toBe('680068.95')
    expect(sectionC.hints).toContain('exclusion-location-missing')
  })

  it('Ersetzung bei Tabelle 2 mit Lage: Genauigkeit der reduzierten Zufallsschicht SE · (N_s − A_s)/N_s · BV_s/BV_s,r', () => {
    const ctx = context(
      { sheet: '08_SRS_1Z', method: 'SRS', bookValue: 2301882970, projectedError: 33000000, exhaustiveError: 469301, precision: SE_EXAMPLE4 },
      { C39: 2301882970, C47: 6, C48: 93598481, C49: REPLACEMENT, C52: 3520 },
    )
    const { cells, hints } = run(ctx, LOCATION4)
    // N_s = 3.520 − 3 = 3.517, A_s = 6 − 1 = 5.
    expect(cells.C25).toBeCloseTo(((SE_EXAMPLE4 * (3517 - 5)) / 3517) * (2006876728 / 2004707008), 6)
    expect(hints).toContain('replacement-precision-not-scaled')
    // Ohne Lage: Gesamt-Näherung SE · (N − A)/N · BV/BV_r, nicht KOM-konform (umfassende Schicht vorhanden).
    const approximation = run(ctx)
    expect(approximation.cells.C25).toBeCloseTo(((SE_EXAMPLE4 * (3520 - 6)) / 3520) * (2301882970 / (2301882970 - 93598481)), 6)
    expect(approximation.hints).toContain('replacement-location-missing')
  })

  it('jeder Hinweis zur Lage hat eine englische Fassung', () => {
    for (const id of ['replacement-precision-not-scaled', 'replacement-precision-reduced', 'replacement-location-missing', 'exclusion-by-stratum', 'exclusion-location-missing', 'annex-iii-approximation']) {
      expect(en.webHints?.[id], id).toMatch(/EGESIF_16-0014-01|Annex III/)
    }
  })
})
