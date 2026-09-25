/**
 * Controlled vocabularies of schema 1.1 (German and English labels).
 *
 * Same content as `auditcore_bpmn.vocab`. Codes are the XML values and stay
 * German. Generally valid for all shared-management funds and all audit
 * authorities: no state, authority or programme names.
 */

export type Locale = 'de' | 'en'
export type Label = { de: string; en: string }
export type Vocabulary = Record<string, Label>

export function label(value: Partial<Label> | undefined, locale: Locale = 'de'): string {
  if (!value) return ''
  return value[locale] || value.de || Object.values(value)[0] || ''
}

function vocabulary(entries: Record<string, [string, string]>): Vocabulary {
  return Object.fromEntries(Object.entries(entries).map(([code, [de, en]]) => [code, { de, en }]))
}

export const DIAGRAM_STATUS = vocabulary({
  entwurf: ['Entwurf', 'Draft'],
  in_pruefung: ['in Prüfung', 'under review'],
  freigegeben: ['freigegeben', 'approved'],
  archiviert: ['archiviert', 'archived'],
})

export const MARKER_TYPES = vocabulary({
  rechtsgrundlage: ['Rechtsgrundlage', 'Legal basis'],
  pruefpunkt: ['Prüfpunkt', 'Check point'],
  frist: ['Frist', 'Deadline'],
  vier_augen: ['Vier-Augen-Prinzip', 'Four-eyes principle'],
  dokument: ['Dokument', 'Document'],
  risiko: ['Risiko', 'Risk'],
  system: ['IT-System', 'IT system'],
  zahlung: ['Zahlung', 'Payment'],
  bewilligung: ['Bewilligung', 'Approval of support'],
  schluesselkontrolle: ['Schlüsselkontrolle', 'Key control'],
  checkliste: ['Checkliste', 'Checklist'],
  bescheid: ['Bescheid', 'Decision'],
  stellungnahme: ['Stellungnahme', 'Opinion'],
  gremium: ['Gremium', 'Committee'],
  interessenkonflikt: ['Interessenkonflikt', 'Conflict of interest'],
  veroeffentlichung: ['Veröffentlichung', 'Publication'],
  feststellung: ['Feststellung', 'Finding'],
  feststellung_formell: ['formelle Feststellung', 'Formal finding'],
  feststellung_finanziell: ['finanzielle Feststellung', 'Financial finding'],
  offener_nachweis: ['offener Nachweis', 'Open evidence'],
  ohne_befund: ['ohne Befund', 'No finding'],
  soll_ohne_regelung: ['Soll ohne Regelung (Lücke)', 'Target without rule (gap)'],
})

/** Colours derived from markers (fill, stroke). */
export const MARKER_COLORS: Record<string, { fill: string; stroke: string }> = {
  feststellung: { fill: '#fce8e6', stroke: '#b3261e' },
  feststellung_formell: { fill: '#fce8e6', stroke: '#b3261e' },
  feststellung_finanziell: { fill: '#fce8e6', stroke: '#b3261e' },
  soll_ohne_regelung: { fill: '#ffe0e0', stroke: '#cc0000' },
  ohne_befund: { fill: '#c8e6c9', stroke: '#1b5e20' },
  offener_nachweis: { fill: '#bbdefb', stroke: '#0d47a1' },
}

/** Precedence when several colouring markers sit on one element. */
export const MARKER_COLOR_PRECEDENCE = [
  'feststellung_finanziell',
  'feststellung_formell',
  'feststellung',
  'soll_ohne_regelung',
  'offener_nachweis',
  'ohne_befund',
] as const

export const AUDIT_TYPES = vocabulary({
  verwk: ['Verwaltungskontrolle (VerwK)', 'Management verification'],
  systempruefung: ['Systemprüfung', 'System audit'],
  vorhabenpruefung: ['Vorhabenprüfung', 'Audit of operations'],
  rechnungslegungspruefung: ['Prüfung der Rechnungslegung', 'Audit of accounts'],
})

export const FUNDS = vocabulary({
  efre: ['Europäischer Fonds für regionale Entwicklung (EFRE)', 'ERDF'],
  esf_plus: ['Europäischer Sozialfonds Plus (ESF+)', 'ESF+'],
  esf: ['Europäischer Sozialfonds (ESF)', 'ESF'],
  kf: ['Kohäsionsfonds', 'Cohesion Fund'],
  jtf: ['Fonds für einen gerechten Übergang (JTF)', 'Just Transition Fund'],
  emfaf: ['Europäischer Meeres-, Fischerei- und Aquakulturfonds (EMFAF)', 'EMFAF'],
  emff: ['Europäischer Meeres- und Fischereifonds (EMFF)', 'EMFF'],
  eler: ['Europäischer Landwirtschaftsfonds für die Entwicklung des ländlichen Raums (ELER)', 'EAFRD'],
  amif: ['Asyl-, Migrations- und Integrationsfonds (AMIF)', 'AMIF'],
  isf: ['Fonds für die innere Sicherheit (ISF)', 'ISF'],
  bmvi: ['Instrument für Grenzverwaltung und Visumpolitik (BMVI)', 'BMVI'],
  interreg: ['Interreg (Europäische territoriale Zusammenarbeit)', 'Interreg'],
})

export const FUND_SHORT: Record<string, string> = {
  efre: 'EFRE',
  esf_plus: 'ESF+',
  esf: 'ESF',
  kf: 'KF',
  jtf: 'JTF',
  emfaf: 'EMFAF',
  emff: 'EMFF',
  eler: 'ELER',
  amif: 'AMIF',
  isf: 'ISF',
  bmvi: 'BMVI',
  interreg: 'Interreg',
}

export const FUNDING_PERIODS = vocabulary({
  '2014-2020': ['Förderperiode 2014–2020', 'Programming period 2014-2020'],
  '2021-2027': ['Förderperiode 2021–2027', 'Programming period 2021-2027'],
  '2028-2034': ['Förderperiode 2028–2034', 'Programming period 2028-2034'],
})

export const CONTROL_KINDS = vocabulary({ praeventiv: ['präventiv', 'preventive'], aufdeckend: ['aufdeckend', 'detective'] })
export const CONTROL_EXECUTION = vocabulary({
  manuell: ['manuell', 'manual'],
  it_gestuetzt: ['IT-gestützt', 'IT-supported'],
  automatisiert: ['automatisiert', 'automated'],
})
export const RISK_CATEGORIES = vocabulary({
  allgemein: ['allgemeines Risiko', 'general risk'],
  betrug: ['Betrugsrisiko', 'fraud risk'],
  interessenkonflikt: ['Interessenkonflikt', 'conflict of interest'],
  doppelfinanzierung: ['Doppelfinanzierung', 'double funding'],
})
export const RISK_LEVELS = vocabulary({ niedrig: ['niedrig', 'low'], mittel: ['mittel', 'medium'], hoch: ['hoch', 'high'] })
export const TEST_RESULTS = vocabulary({
  erfuellt: ['erfüllt', 'met'],
  nicht_erfuellt: ['nicht erfüllt', 'not met'],
  nicht_anwendbar: ['nicht anwendbar', 'not applicable'],
  offen: ['offen', 'open'],
})
export const FINDING_KINDS = vocabulary({
  formell: ['formelle Feststellung', 'formal finding'],
  finanziell: ['finanzielle Feststellung', 'financial finding'],
})
export const FINDING_SEVERITIES = vocabulary({
  gering: ['gering', 'minor'],
  mittel: ['mittel', 'moderate'],
  schwerwiegend: ['schwerwiegend', 'serious'],
})
export const FINDING_STATUS = vocabulary({
  offen: ['offen', 'open'],
  in_umsetzung: ['in Umsetzung', 'in progress'],
  umgesetzt: ['umgesetzt', 'implemented'],
  nicht_umgesetzt: ['nicht umgesetzt', 'not implemented'],
  entfallen: ['entfallen', 'withdrawn'],
})
export const SOURCE_KINDS = vocabulary({
  verfahrenshandbuch: ['Verfahrenshandbuch', 'Procedures manual'],
  interview: ['Interview', 'Interview'],
  durchlauftest: ['Durchlauftest', 'Walk-through test'],
  arbeitspapier: ['Arbeitspapier', 'Working paper'],
  sonstige: ['sonstige Quelle', 'other source'],
})
export const DEADLINE_UNITS = vocabulary({
  tage: ['Tage', 'days'],
  arbeitstage: ['Arbeitstage', 'working days'],
  wochen: ['Wochen', 'weeks'],
  monate: ['Monate', 'months'],
  jahre: ['Jahre', 'years'],
})
export const CONFIDENTIALITY = vocabulary({
  offen: ['offen', 'public'],
  intern: ['intern', 'internal'],
  vs_nfd: ['VS – Nur für den Dienstgebrauch', 'restricted'],
})
export const VARIANTS = vocabulary({ soll: ['Soll', 'target'], ist: ['Ist', 'actual'] })
export const KEY_REFERENCE_KINDS = vocabulary({
  prueffeld: ['Prüffeld', 'Checklist item'],
  feststellung_ref: ['Feststellung', 'Finding reference'],
  register: ['Register der Prüfungsakte', 'Audit file register'],
})
export const FUNCTIONING_CATEGORIES = vocabulary({
  '1': ['Gute Funktionsfähigkeit. Keine oder lediglich geringfügige Verbesserungen erforderlich.', 'Works well. No or only minor improvement needed.'],
  '2': ['Funktionsfähigkeit vorhanden. Bestimmte Verbesserungen erforderlich.', 'Works. Some improvement needed.'],
  '3': ['Funktionsfähigkeit teilweise gegeben. Erhebliche Verbesserungen erforderlich.', 'Works partially. Substantial improvement needed.'],
  '4': ['Funktionsfähigkeit im Wesentlichen nicht vorhanden.', 'Essentially does not work.'],
})

/** Names of all vocabularies, for panels and validation messages. */
export const VOCABULARIES = {
  status: DIAGRAM_STATUS,
  markers: MARKER_TYPES,
  auditTypes: AUDIT_TYPES,
  funds: FUNDS,
  fundingPeriods: FUNDING_PERIODS,
  controlKinds: CONTROL_KINDS,
  controlExecution: CONTROL_EXECUTION,
  riskCategories: RISK_CATEGORIES,
  riskLevels: RISK_LEVELS,
  testResults: TEST_RESULTS,
  findingKinds: FINDING_KINDS,
  findingSeverities: FINDING_SEVERITIES,
  findingStatus: FINDING_STATUS,
  sourceKinds: SOURCE_KINDS,
  deadlineUnits: DEADLINE_UNITS,
  confidentiality: CONFIDENTIALITY,
  variants: VARIANTS,
  keyReferenceKinds: KEY_REFERENCE_KINDS,
} as const

export type VocabularyName = keyof typeof VOCABULARIES
