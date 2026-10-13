import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { sheet as sheet03 } from '../src/sheets/03_MUS_1Z/index'
import { describeNotice, describeOpenError } from '../src/view/notices'
import { FOUNDATION_SHEETS } from './sheets'
import { canonicalInputs, checksumOf, sha256Fallback } from '../src/workspace/canonical'
import { computeWorkspace } from '../src/workspace/compute'
import { exportFileName, workspaceFileName } from '../src/workspace/filenames'
import { openWorkspace } from '../src/workspace/open'
import { saveWorkspace } from '../src/workspace/save'
import { ENGINE_VERSION, WORKSPACE_FORMAT, emptyWorkspace, type WorkspaceFile, type WorkspaceState } from '../src/workspace/types'

const now = new Date('2026-10-13T09:30:00Z')
const state: WorkspaceState = { ...emptyWorkspace(), activeMethod: '03_MUS_1Z', sheets: { '03_MUS_1Z': sheet03.sample.inputs } }
const t = createTranslate()

async function savedFile(): Promise<WorkspaceFile> {
  return (await saveWorkspace(state, { now })).file
}

async function reopen(change: (file: Record<string, unknown>) => void): Promise<Awaited<ReturnType<typeof openWorkspace>>> {
  const file = JSON.parse(JSON.stringify(await savedFile())) as Record<string, unknown>
  change(file)
  return openWorkspace(JSON.stringify(file))
}

describe('Arbeitsstand speichern', () => {
  it('schreibt das Format mit Zelladressen, Ergebnissen und Prüfsumme', async () => {
    const saved = await saveWorkspace(state, { now })
    expect(saved.file).toMatchObject({ format: WORKSPACE_FORMAT, formatVersion: 1, rechenkern: ENGINE_VERSION, gespeichertAm: '2026-10-13T09:30:00.000Z', aktiveMethode: '03_MUS_1Z' })
    expect(saved.file.blaetter['03_MUS_1Z']).toMatchObject({ C7: 48500000, C9: 'mittel' })
    expect(saved.file.ergebnisse['03_MUS_1Z']).toMatchObject({ C27: 92 })
    expect(saved.file.ergebnisse['03_MUS_1Z']).not.toHaveProperty('C9')
    expect(saved.file.pruefsumme).toMatch(/^sha256:[0-9a-f]{64}$/)
    expect(saved.fileName).toBe('Stichprobe_03_MUS_1Z_2025_2026_Arbeitsstand.json')
    expect(exportFileName(state, undefined, now)).toBe('Stichprobe_03_MUS_1Z_2025_2026_Ergebnis.xlsx')
    expect(workspaceFileName(emptyWorkspace(), undefined, now)).toBe('Stichprobe_2026-10-13_Arbeitsstand.json')
    expect(workspaceFileName(state, undefined, now, 'ECOHESION Stichprobe')).toBe('ECOHESION_Stichprobe_03_MUS_1Z_2025_2026_Arbeitsstand.json')
    expect(exportFileName(state, undefined, now, '../')).toBe('Stichprobe_03_MUS_1Z_2025_2026_Ergebnis.xlsx')
  })

  it('die Rechenkern-Fassung ist die Paketversion', () => {
    const manifest = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8')) as { version: string }
    expect(ENGINE_VERSION).toBe(manifest.version)
  })

  it('die Prüfsumme hängt nicht von Reihenfolge und Leerwerten ab', async () => {
    const a = canonicalInputs({ kopf: state.header, aktiveMethode: 'x', blaetter: { s: { C2: 1, C1: 'a', C3: null } } })
    const b = canonicalInputs({ aktiveMethode: 'x', blaetter: { s: { C1: 'a', C2: 1 } }, kopf: { ...state.header } })
    expect(a).toBe(b)
    expect(await checksumOf(a)).toBe(await checksumOf(b))
    expect(canonicalInputs({ kopf: state.header, aktiveMethode: 'x', blaetter: { s: { C1: 'a', C2: 2 } } })).not.toBe(a)
  })

  it('SHA-256 ohne Web Crypto liefert denselben Wert', async () => {
    const hex = (bytes: Uint8Array): string => [...bytes].map((byte) => byte.toString(16).padStart(2, '0')).join('')
    expect(hex(sha256Fallback(new TextEncoder().encode('abc')))).toBe('ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
    for (const text of ['', 'Prüfbehörde – 48.500.000,00 €', 'x'.repeat(55), 'x'.repeat(56), 'x'.repeat(64), 'y'.repeat(1000)]) {
      expect(`sha256:${hex(sha256Fallback(new TextEncoder().encode(text)))}`).toBe(await checksumOf(text))
    }
  })
})

describe('Arbeitsstand öffnen', () => {
  it('Rundlauf: gleiche Eingaben, gleiche Ergebnisse, keine Hinweise', async () => {
    const saved = await saveWorkspace(state, { now })
    const opened = await openWorkspace(saved.text)
    expect(opened).toMatchObject({ ok: true, notices: [], savedAt: '2026-10-13T09:30:00.000Z', engine: ENGINE_VERSION })
    if (!opened.ok) return
    expect(opened.state).toEqual(state)
    expect(computeWorkspace(opened.state)).toEqual(computeWorkspace(state))
  })

  it('veränderte Eingaben lösen den Prüfsummenhinweis aus', async () => {
    const opened = await reopen((file) => {
      ;(file.blaetter as Record<string, Record<string, unknown>>)['03_MUS_1Z']!.C7 = 58500000
    })
    expect(opened.ok && opened.notices).toEqual([{ kind: 'checksum-mismatch' }])
    expect(opened.ok && describeNotice(opened.notices[0]!, t)).toContain('außerhalb der Anwendung verändert')
  })

  it('eine fehlende oder verformte Prüfsumme gilt als Veränderung', async () => {
    const missing = await reopen((file) => delete file.pruefsumme)
    const malformed = await reopen((file) => (file.pruefsumme = 'sha256:abc'))
    expect(missing.ok && missing.notices[0]?.kind).toBe('checksum-mismatch')
    expect(malformed.ok && malformed.notices[0]?.kind).toBe('checksum-mismatch')
  })

  it('abweichende gespeicherte Ergebnisse werden mit Größe und Rechenkern-Fassungen genannt', async () => {
    const opened = await reopen((file) => {
      ;(file.ergebnisse as Record<string, Record<string, unknown>>)['03_MUS_1Z']!.C27 = 95
      file.rechenkern = '0.0.9'
    })
    expect(opened.ok).toBe(true)
    if (!opened.ok) return
    expect(opened.notices).toEqual([
      { kind: 'results-differ', storedEngine: '0.0.9', currentEngine: ENGINE_VERSION, differences: [expect.objectContaining({ sheet: '03_MUS_1Z', cell: 'C27', stored: 95, computed: 92 })] },
    ])
    const text = describeNotice(opened.notices[0]!, t)
    expect(text).toContain('Anzuwendender Stichprobenumfang')
    expect(text).toContain('0.0.9')
  })

  it('unbekannte Felder werden ignoriert und gemeldet', async () => {
    const opened = await reopen((file) => {
      file.zusatz = { a: 1 }
      ;(file.kopf as Record<string, unknown>).referat = 'Z 6'
    })
    expect(opened.ok && opened.notices).toEqual([{ kind: 'unknown-fields', fields: ['zusatz', 'kopf.referat'] }])
    expect(opened.ok && opened.state).toEqual(state)
  })

  it('unbekannte Blätter, fremde Zellen und unpassende Werte werden nicht übernommen', async () => {
    const opened = await reopen((file) => {
      const sheets = file.blaetter as Record<string, Record<string, unknown>>
      sheets['99_Fremd'] = { C1: 1 }
      sheets['03_MUS_1Z']!.C27 = 500
      sheets['03_MUS_1Z']!.C9 = 'sehr hoch'
      sheets['03_MUS_1Z']!.C8 = 'viele'
    })
    expect(opened.ok).toBe(true)
    if (!opened.ok) return
    const unknown = opened.notices.find((notice) => notice.kind === 'unknown-fields')
    expect(unknown).toEqual({ kind: 'unknown-fields', fields: expect.arrayContaining(['blaetter.99_Fremd', 'blaetter.03_MUS_1Z.C27', 'blaetter.03_MUS_1Z.C9', 'blaetter.03_MUS_1Z.C8']) })
    expect(opened.state.sheets['03_MUS_1Z']).not.toHaveProperty('C27')
    expect(opened.state.sheets).not.toHaveProperty('99_Fremd')
  })

  it('Eingaben geplanter Blätter bleiben erhalten', async () => {
    const withPlanned: WorkspaceState = { ...state, sheets: { ...state.sheets, '05_MUS_2Z': { C7: 1000 }, '18_GFQ_AnhIII': [{ kennung: 'V-1', C6: 5 }] } }
    const opened = await openWorkspace((await saveWorkspace(withPlanned, { now, sheets: FOUNDATION_SHEETS })).text, { sheets: FOUNDATION_SHEETS })
    expect(opened).toMatchObject({ ok: true, notices: [] })
    expect(opened.ok && opened.state.sheets).toEqual(withPlanned.sheets)
  })

  it('neuere Formatfassungen werden abgelehnt', async () => {
    const opened = await reopen((file) => (file.formatVersion = 2))
    expect(opened).toEqual({ ok: false, error: { code: 'newer-version', detail: '2' } })
    expect(!opened.ok && describeOpenError(opened.error, t)).toContain('neueren Fassung')
  })

  it('ältere Formatfassungen werden über Migrationen angehoben', async () => {
    const file = JSON.parse(JSON.stringify(await savedFile())) as Record<string, unknown>
    const old = { ...file, eingaben: file.blaetter, blaetter: undefined }
    const opened = await openWorkspace(JSON.stringify(old), {
      currentVersion: 2,
      migrations: { 1: (previous) => ({ ...previous, blaetter: previous.eingaben, eingaben: undefined }) },
    })
    expect(opened.ok && opened.notices).toContainEqual({ kind: 'migrated', from: 1, to: 2 })
    expect(opened.ok && opened.state.sheets['03_MUS_1Z']).toEqual(sheet03.sample.inputs)
    const missing = await openWorkspace(JSON.stringify(file), { currentVersion: 3, migrations: {} })
    expect(missing).toMatchObject({ ok: false, error: { code: 'invalid-structure' } })
  })

  it('fremde und beschädigte Dateien werden mit Grund abgelehnt', async () => {
    expect(await openWorkspace('{"format":"anders","formatVersion":1}')).toEqual({ ok: false, error: { code: 'not-a-workspace', detail: undefined } })
    expect(await openWorkspace('[1,2]')).toMatchObject({ ok: false, error: { code: 'not-a-workspace' } })
    expect(await openWorkspace('{kein json')).toMatchObject({ ok: false, error: { code: 'invalid-json' } })
    expect(await openWorkspace('x'.repeat(100), { maxSize: 50 })).toMatchObject({ ok: false, error: { code: 'too-large' } })
    expect(await reopen((file) => (file.formatVersion = 1.5))).toMatchObject({ ok: false, error: { code: 'invalid-structure', detail: 'formatVersion' } })
    expect(await reopen((file) => (file.blaetter = { '03_MUS_1Z': { 'C7; DROP': 1 } }))).toMatchObject({ ok: false, error: { code: 'invalid-structure' } })
    expect(await reopen((file) => (file.blaetter = { '03_MUS_1Z': { C7: { verschachtelt: true } } }))).toMatchObject({ ok: false, error: { code: 'invalid-structure', detail: 'blaetter.03_MUS_1Z.C7' } })
    expect(await reopen((file) => (file.kopf = { programm: 5 }))).toMatchObject({ ok: false, error: { code: 'invalid-structure', detail: 'kopf.programm' } })
    expect(await reopen((file) => (file.aktiveMethode = '../etc'))).toMatchObject({ ok: false, error: { code: 'invalid-structure', detail: 'aktiveMethode' } })
  })

  it('Schlüssel, die den Prototyp verändern könnten, führen zum Abbruch', async () => {
    const text = (await saveWorkspace(state, { now })).text
    for (const key of ['__proto__', 'constructor', 'prototype']) {
      const opened = await openWorkspace(text.replace('"kopf": {', `"kopf": { "${key}": { "polluted": true },`))
      expect(opened).toEqual({ ok: false, error: { code: 'unsafe-key', detail: key } })
    }
    expect(({} as Record<string, unknown>).polluted).toBeUndefined()
  })

  it('ohne Blattangaben entsteht ein leerer Arbeitsstand', async () => {
    const saved = await saveWorkspace(emptyWorkspace(), { now })
    expect(saved.file.blaetter).toEqual({})
    expect(await openWorkspace(saved.text)).toMatchObject({ ok: true, state: emptyWorkspace(), notices: [] })
  })
})
