import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import {
  addScenario,
  bandTone,
  blockProgress,
  groupByDepartment,
  isDeviation,
  mayRelease,
  parseConditions,
  parseCount,
  registerCsv,
  registerHtml,
  registerMarkdown,
  surveyFrom,
  toggleMeasure,
  withAnswer,
} from '../../src/dataprotection'
import { completeness, editedBy, fieldIssues, issuesFor, withField } from '../../src/dataprotection/registerView'
import type { Issue, RegisterContent } from '../../src/dataprotection/types'
import { draftAssessment, profile, proposal, register, released } from './fake-port'

const content = register.draft!.content
const issues = register.draft!.issues
const texts = {
  yes: 'ja', no: 'nein', empty: '—', title: 'Verzeichnis', department: 'Referat', withoutDepartment: 'Ohne Referat',
  controller: 'Verantwortlicher', dpo: 'DSB', version: 'Fassung', issues: 'Hinweise', noIssues: 'Keine', required: 'Pflicht',
  hint: 'Hinweis', field: 'Angabe', content: 'Inhalt', generated: 'Erstellt am',
}

function contract(name: string): { cases: { id: string; input: Record<string, unknown>; expect: { value: string } }[] } {
  // Vitest läuft in packages-js/ui; die Verträge liegen im Repository-Wurzelverzeichnis.
  const path = resolve(process.cwd(), '../../contracts/common-cases', `${name}.json`)
  return JSON.parse(readFileSync(path, 'utf-8')) as ReturnType<typeof contract>
}

describe('View-Logik Verzeichnis', () => {
  it('gruppiert nach Referaten wie die Bibliothek und filtert per Suche', () => {
    expect(groupByDepartment(content).map((group) => [group.department, group.items.length])).toEqual([['Referat Z 1', 1], ['Referat Z 6', 2]])
    expect(groupByDepartment(content, 'online').map((group) => group.items.map((item) => item.activity.id))).toEqual([['cloud']])
    const unknown: RegisterContent = { ...content, referate: [], taetigkeiten: [{ name: 'A', referat: '' }, { name: 'B', referat: 'X' }] }
    expect(groupByDepartment(unknown).map((group) => group.department)).toEqual(['', 'X'])
  })

  it('ordnet die Hinweise der Bibliothek Tätigkeiten und Feldern zu', () => {
    const cloud = content.taetigkeiten.find((activity) => activity.id === 'cloud')!
    expect(completeness(issuesFor(issues, cloud))).toEqual({ blocking: 2, hints: 2 })
    expect(fieldIssues(issues, cloud, 'speicherdauer')[0]?.message).toContain('Speicherdauer')
    expect(issuesFor(issues, content.taetigkeiten[0]!)).toEqual([])
  })

  it('ändert Inhalte unveränderlich und prüft Zahlfelder', () => {
    const changed = withField(content, 0, 'zweck', 'Neu')
    expect(changed.taetigkeiten[0]?.zweck).toBe('Neu')
    expect(content.taetigkeiten[0]?.zweck).not.toBe('Neu')
    expect([parseCount(''), parseCount(' 12 '), parseCount('1,5'), parseCount('-1')]).toEqual([null, 12, undefined, undefined])
    expect(editedBy(register.draft, 'daten-a')).toBe(true)
    expect(editedBy(register.draft, 'daten-b')).toBe(false)
  })
})

describe('Exporte mit Formelschutz', () => {
  it('schützt jede Zelle nach dem gemeinsamen Vertrag csv-cell (über @flowaudit/common)', () => {
    const cells = contract('csv-cell').cases.map((entry) => entry.input.value as string | number | null)
    const activities = cells.map((value) => ({ name: 'x', anmerkungen: value }))
    const csv = registerCsv({ content: { ...content, taetigkeiten: activities }, columns: [{ key: 'anmerkungen', title: 'A', reference: '', kind: 'text', required: false }], issues: [], versionLabel: '', texts })
    const expected = contract('csv-cell').cases.map((entry) => `;${entry.expect.value}`)
    expect(csv.split('\r\n').slice(1, -1)).toEqual(expected)
  })

  it('schreibt das Verzeichnis als CSV, Markdown und Druckansicht', () => {
    const input = { content, columns: profile.register.columns, issues, versionLabel: 'Fassung 2 – Entwurf', texts }
    const csv = registerCsv(input)
    expect(csv.startsWith('﻿Referat / Abteilung;Datenverarbeitungsvorgang;')).toBe(true)
    expect(csv).toContain(";'=Voreinstellung des Anbieters;")
    expect(csv.split('\r\n')).toHaveLength(content.taetigkeiten.length + 2)
    const markdown = registerMarkdown(input)
    expect(markdown).toContain('## Referat Z 6')
    expect(markdown).toContain('- Pflicht: „Speicherdauer“ fehlt')
    const html = registerHtml({ ...input, generatedAt: '25.09.2026' })
    expect(html).toMatch(/^<!DOCTYPE html><html lang="de">/)
    expect(html).toContain('<h3>Terminplanung über Online-Dienst</h3>')
    const hostile: Issue = { code: 'x', message: '<script>alert(1)</script>', blocking: true, subject: 'a:b' }
    expect(registerHtml({ ...input, issues: [hostile] })).not.toContain('<script>alert')
  })
})

describe('View-Logik Folgenabschätzung', () => {
  it('übernimmt die gespeicherte Erhebung und zählt Antworten je Block', () => {
    const survey = surveyFrom(released, profile)
    const muss = profile.screening.blocks[1]!
    expect(blockProgress(muss, survey)).toEqual({ answered: 17, total: 17, yes: 1 })
    const empty = surveyFrom(draftAssessment, profile)
    expect(blockProgress(muss, empty)).toEqual({ answered: 0, total: 17, yes: 0 })
    const answered = withAnswer(empty, 'dsk_nr01_biometrie', 'unbekannt')
    expect(blockProgress(muss, answered).answered).toBe(0)
    expect(answered.answers.dsk_nr01_biometrie).toEqual({ value: 'unbekannt', justification: '' })
  })

  it('verwaltet Szenarien und Maßnahmen', () => {
    const survey = addScenario(surveyFrom(draftAssessment, profile), profile)
    const scenario = survey.scenarios[0]!
    expect(scenario).toMatchObject({ dimension: 'vertraulichkeit', severity: 3, likelihood: 3, measures: [] })
    const toggled = toggleMeasure(toggleMeasure(scenario, 'verschluesselung'), 'loeschkonzept')
    expect(toggleMeasure(toggled, 'verschluesselung').measures).toEqual(['loeschkonzept'])
  })

  it('ordnet Stufen, Abweichungen und Freigaberecht ein', () => {
    const bands = profile.risk.bands
    expect(bands.map((band) => bandTone(band, bands))).toEqual(['neutral', 'success', 'warning', 'danger'])
    expect(isDeviation(proposal, 'freigabe_mit_auflagen')).toBe(false)
    expect(isDeviation(proposal, 'freigabe')).toBe(true)
    expect(parseConditions(' A \n\n B ')).toEqual(['A', 'B'])
    expect(mayRelease(draftAssessment, 'daten-a')).toBe(false)
    expect(mayRelease(draftAssessment, 'daten-b')).toBe(true)
    expect(mayRelease(released, 'daten-b')).toBe(false)
  })
})
