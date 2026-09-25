import { describe, expect, it } from 'vitest'
import { applySuggestions, collectSuggestions, type Suggestion } from '../src/enrichment/suggestions'
import { auditReferencesIn, crossReferencesIn, removeRolePrefix, sourcesIn } from '../src/enrichment/textPatterns'
import { headlessAccess } from '../src/model/access'
import { loadDefinitions, saveDefinitions } from '../src/model/load'
import { modelFromDefinitions } from '../src/model/buildModel'
import { fixture, modelOf, TEST_PROFILE } from './helpers'

describe('text patterns (notations of AUSWERTUNG.md)', () => {
  it('assessment criteria in long and short form', () => {
    expect(auditReferencesIn('Bewertungskriterien 2.4 und 2.6').map((h) => h.value)).toEqual([
      { keyRequirement: '2', assessmentCriterion: '2.4' },
      { keyRequirement: '2', assessmentCriterion: '2.6' },
    ])
    expect(auditReferencesIn('siehe BK 2.3')[0]!.value).toEqual({ keyRequirement: '2', assessmentCriterion: '2.3' })
  })

  it('finding references, checklist items and registers', () => {
    const values = crossReferencesIn('Feststellungen T15 F1 und T15 F6; Antragsprüfcheckliste FP 1000 V 1.2, Prüffeld 3.21 [A1, A3, B1]').map((h) => h.value)
    expect(values).toEqual([
      { kind: 'feststellung_ref', key: 'T15 F1' },
      { kind: 'feststellung_ref', key: 'T15 F6' },
      { kind: 'prueffeld', key: '3.21', document: 'Antragsprüfcheckliste FP 1000 V 1.2' },
      { kind: 'register', key: 'A1' },
      { kind: 'register', key: 'A3' },
      { kind: 'register', key: 'B1' },
    ])
  })

  it('manual references with page range', () => {
    const [hit] = sourcesIn('Förderhandbuch 21+ V 1.1, Kapitel 11.2.1 (PDF-Seiten 77 bis 82)')
    expect(hit!.value).toEqual({ sourceType: 'verfahrenshandbuch', location: 'Förderhandbuch 21+ V 1.1, Kapitel 11.2.1 (PDF-Seiten 77 bis 82)' })
  })

  it('removes the role prefix of a label', () => {
    expect(removeRolePrefix('Musterbank: Antrag prüfen')).toBe('Antrag prüfen')
    expect(removeRolePrefix('Antrag prüfen')).toBe('Antrag prüfen')
  })
})

describe('collectSuggestions', () => {
  it('derives legal bases, references, sources, roles and markers', async () => {
    const suggestions = collectSuggestions(await modelOf(fixture('enrichment.bpmn')), { profile: TEST_PROFILE })
    const of = (elementId: string, kind: Suggestion['kind']) => suggestions.filter((s) => s.elementId === elementId && s.kind === kind)
    expect(of('Task_Pruefen', 'legalBasis')[0]!.value).toMatchObject({ article: '73', point: 'b' })
    expect(of('Task_Pruefen', 'source')).toHaveLength(1)
    expect(of('Task_Pruefen', 'crossReference').map((s) => (s.value as { key: string }).key)).toEqual(['T15 F1', 'T15 F6', '3.21', 'A1', 'A3', 'B1'])
    expect(of('Task_Nachfordern', 'legalBasis').map((s) => (s.value as { text?: string }).text)).toEqual([
      'Artikel 74 Absatz 2 Unterabsatz 2 der Verordnung (EU) 2021/1060',
      '§ 23 LHO',
      '§ 44 LHO',
      'VV Nummer 4.2 zu § 44 LHO',
      '§ 37 Absatz 2 Satz 2 HVwVfG',
    ])
    expect(of('Pool_A', 'auditReference')).toHaveLength(2)
    expect(of('Lane_Bank', 'actor')[0]!.value).toEqual({ role: 'zgs', displayName: 'Musterbank (zwischengeschaltete Stelle)' })
    expect(of('Lane_VB', 'actor')[0]!.value).toMatchObject({ role: 'vb' })
    expect(of('Lane_Antrag', 'actor')[0]!.value).toMatchObject({ role: 'beg' })
    expect(of('Task_Nachreichen', 'rolePrefix')[0]!.value).toBe('beg')
    expect(of('Task_Pruefen', 'marker')[0]!.value).toEqual({ type: 'feststellung' })
    expect(of('Task_Nachfordern', 'marker').map((s) => s.value)).toEqual([{ type: 'soll_ohne_regelung' }])
    expect(of('Task_Auswahl', 'marker')[0]!.value).toEqual({ type: 'ohne_befund' })
  })

  it('supports application aliases for names of bodies', async () => {
    const suggestions = collectSuggestions(await modelOf(fixture('enrichment.bpmn')), { profile: TEST_PROFILE, roleAliases: [{ pattern: 'Musterbank', role: 'zgs' }] })
    expect(suggestions.find((s) => s.elementId === 'Task_Pruefen' && s.kind === 'rolePrefix')?.value).toBe('zgs')
  })
})

describe('applySuggestions', () => {
  it('writes accepted suggestions without duplicates and removes prefixes', async () => {
    const loaded = await loadDefinitions(fixture('enrichment.bpmn'))
    const model = modelFromDefinitions(loaded.definitions)
    const suggestions = collectSuggestions(model, { profile: TEST_PROFILE })
    const access = headlessAccess(loaded.definitions, loaded.moddle)
    const changed = applySuggestions(access, [...suggestions, ...suggestions], { removePrefixes: true })
    expect(changed).toBeGreaterThan(5)
    const after = modelFromDefinitions((await loadDefinitions(await saveDefinitions(loaded))).definitions)
    expect(after.byId.get('Task_Pruefen')?.extensions.crossReferences).toHaveLength(6)
    expect(after.byId.get('Lane_Bank')?.extensions.actor?.role).toBe('zgs')
    expect(after.byId.get('Task_Nachreichen')?.name).toBe('Unterlagen nachreichen')
    expect(after.byId.get('Task_Pruefen')?.extensions.markers).toEqual([{ type: 'feststellung' }])
  })

  it('does not overwrite an existing actor', async () => {
    const loaded = await loadDefinitions(fixture('schema-1.1.bpmn'))
    const access = headlessAccess(loaded.definitions, loaded.moddle)
    applySuggestions(access, [{ id: 'S1', elementId: 'Lane_VB', kind: 'actor', value: { role: 'pb' }, excerpt: '', origin: 'name' }])
    expect(access.read('Lane_VB').actor?.role).toBe('vb')
  })
})
