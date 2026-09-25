import { describe, expect, it } from 'vitest'
import { changeLabel, checkTargetActual, colorsFromMarkers, compareVersions, diffColors, isUnchanged, synopsis } from '../src/compare/compare'
import { category, matchElements, normalName } from '../src/compare/matching'
import { suggestCategories } from '../src/reports/categorySuggestion'
import { findingsList, flowOrder, processTable, PROCESS_TABLE_COLUMNS, riskControlMatrix, walkthroughOverview } from '../src/reports/processReports'
import { toCsv, toMyst } from '../src/reports/tables'
import { fixture, modelOf, TEST_PROFILE } from './helpers'

describe('compareVersions', () => {
  it('finds no change between identical versions', async () => {
    const model = await modelOf(fixture('schema-1.1.bpmn'))
    expect(isUnchanged(compareVersions(model, await modelOf(fixture('schema-1.1.bpmn'))))).toBe(true)
  })

  it('classifies added, removed and changed elements and builds a synopsis', async () => {
    const before = await modelOf(fixture('schema-1.1.bpmn'))
    const changedXml = fixture('schema-1.1.bpmn')
      .replace('name="Mittel auszahlen"', 'name="Mittel anweisen"')
      .replace('<bpmn:task id="Task_Nachfordern" name="Unterlagen nachfordern">', '<bpmn:task id="Task_Nachfordern_Neu" name="Unterlagen per Portal nachfordern">')
      .replace(/targetRef="Task_Nachfordern"/g, 'targetRef="Task_Nachfordern_Neu"')
      .replace(/sourceRef="Task_Nachfordern"/g, 'sourceRef="Task_Nachfordern_Neu"')
      .replace(/<bpmn:flowNodeRef>Task_Nachfordern<\/bpmn:flowNodeRef>/, '<bpmn:flowNodeRef>Task_Nachfordern_Neu</bpmn:flowNodeRef>')
      .replace('bpmnElement="Task_Nachfordern"', 'bpmnElement="Task_Nachfordern_Neu"')
    const comparison = compareVersions(before, await modelOf(changedXml))
    const kinds = Object.fromEntries(comparison.changes.map((c) => [c.newId ?? c.oldId, c.kind]))
    expect(kinds.Task_Auszahlen).toBe('geaendert')
    expect(kinds.Task_Nachfordern).toBe('entfallen')
    expect(kinds.Task_Nachfordern_Neu).toBe('hinzugefuegt')
    expect(kinds.Gateway_Vollst).toBe('geaendert')
    const rows = synopsis(comparison)
    expect(rows.find((r) => r.field === 'name')).toMatchObject({ before: 'Mittel auszahlen', after: 'Mittel anweisen', change: 'geändert' })
    const [old, now] = diffColors(comparison)
    expect(old.get('Task_Nachfordern')).toBe('entfallen')
    expect(now.get('Task_Nachfordern_Neu')).toBe('hinzugefuegt')
    expect(changeLabel('hinzugefuegt')).toBe('hinzugefügt')
  })

  it('matches renamed ids by type and name', async () => {
    const before = await modelOf(fixture('legacy-1.0.bpmn'))
    const after = await modelOf(fixture('legacy-1.0.bpmn').replace(/Task_Pruefen/g, 'Task_X'))
    expect(matchElements(before, after).get('Task_Pruefen')).toBe('Task_X')
    expect(normalName('  Antrag   Prüfen ')).toBe('antrag prüfen')
    expect(category('bpmn:DataStoreReference')).toBe('daten')
  })
})

describe('checkTargetActual', () => {
  it('reports met and not met elements with reasons', async () => {
    const target = await modelOf(fixture('schema-1.1.bpmn'))
    const actualXml = fixture('schema-1.1.bpmn')
      .replace('<flowaudit:kontrolle id="K1"', '<flowaudit:kontrolle id="K2"')
      .replace('bezeichnung="Vier-Augen-Prüfung der Checkliste"', 'bezeichnung="Sichtprüfung"')
      .replace('ergebnis="erfuellt"', 'ergebnis="nicht_erfuellt"')
    const check = checkTargetActual(target, await modelOf(actualXml))
    const pruefen = check.results.find((r) => r.targetId === 'Task_Pruefen')
    expect(pruefen?.met).toBe(false)
    expect(pruefen?.reasons.join(' ')).toContain('Kontrolle fehlt im Ist: Vier-Augen-Prüfung der Checkliste.')
    expect(pruefen?.reasons.join(' ')).toContain('Prüfschritt im Ist nicht erfüllt.')
    expect(check.results.find((r) => r.targetId === 'Task_Auszahlen')?.met).toBe(true)
    expect(check.met + check.notMet).toBe(check.results.length)
  })

  it('derives colours from markers with precedence', async () => {
    const colors = colorsFromMarkers(await modelOf(fixture('schema-1.1.bpmn')))
    expect(colors.get('Task_Bewilligen')).toEqual({ fill: '#fce8e6', stroke: '#b3261e' })
    expect(colors.has('Task_Pruefen')).toBe(false)
  })
})

describe('reports', () => {
  it('orders flow nodes from the start event', async () => {
    const order = flowOrder(await modelOf(fixture('schema-1.1.bpmn'))).map((el) => el.id)
    expect(order.indexOf('Task_Pruefen')).toBeLessThan(order.indexOf('Task_Auszahlen'))
  })

  it('builds the process table with actor, legal basis, control, evidence, system, deadline and KA/BK', async () => {
    const rows = processTable(await modelOf(fixture('schema-1.1.bpmn')))
    const pruefen = rows.find((r) => r.element_id === 'Task_Pruefen')
    expect(pruefen).toMatchObject({
      akteur: 'Zwischengeschaltete Stelle (Musterförderbank)',
      rechtsgrundlage: 'Artikel 73 Absatz 2 Buchstabe b der Verordnung (EU) 2021/1060',
      kontrolle: 'Vier-Augen-Prüfung der Checkliste (Schlüsselkontrolle)',
      nachweis: 'Prüfvermerk; Prüfvermerk (eAkte)',
      it_system: 'Fördersystem',
      ka_bk: 'KA 2 · BK 2.3',
    })
    const csv = toCsv(rows, PROCESS_TABLE_COLUMNS)
    expect(csv.split('\n')[0]).toBe('Nr.;Schritt;Akteur;Rechtsgrundlage;Kontrolle;Nachweis;IT-System;Frist;KA/BK')
    expect(toMyst(rows, PROCESS_TABLE_COLUMNS, { title: 'Prozess', label: 'p' })).toContain('(p)=\n## Prozess')
  })

  it('builds risk-control matrix, findings list and walk-through overview', async () => {
    const model = await modelOf(fixture('schema-1.1.bpmn'))
    const rcm = riskControlMatrix(model)
    expect(rcm.find((r) => r.risiko_id === 'R1')).toMatchObject({ kontrolle_id: 'K1', schluesselkontrolle: 'ja', test: 'erfuellt' })
    expect(rcm.find((r) => r.risiko_id === 'R_Gesamt')?.ort).toBe('Antrag prüfen')
    expect(findingsList(model)[0]).toMatchObject({ kennung: 'T15 F1', art: 'formell', element: 'Zuwendung bewilligen' })
    const overview = walkthroughOverview(model)
    expect(overview.results).toEqual({ erfuellt: 1 })
    expect(overview.notWalkedThrough).toContain('Task_Auszahlen')
  })

  it('escapes CSV and MyST cells', () => {
    expect(toCsv([{ a: 'x;y', b: 'mit "Anführung"' }], undefined, { bom: true })).toBe('﻿a;b\n"x;y";"mit ""Anführung"""\n')
    expect(toMyst([{ a: 'x|y' }])).toContain('x\\|y')
  })

  it('suggests functioning categories per key requirement', async () => {
    const suggestions = suggestCategories([await modelOf(fixture('schema-1.1.bpmn'))], TEST_PROFILE)
    expect(suggestions.find((s) => s.keyRequirement === 2)).toMatchObject({ category: 2, findings: ['T15 F1'] })
    expect(suggestions.find((s) => s.keyRequirement === 4)).toMatchObject({ category: 1 })
    expect(suggestions.find((s) => s.keyRequirement === 7)?.category).toBeNull()
    expect(suggestions[0].note).toContain('Vorschlag')
  })
})
