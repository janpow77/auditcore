import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { loadDefinitions } from '../src/model/load'
import { modelFromDefinitions } from '../src/model/buildModel'
import type { ProcessModel } from '../src/model/processModel'
import type { ProfileData } from '../src/profile/profile'

export function fixture(name: string): string {
  return readFileSync(join(process.cwd(), 'test', 'fixtures', name), 'utf-8')
}

export async function modelOf(xml: string): Promise<ProcessModel> {
  const loaded = await loadDefinitions(xml)
  return modelFromDefinitions(loaded.definitions)
}

/** Synthetic test profile (same structure as `auditcore_bpmn.profile/1`). */
export const TEST_PROFILE: ProfileData = {
  schema: 'auditcore_bpmn.profile/1',
  id: 'foerderperiode-2021-2027',
  version: '2026.09.1',
  title: { de: 'Testprofil 2021–2027', en: 'Test profile 2021-2027' },
  programming_period: '2021-2027',
  roles: ['vb', 'zgs', 'rfs', 'pb', 'pbs', 'kom', 'beg', 'bga', 'gut', 'ftd', 'sonstige'],
  funds: ['efre', 'esf_plus'],
  key_requirements: {
    entries: Array.from({ length: 15 }, (_, i) => ({
      number: i + 1,
      title: { de: `Kernanforderung ${i + 1}`, en: `Key requirement ${i + 1}` },
      assessment_criteria: i === 1 ? [{ code: '2.3' }, { code: '2.4' }, { code: '2.6' }] : [],
    })),
  },
  role_aliases: [
    { pattern: 'zwischengeschaltete Stelle', role: 'zgs' },
    { pattern: 'Verwaltungsbehörde', role: 'vb' },
    { pattern: 'Antragstell', role: 'beg' },
    { pattern: 'Gutachter', role: 'gut' },
  ],
  segregation_rules: [
    { id: 'FT01', kind: 'separate_bodies', severity: 'warnung', a: { markers: ['bewilligung'] }, b: { markers: ['zahlung'] }, title: { de: 'Bewilligung und Auszahlung in derselben Stelle', en: 'Approval and payment in the same body' } },
    { id: 'FT03', kind: 'excluded_role', severity: 'fehler', selection: { audit_types: ['verwk'] }, roles: ['pb'], title: { de: 'Verwaltungskontrolle durch die Prüfbehörde', en: 'Management verification by the audit authority' } },
    { id: 'FT05', kind: 'four_eyes', severity: 'warnung', title: { de: 'Vier-Augen-Prinzip ohne zweite Stelle oder Rolle', en: 'Four-eyes principle without a second body or role' } },
  ],
  legal_bases: {
    entries: [
      { act: 'VO (EU) 2021/1060', article: '74', short_title: { de: 'Verwaltungsprüfungen', en: 'Management verifications' }, celex: '32021R1060' },
      { act: 'VO (EU) 2021/1060', article: '69', short_title: { de: 'Verantwortlichkeiten der Mitgliedstaaten', en: 'Responsibilities of Member States' } },
    ],
  },
}
