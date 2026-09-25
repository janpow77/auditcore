/**
 * Standard catalogue of roles (bodies) for pools and lanes.
 *
 * Codes and labels match `auditcore_bpmn.vocab.ROLLEN`. Colours of the four
 * most frequent roles follow the colour-by-actor convention found in the
 * analysed diagrams (MA, IB, beneficiaries, technical body/committee).
 * Display names such as the name of a body in a programme are never part of
 * the library; applications configure them.
 */

import type { Label } from './vocabulary'

export interface Role {
  code: string
  label: Label
  /** Short form for palette and plaque, e.g. „VB“. */
  short: string
  /** First start year of a programming period in which the role exists. */
  fromYear?: number
  /** Last start year of a programming period in which the role exists. */
  untilYear?: number
  /** Default colours of the pool/lane header. */
  color: { fill: string; stroke: string }
  /** Icon name in the icon set. */
  icon: string
}

type RoleRow = [code: string, de: string, en: string, short: string, fill: string, stroke: string, fromYear?: number, untilYear?: number]

const ROWS: RoleRow[] = [
  ['vb', 'Verwaltungsbehörde', 'Managing authority', 'VB', '#fdf2e0', '#9a5b00'],
  ['zgs', 'Zwischengeschaltete Stelle', 'Intermediate body', 'ZGS', '#eaf3ea', '#2e6b30'],
  ['rfs', 'Stelle mit Rechnungsführungsfunktion (Art. 76 CPR)', 'Body carrying out the accounting function', 'RFS', '#fff6d6', '#7a6200', 2021],
  ['bb', 'Bescheinigungsbehörde', 'Certifying authority', 'BB', '#fff1e0', '#8a4b00', undefined, 2014],
  ['pb', 'Prüfbehörde', 'Audit authority', 'PB', '#fde8ec', '#9c1c3c'],
  ['pbs', 'Programmbeteiligte Stelle', 'Body involved in the programme', 'PBS', '#e9f4f4', '#1d6464'],
  ['kom', 'Europäische Kommission', 'European Commission', 'KOM', '#e6eefc', '#1f4aa8'],
  ['beg', 'Begünstigte', 'Beneficiary', 'BEG', '#e8eef7', '#34507a'],
  ['bga', 'Begleitausschuss', 'Monitoring committee', 'BGA', '#efe9f7', '#5b3d8a'],
  ['gs', 'Gemeinsames Sekretariat (Interreg)', 'Joint secretariat (Interreg)', 'GS', '#e7f3fb', '#1b5f86'],
  ['gdp', 'Gruppe von Prüfern (Interreg)', 'Group of auditors (Interreg)', 'GdP', '#fbe9f1', '#8a2457'],
  ['fb', 'Fachbehörde/Bewilligungsstelle', 'Granting body', 'FB', '#edf6e8', '#3f6a1f'],
  ['ftd', 'Fachtechnische Dienststelle', 'Technical body', 'FTD', '#f2eef7', '#5a4a7a'],
  ['gut', 'Gutachter/Sachverständige', 'Expert/assessor', 'GUT', '#f4efe6', '#6b5433'],
  ['gre', 'Gremium', 'Committee', 'GRE', '#f2eef7', '#5a4a7a'],
  ['fr', 'Fachreferat', 'Specialist unit', 'FR', '#f0f1e6', '#5b5f22'],
  ['ds', 'Datenschutz', 'Data protection', 'DS', '#eceff4', '#3c4a5e'],
  ['it', 'IT-System', 'IT system', 'IT', '#e8f1f8', '#23577d'],
  ['sonstige', 'Sonstige Stelle', 'Other body', '…', '#f1f3f5', '#4a5563'],
]

export const ROLES: Record<string, Role> = Object.fromEntries(
  ROWS.map(([code, de, en, short, fill, stroke, fromYear, untilYear]) => [
    code,
    { code, label: { de, en }, short, color: { fill, stroke }, icon: `role-${code}`, fromYear, untilYear },
  ]),
)

/** Start year from `YYYY-YYYY`, otherwise `null`. */
export function periodStart(fundingPeriod: string | undefined | null): number | null {
  if (!fundingPeriod || !/^\d{4}-\d{4}$/.test(fundingPeriod)) return null
  return Number(fundingPeriod.slice(0, 4))
}

/** `true` if the role exists in the programming period (unknown period: yes). */
export function roleAppliesTo(role: Role, fundingPeriod: string | undefined | null): boolean {
  const start = periodStart(fundingPeriod)
  if (start === null) return true
  if (role.fromYear !== undefined && start < role.fromYear) return false
  return !(role.untilYear !== undefined && start > role.untilYear)
}
