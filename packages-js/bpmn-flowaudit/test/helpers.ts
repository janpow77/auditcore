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

/** Synthetic test profile (same structure as `auditcore_bpmn.profil/1`). */
export const TEST_PROFILE: ProfileData = {
  schema: 'auditcore_bpmn.profil/1',
  id: 'foerderperiode-2021-2027',
  version: '2026.09.1',
  titel: { de: 'Testprofil 2021–2027', en: 'Test profile 2021-2027' },
  foerderperiode: '2021-2027',
  rollen: ['vb', 'zgs', 'rfs', 'pb', 'pbs', 'kom', 'beg', 'bga', 'gut', 'ftd', 'sonstige'],
  fonds: ['efre', 'esf_plus'],
  kernanforderungen: {
    eintraege: Array.from({ length: 15 }, (_, i) => ({
      nummer: i + 1,
      titel: { de: `Kernanforderung ${i + 1}`, en: `Key requirement ${i + 1}` },
      bewertungskriterien: i === 1 ? [{ code: '2.3' }, { code: '2.4' }, { code: '2.6' }] : [],
    })),
  },
  rollen_aliase: [
    { muster: 'zwischengeschaltete Stelle', rolle: 'zgs' },
    { muster: 'Verwaltungsbehörde', rolle: 'vb' },
    { muster: 'Antragstell', rolle: 'beg' },
    { muster: 'Gutachter', rolle: 'gut' },
  ],
  funktionstrennung: [
    { id: 'FT01', typ: 'getrennte_stellen', schwere: 'warnung', a: { kennzeichen: ['bewilligung'] }, b: { kennzeichen: ['zahlung'] }, titel: { de: 'Bewilligung und Auszahlung in derselben Stelle', en: 'Approval and payment in the same body' } },
    { id: 'FT03', typ: 'rolle_ausgeschlossen', schwere: 'fehler', auswahl: { pruefart: ['verwk'] }, rollen: ['pb'], titel: { de: 'Verwaltungskontrolle durch die Prüfbehörde', en: 'Management verification by the audit authority' } },
    { id: 'FT05', typ: 'vier_augen', schwere: 'warnung', titel: { de: 'Vier-Augen-Prinzip ohne zweite Stelle oder Rolle', en: 'Four-eyes principle without a second body or role' } },
  ],
  rechtsgrundlagen: {
    eintraege: [
      { norm: 'VO (EU) 2021/1060', artikel: '74', kurzbezeichnung: { de: 'Verwaltungsprüfungen', en: 'Management verifications' }, celex: '32021R1060' },
      { norm: 'VO (EU) 2021/1060', artikel: '69', kurzbezeichnung: { de: 'Verantwortlichkeiten der Mitgliedstaaten', en: 'Responsibilities of Member States' } },
    ],
  },
}
