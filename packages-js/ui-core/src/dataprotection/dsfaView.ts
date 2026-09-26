// View-Logik der Datenschutz-Folgenabschätzung, ohne Vue und ohne DOM.
// Schwellwertanalyse, Brutto-/Nettorisiko und Vorschlag rechnet ausschließlich
// die Bibliothek (Port `calculate` bzw. gespeicherter Vorschlag); hier werden
// nur Eingaben verwaltet und Ergebnisse für die Anzeige eingeordnet.

import type { BadgeTone } from '../base/types'
import type {
  AnswerInput,
  AnswerValue,
  AssessmentView,
  BlockView,
  LevelView,
  DataProtectionProfile,
  Proposal,
  ScenarioInput,
  SurveyInput,
} from './types'

export const ANSWER_VALUES: readonly AnswerValue[] = ['ja', 'nein', 'unbekannt']

export interface TabItem {
  key: string
  label: string
}

export interface BlockProgress {
  answered: number
  total: number
  yes: number
}

function residualFrom(raw: Partial<ScenarioInput>): Pick<ScenarioInput, 'residual_severity' | 'residual_likelihood' | 'residual_justification'> {
  return {
    residual_severity: raw.residual_severity ?? null,
    residual_likelihood: raw.residual_likelihood ?? null,
    residual_justification: raw.residual_justification ?? '',
  }
}

function scenarioFrom(raw: Partial<ScenarioInput>, profile: DataProtectionProfile): ScenarioInput {
  const middle = Math.ceil((profile.risk.scale_min + profile.risk.scale_max) / 2)
  return {
    dimension: raw.dimension ?? profile.risk.dimensions[0]?.key ?? '',
    description: raw.description ?? '',
    severity: raw.severity ?? middle,
    likelihood: raw.likelihood ?? middle,
    measures: [...(raw.measures ?? [])],
    ...residualFrom(raw),
  }
}

export function emptyScenario(profile: DataProtectionProfile): ScenarioInput {
  return scenarioFrom({}, profile)
}

/** Bearbeitbare Kopie der gespeicherten Erhebung. */
export function surveyFrom(view: AssessmentView, profile: DataProtectionProfile): SurveyInput {
  const answers: Record<string, AnswerInput> = {}
  for (const [key, answer] of Object.entries(view.answers)) answers[key] = { value: answer.value, justification: answer.justification ?? '' }
  return {
    answers,
    scenarios: view.scenarios.map((scenario) => scenarioFrom(scenario, profile)),
    necessity: view.necessity,
    proportionality: view.proportionality,
    dossier: { ...view.dossier },
  }
}

export function sameSurvey(a: SurveyInput | null, b: SurveyInput | null): boolean {
  return JSON.stringify(a) === JSON.stringify(b)
}

export function answerOf(survey: SurveyInput, key: string): AnswerValue | null {
  return survey.answers[key]?.value ?? null
}

export function withAnswer(survey: SurveyInput, key: string, value: AnswerValue): SurveyInput {
  const previous = survey.answers[key]
  return { ...survey, answers: { ...survey.answers, [key]: { value, justification: previous?.justification ?? '' } } }
}

export function withJustification(survey: SurveyInput, key: string, justification: string): SurveyInput {
  const previous = survey.answers[key] ?? { value: 'unbekannt' as AnswerValue, justification: '' }
  return { ...survey, answers: { ...survey.answers, [key]: { ...previous, justification } } }
}

export function blockProgress(block: BlockView, survey: SurveyInput): BlockProgress {
  const values = block.questions.map((question) => answerOf(survey, question.key))
  return {
    answered: values.filter((value) => value === 'ja' || value === 'nein').length,
    total: values.length,
    yes: values.filter((value) => value === 'ja').length,
  }
}

export function withScenario(survey: SurveyInput, index: number, scenario: ScenarioInput): SurveyInput {
  const scenarios = survey.scenarios.slice()
  scenarios[index] = scenario
  return { ...survey, scenarios }
}

export function addScenario(survey: SurveyInput, profile: DataProtectionProfile): SurveyInput {
  return { ...survey, scenarios: [...survey.scenarios, emptyScenario(profile)] }
}

export function removeScenario(survey: SurveyInput, index: number): SurveyInput {
  return { ...survey, scenarios: survey.scenarios.filter((_, position) => position !== index) }
}

export function toggleMeasure(scenario: ScenarioInput, measure: string): ScenarioInput {
  const measures = scenario.measures.includes(measure)
    ? scenario.measures.filter((key) => key !== measure)
    : [...scenario.measures, measure]
  return { ...scenario, measures }
}

export function levelLabel(levels: readonly LevelView[], value: number | null): string {
  if (value === null) return ''
  return levels.find((level) => level.value === value)?.label ?? String(value)
}

/** Stufe eines Risikos nach Rang im Profil: höchste Stufe rot, zweithöchste gelb. */
export function bandTone(band: string | undefined, bands: readonly string[]): BadgeTone {
  const rank = band ? bands.indexOf(band) : -1
  if (rank <= 0) return 'neutral'
  if (rank === bands.length - 1) return 'danger'
  return rank === bands.length - 2 ? 'warning' : 'success'
}

const RECOMMENDATION_TONES: Readonly<Record<string, BadgeTone>> = {
  freigabe: 'success',
  freigabe_mit_auflagen: 'warning',
  konsultation_aufsichtsbehoerde: 'danger',
  verworfen: 'danger',
  nur_schwellwert: 'accent',
}

export function recommendationTone(recommendation: string | null | undefined): BadgeTone {
  return (recommendation && RECOMMENDATION_TONES[recommendation]) || 'neutral'
}

export function screeningTone(outcome: Proposal['screening']['outcome']): BadgeTone {
  if (outcome === 'pflicht') return 'warning'
  return outcome === 'keine_pflicht' ? 'success' : 'neutral'
}

export function decisionTitle(profile: DataProtectionProfile, key: string | null | undefined): string {
  if (!key) return ''
  return profile.decisions.find((decision) => decision.key === key)?.title ?? key
}

/** Abweichung vom Vorschlag verlangt eine Begründung (Bibliothek prüft Mindestlänge). */
export function isDeviation(proposal: Proposal, decision: string): boolean {
  return !!decision && proposal.recommendation !== 'unvollstaendig' && decision !== proposal.recommendation
}

/** Auflagen: eine je Zeile, leere Zeilen entfallen. */
export function parseConditions(text: string): string[] {
  return text.split('\n').map((line) => line.trim()).filter(Boolean)
}

/** Vier-Augen-Prinzip vorab anzeigen; maßgeblich bleibt die Prüfung des Servers. */
export function mayRelease(view: AssessmentView, actor: string): boolean {
  return !view.locked && !(actor && view.editors.includes(actor))
}

/** Eingabefelder der Entscheidung, vorbelegt aus der Fassung bzw. dem Vorschlag. */
export interface DecisionForm {
  decision: string
  justification: string
  conditions: string
}

export function decisionForm(view: AssessmentView, proposal: Proposal): DecisionForm {
  return {
    decision: view.decision ?? (proposal.recommendation === 'unvollstaendig' ? '' : proposal.recommendation),
    justification: view.deviation_justification ?? '',
    conditions: view.conditions.join('\n'),
  }
}

/** Freigabe möglich: Vier-Augen-Vorprüfung, keine ungespeicherten Eingaben, keine Sperrgründe. */
export function canReleaseAssessment(view: AssessmentView, actor: string, dirty: boolean): boolean {
  return mayRelease(view, actor) && !dirty && !view.release_blockers.length
}
