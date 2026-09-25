import { existsSync, readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { RULES, ruleText } from '../src/validation/catalog'
import { countIssues, issueFromWire, issueMessage, severityLabel, sortIssues } from '../src/validation/issue'
import { validateModel } from '../src/validation/validate'
import { fixture, modelOf, TEST_PROFILE } from './helpers'

const ids = (report: ReturnType<typeof validateModel>) => report.issues.map((i) => `${i.ruleId}@${i.elementId ?? ''}`)

describe('rule catalogue', () => {
  it('fills placeholders and prefers localized parameters', () => {
    expect(ruleText(RULES['BPMN-F020'], 'de', { art: 'Lane', name: 'X' })).toBe('Lane „X“ hat keine Akteur-Rolle.')
    expect(ruleText(RULES['BPMN-F022'], 'en', { rolle: 'bb', bezeichnung: 'Bescheinigungsbehörde', bezeichnung_en: 'Certifying authority', name: 'L', periode: '2021-2027' })).toContain('Certifying authority')
  })

  it('is identical to the catalogue of auditcore_bpmn when present', () => {
    const base = join(process.cwd(), '../../packages/auditcore_bpmn/src/auditcore_bpmn')
    const candidates = existsSync(base) ? findPython(base) : []
    const sources = candidates.filter((file) => /texts_\w+\.py$/.test(file)).map((file) => readFileSync(file, 'utf-8'))
    if (!sources.length) return
    const pythonIds = sources.flatMap((source) => [...source.matchAll(/\(\s*"(BPMN-[A-Z0-9-]+)"/g)].map((m) => m[1])).sort()
    expect(Object.keys(RULES).sort()).toEqual(pythonIds)
  })
})

function findPython(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name)
    if (entry.isDirectory()) return entry.name.startsWith('_') ? [] : findPython(path)
    return entry.name.endsWith('.py') ? [path] : []
  })
}

describe('validateModel', () => {
  it('accepts the complete 1.1 example except expected domain issues', async () => {
    const report = validateModel(await modelOf(fixture('schema-1.1.bpmn')), { profile: TEST_PROFILE, referenceDate: '2026-09-25' })
    expect(report.valid).toBe(true)
    expect(ids(report)).toContain('BPMN-FT01@Task_Bewilligen')
    expect(ids(report)).toContain('BPMN-F020@Pool_Verwaltung')
    expect(ids(report)).toContain('BPMN-F001@Task_Nachfordern')
    expect(ids(report)).not.toContain('BPMN-P001@Task_Pruefen')
    expect(ids(report)).not.toContain('BPMN-P002@DataRef_Vermerk')
    expect(ids(report)).not.toContain('BPMN-P004@Task_Pruefen')
    // Four eyes within the same body and role: reported as in auditcore_bpmn.
    expect(ids(report)).toContain('BPMN-FT05@Task_Pruefen')
    expect(report.profile).toBe('foerderperiode-2021-2027@2026.09.1')
  })

  it('reports structure errors', async () => {
    const xml = `<?xml version="1.0"?><bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="D" targetNamespace="x">
      <bpmn:process id="P"><bpmn:task id="T" /><bpmn:exclusiveGateway id="G"><bpmn:outgoing>F1</bpmn:outgoing><bpmn:outgoing>F2</bpmn:outgoing></bpmn:exclusiveGateway>
      <bpmn:task id="A" name="A"/><bpmn:task id="B" name="B"/>
      <bpmn:sequenceFlow id="F1" sourceRef="G" targetRef="A"/><bpmn:sequenceFlow id="F2" sourceRef="G" targetRef="B"/></bpmn:process></bpmn:definitions>`
    const report = validateModel(await modelOf(xml))
    expect(ids(report)).toEqual(expect.arrayContaining(['BPMN-S010@P', 'BPMN-S011@P', 'BPMN-S012@T', 'BPMN-S050@T', 'BPMN-S032@G', 'BPMN-S051@G', 'BPMN-S013@G', 'BPMN-F002@']))
    expect(report.valid).toBe(false)
  })

  it('checks key requirements and criteria against the profile', async () => {
    const xml = fixture('schema-1.1.bpmn').replace('ka="2" bk="2.3" art="verwk"', 'ka="2" bk="3.1" art="prüfen"').replace('ka="4" bk="4.1" art="verwk" />', 'ka="16" />')
    const report = validateModel(await modelOf(xml), { profile: TEST_PROFILE, referenceDate: '2026-09-25' })
    expect(ids(report)).toEqual(expect.arrayContaining(['BPMN-F024@Task_Pruefen', 'BPMN-F026@Task_Pruefen', 'BPMN-F023@Task_VerwK']))
  })

  it('checks audit authority data (controls, risks, steps, findings)', async () => {
    const xml = fixture('schema-1.1.bpmn')
      .replace('nachweis="Prüfvermerk" ', '')
      .replace('<bpmn:dataOutputAssociation id="DOA_Vermerk">', '<bpmn:dataInputAssociation id="DOA_Vermerk">')
      .replace('</bpmn:dataOutputAssociation>', '</bpmn:dataInputAssociation>')
      .replace('kontrollen="K1" />\n        <flowaudit:verweis', 'kontrollen="K9" />\n        <flowaudit:verweis')
      .replace('ergebnis="erfuellt"', 'ergebnis="nicht_erfuellt"')
      .replace('aufbewahrungsort="eAkte" ', '')
    const report = validateModel(await modelOf(xml), { profile: TEST_PROFILE, referenceDate: '2026-09-25' })
    expect(ids(report)).toEqual(expect.arrayContaining(['BPMN-P006@Collaboration_Muster', 'BPMN-P010@Task_Pruefen', 'BPMN-P002@DataRef_Vermerk']))
    // A data association counts as evidence (as in auditcore_bpmn).
    expect(ids(report)).not.toContain('BPMN-P001@Task_Pruefen')
  })

  it('reports expired validity against the reference date', async () => {
    const report = validateModel(await modelOf(fixture('schema-1.1.bpmn')), { profile: TEST_PROFILE, referenceDate: '2028-01-01' })
    expect(ids(report)).toContain('BPMN-F005@Collaboration_Muster')
  })

  it('supports disabling rules', async () => {
    const report = validateModel(await modelOf(fixture('schema-1.1.bpmn')), { profile: TEST_PROFILE, disabled: ['BPMN-F001', 'BPMN-FT01'] })
    expect(report.issues.some((i) => i.ruleId === 'BPMN-F001' || i.ruleId === 'BPMN-FT01')).toBe(false)
  })
})

describe('issues', () => {
  it('sorts, counts, labels and converts server issues', () => {
    const list = [
      { ruleId: 'BPMN-F001', severity: 'hinweis' as const, params: { name: 'A' } },
      { ruleId: 'BPMN-S010', severity: 'fehler' as const, params: { name: 'P' } },
    ]
    expect(sortIssues(list)[0].ruleId).toBe('BPMN-S010')
    expect(countIssues(list)).toEqual({ fehler: 1, warnung: 0, hinweis: 1 })
    expect(severityLabel('warnung', 'en')).toBe('Warning')
    expect(issueMessage(list[0])).toBe('Aufgabe „A“ hat keine Rechtsgrundlage.')
    const wire = issueFromWire({ rule_id: 'BPMN-S010', severity: 'fehler', message: 'Vom Server', element_id: 'P', params: {} })
    expect(wire).toMatchObject({ ruleId: 'BPMN-S010', elementId: 'P' })
    expect(issueMessage(wire)).toBe('Vom Server')
  })
})
