/** Gemeinsame Paritätsfälle der Risiko-Merkmale (Vue ↔ React); echte Antworten von auditcore_risk.web, synthetische Belege. */
import type { Evaluation, ProfileDetail, RiskPort } from '../../src'
import flowstatJson from '../fixtures/risk/evaluation-flowstat.json'
import profileJson from '../fixtures/risk/profile-year-bound.json'
import yearBoundJson from '../fixtures/risk/evaluation-year-bound.json'
import type { ParityCase } from './cases'

export const riskEvaluation = yearBoundJson as unknown as Evaluation
export const riskFlowstat = flowstatJson as unknown as Evaluation
export const riskProfile = profileJson as unknown as ProfileDetail

export interface RiskCaseProps {
  evaluation?: Evaluation | null
  profile?: ProfileDetail | null
  port?: RiskPort | null
  heading?: string
  locale?: 'de' | 'en'
}

/** Port, der nur die Profilbeschreibung liefert (oder mit `failure` scheitert). */
export function riskPort(failure?: string): RiskPort {
  return {
    profiles: async () => [],
    profile: async () => {
      if (failure) throw new Error(failure)
      return riskProfile
    },
    checkColumns: async () => ({ profile: riskEvaluation.profile, columns: [], complete: true, aborts: false, rules: [] }),
    evaluate: async () => riskEvaluation,
  }
}

export const riskCases: ReadonlyArray<ParityCase<RiskCaseProps>> = [
  {
    name: 'Auswertung mit Profil (Treffer und unbestimmte Merkmale)',
    props: () => ({ evaluation: riskEvaluation, profile: riskProfile }),
    expect: {
      texts: ['riskanalysis.year_bound', '2026.09.5', 'Nettobetrag fehlt in der Quelle (3)', '3 mit unbestimmtem Merkmal', 'Datensatz wählen', 'Profil und Eingabefelder'],
      roles: [['search', 'Filter'], ['heading', 'Risiko-Merkmale'], ['img', 'RF02: unbestimmt'], ['button', 'RF13']],
      counts: { '.fa-risk-table tbody tr': 10, '.fa-risk-profile': 1 },
    },
  },
  {
    name: 'übersprungene Regeln, Befunde über alle Datensätze, Altprofil',
    props: () => ({ evaluation: riskFlowstat, heading: 'Belegliste' }),
    expect: {
      texts: ['5 Regeln übersprungen', 'Spalten fehlen: zahlungsdatum', 'Befunde über alle Datensätze', 'BL_RF10_VENDOR_CONCENTRATION', 'charakterisiertes Altverhalten'],
      roles: [['heading', 'Belegliste']],
      counts: { '.fa-risk__hint[role="note"]': 1 },
    },
  },
  {
    name: 'fehlende Spalten bei weiterlaufenden Regeln',
    props: () => ({ evaluation: { ...riskEvaluation, missing_columns: { RF02: ['nettobetrag'] } } }),
    expect: { texts: ['Fehlende Spalten: nettobetrag'] },
  },
  {
    name: 'Profil über den Port nachgeladen',
    props: () => ({ evaluation: riskEvaluation, port: riskPort() }),
    expect: { texts: ['Profil und Eingabefelder', 'Wertgrenzen'], counts: { 'details.fa-risk__profile-info': 1 } },
  },
  {
    name: 'Ladefehler des Profils',
    props: () => ({ evaluation: riskEvaluation, port: riskPort('Netzwerkfehler') }),
    expect: { texts: ['Netzwerkfehler'], counts: { '.fa-risk__hint[role="alert"]': 1 } },
  },
  { name: 'ohne Auswertung', props: () => ({}), expect: { texts: ['0 von 0 Datensätzen', 'Keine Datensätze für diesen Filter.'] } },
  {
    name: 'englisch',
    props: () => ({ evaluation: riskEvaluation, locale: 'en' }),
    expect: { roles: [['heading', 'Risk flags'], ['search', 'Filter'], ['region', 'Distribution per flag']] },
  },
]
