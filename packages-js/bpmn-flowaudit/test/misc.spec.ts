import { describe, expect, it } from 'vitest'
import { groupByElement, normalizeEsiResponse, summarize } from '../src/esi/esiRequirements'
import { collectExportData } from '../src/export/exportData'
import { fileName, readSvgSize } from '../src/export/imageExport'
import { imageToPdf, pdfString, pixelsToMm } from '../src/export/pdf'
import { createTranslator, translateModule } from '../src/i18n/translate'
import { ICONS, hasIcon, iconElement, iconPrimitives, iconSvg } from '../src/icons/icons'
import { InMemoryStorage, ProfileCataloguePort, ProfileLegalSearch, StaticProfilePort } from '../src/ports/inMemory'
import { bundledProfiles } from '../src/profile/bundled'
import { criterionKnown, keyRequirement, latestProfiles, roleFromText, roleOf, rolesFor, validateProfile, withCriteria } from '../src/profile/profile'
import { MARKERS } from '../src/schema/vocabulary'
import { ROLES, roleAppliesTo } from '../src/schema/roles'
import { nextStepId, recordStep, removeStep, walkthroughProgress, walkthroughSteps } from '../src/walkthrough/walkthrough'
import { headlessAccess } from '../src/model/access'
import { loadDefinitions } from '../src/model/load'
import { modelFromDefinitions } from '../src/model/buildModel'
import { emptyCollection } from '../src/collection/collectionData'
import { fixture, modelOf, TEST_PROFILE } from './helpers'

describe('icons', () => {
  it('has an icon for every role and every marker', () => {
    for (const role of Object.values(ROLES)) expect(hasIcon(role.icon)).toBe(true)
    for (const type of Object.keys(MARKERS)) expect(hasIcon(`marker-${type}`)).toBe(true)
  })

  it('uses only the 24 px grid and currentColor', () => {
    for (const [name, shapes] of Object.entries(ICONS)) {
      expect(shapes.length, name).toBeGreaterThan(0)
      const numbers = JSON.stringify(shapes).match(/-?\d+(\.\d+)?/g)?.map(Number) ?? []
      expect(Math.max(...numbers), name).toBeLessThanOrEqual(24)
    }
    const svg = iconSvg('save', 20)
    expect(svg).toContain('stroke="currentColor"')
    expect(svg).toContain('width="20"')
    expect(iconPrimitives('unbekannt')).toEqual(iconPrimitives('info'))
    expect(iconElement(document, 'check', 1, 2, 12).getAttribute('transform')).toBe('translate(1 2) scale(0.5)')
  })
})

describe('profiles', () => {
  it('resolves roles, aliases and criteria', () => {
    expect(rolesFor(TEST_PROFILE).map((r) => r.code)).toContain('rfs')
    expect(rolesFor(TEST_PROFILE, '2014-2020').map((r) => r.code)).not.toContain('rfs')
    expect(roleAppliesTo(ROLES.bb!, '2021-2027')).toBe(false)
    expect(roleFromText(TEST_PROFILE, 'Musterbank (zwischengeschaltete Stelle)')).toBe('zgs')
    expect(roleFromText(TEST_PROFILE, 'Musterbank', [{ pattern: 'musterbank', role: 'zgs' }])).toBe('zgs')
    expect(keyRequirement(TEST_PROFILE, '2')?.number).toBe(2)
    expect(criterionKnown(TEST_PROFILE, 2, '2.3')).toBe(true)
    expect(criterionKnown(TEST_PROFILE, 4, '4.1')).toBeUndefined()
    expect(criterionKnown(withCriteria(TEST_PROFILE, { 4: [{ code: '4.1' }] }), 4, '4.2')).toBe(false)
    expect(roleOf({ ...TEST_PROFILE, custom_roles: { xy: { labels: 'Eigene Stelle' } } }, 'xy')?.label.de).toBe('Eigene Stelle')
    expect(latestProfiles([TEST_PROFILE, { ...TEST_PROFILE, version: '2026.10.1' }])[0]!.version).toBe('2026.10.1')
    expect(() => validateProfile({ schema: 'x' })).toThrow('Profilschema')
  })

  it('bundles the profiles of auditcore_bpmn when present', () => {
    const profiles = bundledProfiles()
    if (!profiles.length) return
    expect(profiles.map((p) => p.id)).toContain('foerderperiode-2021-2027')
    expect(profiles.find((p) => p.id === 'foerderperiode-2021-2027')?.key_requirements?.entries).toHaveLength(15)
  })
})

describe('ports in memory', () => {
  it('stores collection, diagrams, approvals and comments', async () => {
    const storage = new InMemoryStorage({ diagrams: { a: '<x/>' } })
    expect(await storage.loadCollection()).toBeNull()
    await storage.saveCollection(emptyCollection())
    expect((await storage.loadCollection())?.schema).toBe('auditcore_bpmn.diagram-collection/1')
    expect(await storage.loadDiagram('a')).toBe('<x/>')
    await storage.deleteDiagram('a')
    await expect(storage.loadDiagram('a')).rejects.toThrow('unbekannt')
    await storage.saveApproval('a', '1', '<x/>')
    await expect(storage.saveApproval('a', '1', '<y/>')).rejects.toThrow('bereits freigegeben')
    expect(await storage.loadApproval('a', '1')).toBe('<x/>')
    await storage.saveComments('a', [{ id: '1', elementId: 'T', text: 'x', author: 'A', timestamp: 't', resolved: false }])
    expect(await storage.loadComments('a')).toHaveLength(1)
  })

  it('serves profiles, catalogue and legal search', async () => {
    const profiles = new StaticProfilePort([TEST_PROFILE])
    expect((await profiles.profiles())[0]).toMatchObject({ id: 'foerderperiode-2021-2027', programmingPeriod: '2021-2027' })
    const catalogue = new ProfileCataloguePort(profiles, { 'foerderperiode-2021-2027': { 4: [{ code: '4.1', title: 'Verfahren' }] } })
    const entries = await catalogue.keyRequirements('foerderperiode-2021-2027')
    expect(entries[3]!.criteria).toEqual([{ code: '4.1', title: 'Verfahren' }])
    expect(entries[1]!.criteria.map((c) => c.code)).toEqual(['2.3', '2.4', '2.6'])
    const search = new ProfileLegalSearch(TEST_PROFILE)
    expect((await search.search('Art. 74'))[0]).toMatchObject({ article: '74', origin: 'Profil' })
    expect((await search.search('Art. 5 VO (EU) 2021/1060'))[0]).toMatchObject({ article: '5', origin: 'Eingabe', celex: '32021R1060' })
    expect((await search.search('verwaltungsprüf')).map((h) => h.article)).toEqual(['74'])
    expect(await search.search('  ')).toEqual([])
  })
})

describe('walkthrough', () => {
  it('lists steps in flow order with status and progress', async () => {
    const steps = walkthroughSteps(await modelOf(fixture('schema-1.1.bpmn')))
    expect(steps[0]!.elementId).toBe('Task_Pruefen')
    expect(steps[0]).toMatchObject({ status: 'erfuellt', keyControls: [expect.objectContaining({ id: 'K1' })] })
    expect(steps.find((s) => s.elementId === 'Gateway_Vollst')).toBeDefined()
    expect(walkthroughProgress(steps)).toMatchObject({ met: 1, open: steps.length - 1 })
  })

  it('records, replaces and removes audit steps', async () => {
    const loaded = await loadDefinitions(fixture('schema-1.1.bpmn'))
    const access = headlessAccess(loaded.definitions, loaded.moddle)
    const id = nextStepId(modelFromDefinitions(loaded.definitions))
    expect(id).toBe('PS2')
    recordStep(access, 'Task_Auszahlen', { id, case: 'Vorhaben 0002', result: 'nicht_erfuellt' })
    recordStep(access, 'Task_Auszahlen', { id, case: 'Vorhaben 0002', result: 'erfuellt' })
    expect(access.read('Task_Auszahlen').auditSteps).toEqual([{ id, case: 'Vorhaben 0002', result: 'erfuellt' }])
    removeStep(access, 'Task_Auszahlen', id)
    expect(access.read('Task_Auszahlen').auditSteps).toEqual([])
  })
})

describe('ESI requirements', () => {
  it('normalises every response shape and derives the status', () => {
    const list = normalizeEsiResponse({
      elements: [
        { element_id: 'T1', element_name: 'Prüfen', requirements: [{ id: 'R1', description: 'A', expected: 'x', actual: 'x' }, { id: 'R2', expected: 'x' }] },
        { elementId: 'T2', requirements: [{ id: 'R3', status: 'ok' }] },
      ],
    })
    expect(list.map((r) => r.status)).toEqual(['fulfilled', 'missing', 'fulfilled'])
    expect(normalizeEsiResponse([{ element_id: 'T3', status: 'unklar' }])[0]!.status).toBe('unclear')
    expect(normalizeEsiResponse({ T4: { requirements: [{ id: 'R' }] } })[0]!.elementId).toBe('T4')
    expect(normalizeEsiResponse(null)).toEqual([])
    expect(groupByElement(list)[0]).toMatchObject({ elementId: 'T1', fulfilledCount: 1, totalCount: 2 })
    expect(summarize(list)).toEqual({ total: 3, fulfilled: 2, unclear: 0, missing: 1 })
  })
})

describe('export helpers', () => {
  it('collects colours, markers and legal basis notes', async () => {
    const data = collectExportData(await modelOf(fixture('schema-1.1.bpmn')))
    expect(data.markers.find((m) => m.type === 'vier_augen')).toMatchObject({ label: 'Vier-Augen-Prinzip', count: 1 })
    expect(data.legalBases.find((n) => n.elementId === 'Task_Pruefen')).toMatchObject({ x: 260, y: 310, width: 100 })
    expect(collectExportData(await modelOf(fixture('legacy-1.0.bpmn'))).colors[0]!.label).toBe('Kritisch / neu')
  })

  it('builds file names and reads SVG sizes', () => {
    expect(fileName('Ablauf der Prüfung: Teil/1', 'svg')).toBe('Ablauf_der_Prüfung_Teil1.svg')
    expect(fileName('', 'png')).toBe('diagramm.png')
    expect(readSvgSize('<svg width="10" height="20">')).toEqual({ width: 10, height: 20 })
    expect(readSvgSize('<svg viewBox="0 0 30 40">')).toEqual({ width: 30, height: 40 })
    expect(readSvgSize('<svg>')).toEqual({ width: 1200, height: 800 })
  })

  it('writes a valid single page PDF with the JPEG', () => {
    const jpeg = new Uint8Array([0xff, 0xd8, 0xff, 0xd9])
    const pdf = imageToPdf({ bytes: jpeg, width: 400, height: 200 }, { title: 'Prüfung (Muster)' })
    const text = new TextDecoder('latin1').decode(pdf)
    expect(text.startsWith('%PDF-1.4')).toBe(true)
    expect(text).toContain('/Filter /DCTDecode')
    expect(text).toContain('/MediaBox [0 0 841.89 595.28]')
    expect(text).toContain('(Pr\xfcfung \\(Muster\\))')
    expect(text.trimEnd().endsWith('%%EOF')).toBe(true)
    const xref = Number(/startxref\n(\d+)/.exec(text)?.[1])
    expect(text.slice(xref, xref + 4)).toBe('xref')
    expect(pdfString('€')).toBe('(?)')
    expect(Math.round(pixelsToMm(96))).toBe(25)
  })
})

describe('translation', () => {
  it('merges tables and fills placeholders', () => {
    const t = createTranslator('de', { Extra: 'Zusatz' })
    expect(t('Create pool: {role}', { role: 'VB' })).toBe('Pool anlegen: VB')
    expect(t('Extra')).toBe('Zusatz')
    expect(t('Delete')).toBe('Löschen')
    expect(createTranslator('en')('Delete')).toBe('Delete')
    expect(Object.keys(translateModule())).toEqual(['translate'])
  })
})
