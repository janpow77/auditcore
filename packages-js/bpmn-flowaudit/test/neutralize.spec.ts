import { describe, expect, it } from 'vitest'
import { neutralize } from '../src/neutralize/neutralize'
import { fixture, modelOf, TEST_PROFILE } from './helpers'

const SENSITIVE = `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:flowaudit="https://flowaudit.de/bpmn/schema/1.0" id="D" targetNamespace="x">
  <bpmn:process id="P">
    <bpmn:task id="T1" name="Musterbank: Zahlung freigeben">
      <bpmn:documentation>Rückfragen an Herr Beispielmann (max.beispiel@musterbank.example), Betrag 12.345,67 EUR, IBAN DE44 5001 0517 5407 3249 31, SAP-Nr. 4711234, MaStR-Nr. SEE912345678901, Muster Solar GmbH. Feststellung T15 F1 und Themenvermerk T07.</bpmn:documentation>
      <bpmn:extensionElements>
        <flowaudit:interneNotiz>intern</flowaudit:interneNotiz>
        <flowaudit:kennzeichen typ="feststellung" />
        <flowaudit:kennzeichen typ="zahlung" />
        <flowaudit:pruefschritt id="PS1" pruefer="Erika Beispiel" ergebnis="erfuellt" />
        <flowaudit:quelle art="interview" fundstelle="Gespräch am 01.02." />
        <flowaudit:verweis art="feststellung_ref" schluessel="T15 F1" />
        <flowaudit:verweis art="prueffeld" schluessel="3.21" />
        <flowaudit:rechtsgrundlage vertraulich="true">geheim</flowaudit:rechtsgrundlage>
        <flowaudit:rechtsgrundlage>§ 70 LHO</flowaudit:rechtsgrundlage>
      </bpmn:extensionElements>
    </bpmn:task>
  </bpmn:process>
</bpmn:definitions>`

describe('neutralize', () => {
  it('replaces display names of pools and lanes by role labels everywhere', async () => {
    const result = neutralize(fixture('schema-1.1.bpmn'), { profile: TEST_PROFILE })
    const model = await modelOf(result.xml)
    expect(model.byId.get('Lane_ZGS')?.name).toBe('Zwischengeschaltete Stelle')
    expect(model.byId.get('Lane_VB')?.name).toBe('Verwaltungsbehörde')
    expect(model.byId.get('Pool_Beg')?.name).toBe('Begünstigte')
    expect(model.byId.get('Lane_ZGS')?.extensions.actor).toEqual({ role: 'zgs' })
    expect(result.xml).not.toContain('Musterförderbank')
    expect(result.xml).not.toContain('Musterfirma')
  })

  it('removes names, e-mails, amounts and identifiers from texts', () => {
    const result = neutralize(SENSITIVE, { profile: TEST_PROFILE, replacements: { Musterbank: 'Zwischengeschaltete Stelle' } })
    for (const secret of ['Beispielmann', 'max.beispiel', '12.345,67', 'DE44', '4711234', 'SEE912345678901', 'Muster Solar GmbH', 'Musterbank', 'T15 F1', 'T07']) {
      expect(result.xml).not.toContain(secret)
    }
    expect(result.xml).toContain('Zwischengeschaltete Stelle: Zahlung freigeben')
    expect(result.xml).toContain('[E-Mail entfernt]')
    expect(result.xml).toContain('[Betrag entfernt]')
  })

  it('removes internal notes, audit steps, finding data and confidential entries', () => {
    const result = neutralize(SENSITIVE, { profile: TEST_PROFILE })
    for (const tag of ['interneNotiz', 'pruefschritt', 'typ="feststellung"', 'art="interview"', 'feststellung_ref', 'geheim', 'Erika']) {
      expect(result.xml).not.toContain(tag)
    }
    expect(result.xml).toContain('typ="zahlung"')
    expect(result.xml).toContain('schluessel="3.21"')
    expect(result.xml).toContain('§ 70 LHO')
  })

  it('removes person fields of the diagram info and finding colours', () => {
    const result = neutralize(fixture('enrichment.bpmn').replace('id="Collaboration_A">', 'id="Collaboration_A"><bpmn:extensionElements><flowaudit:diagrammInfo xmlns:flowaudit="https://flowaudit.de/bpmn/schema/1.0" autor="Erika Musterfrau" freigegebenDurch="Max Muster" titel="T"/></bpmn:extensionElements>'), { profile: TEST_PROFILE })
    expect(result.xml).not.toContain('Erika Musterfrau')
    expect(result.xml).not.toContain('Max Muster')
    expect(result.xml).not.toContain('#fce8e6')
    expect(result.xml).not.toContain('#cc0000')
    expect(result.xml).toContain('#c8e6c9')
  })

  it('reports every change with counts per kind', () => {
    const result = neutralize(SENSITIVE, { profile: TEST_PROFILE, withOriginals: true })
    expect(result.summary.email).toBe(1)
    expect(result.summary.betrag).toBe(1)
    expect(result.summary.iban).toBe(1)
    expect(result.summary.kennnummer).toBe(2)
    expect(result.summary.unternehmen).toBe(1)
    expect(result.summary.person).toBeGreaterThanOrEqual(1)
    expect(result.summary.entfernt).toBeGreaterThanOrEqual(6)
    expect(result.replacements.find((r) => r.kind === 'email')?.original).toBe('max.beispiel@musterbank.example')
    expect(neutralize(SENSITIVE).replacements.every((r) => r.original === undefined)).toBe(true)
  })

  it('numbers bodies without role as „Stelle n“', () => {
    const xml = fixture('enrichment.bpmn')
    const result = neutralize(xml, { profile: null })
    expect(result.xml).toContain('name="Stelle 1"')
  })

  it('rejects malformed XML', () => {
    expect(() => neutralize('<nicht')).toThrow('wohlgeformt')
  })
})
