/**
 * Englische Fassung zu Blatt 06_MUS_2Z_S.
 * Vermerk: nicht amtliche Arbeitsübersetzung; maßgeblich ist der deutsche Wortlaut der Vorlage.
 * Fachbegriffe nach der englischen Fassung der Delegierten Verordnung (EU) 2023/67 („DR“).
 */
import { STRATA_COLUMNS } from '../../model/strata'
import type { FieldTexts, SheetTexts } from '../../model/texts'
import { HINTS_EN, INCREASE_INTERPRETATION_EN, VALUES_EN } from '../shared/mus'
import { delvoHintsEn, globalMarginId, withNotApplicableNoteEn } from '../shared/delvo'
import { HIGH_VALUE_INTERPRETATION_EN, ROUNDING_INTERPRETATION_EN, UPPER_LIMIT_INTERPRETATION_EN } from '../shared/interpretations'

const ERRORS = 'Art. 2(20), (21); Art. 8(1) DR.'
const INCREASE_NOTE = `Approach “increase” – ${INCREASE_INTERPRETATION_EN}`

/** Auswahl und Ergebnisse eines Zeitraums je Schicht: zehn Zeilen ab `row` (Grenzwert bis Standardabweichung der Stichprobe). */
function period(row: number, number: number): Record<string, FieldTexts> {
  const cell = (offset: number): string => `D${row + offset}`
  return {
    [cell(0)]: { label: `Cut-off value for period ${number} per stratum (BV/n)` },
    [cell(1)]: { label: 'Number of high value units (n_eh)' },
    [cell(2)]: { label: 'Book value of the high value units (BV_eh)' },
    [cell(3)]: { label: 'Book value of the random stratum (BV_hs)' },
    [cell(4)]: { label: 'Random units to be selected (n_hs)' },
    [cell(5)]: { label: 'At least three units in each random stratum', hint: 'Art. 5(5) DR.' },
    [cell(6)]: { label: 'Interval of selection (SI_h)' },
    [cell(7)]: { label: 'Sum of the errors in high value units (ΣE_eh)' },
    [cell(8)]: { label: 'Sum of the error rates of the random stratum (Σ E/BV)' },
    [cell(9)]: { label: 'Standard deviation of the error rates of the random stratum (s_rh)' },
  }
}

/** Hinweise je Schicht (`<kennung>-<n>`) mit vorangestellter Schichtnummer. */
function perStratum(id: string, text: string): Record<string, string> {
  return Object.fromEntries(STRATA_COLUMNS.map((_, index) => [`${id}-${index + 1}`, `Stratum ${index + 1}: ${text}`]))
}

export const en: SheetTexts = {
  title: 'MUS standard approach – two sampling periods, stratified',
  shortTitle: 'MUS, 2 periods, stratified',
  legalBasis: 'Art. 4; Art. 5(1)(a), (5) to (7); Art. 8; Annex I; Annex II point 1.2 (stratified) of Delegated Regulation (EU) 2023/67',
  sections: {
    H: { title: 'Population and forecast' },
    I: { title: 'Sampling parameters', reference: 'Annex I' },
    J: { title: 'Sample size “First period”' },
    K: { title: 'Selection and results for period 1 (PPS)' },
    L: { title: 'Recalculation for period 2', reference: 'Art. 5(6) and (7)' },
    M: { title: 'Selection and results for period 2 (PPS)' },
    N: { title: 'Extrapolation and precision', reference: 'Annex II point 1.2, stratified; Art. 8' },
  },
  fields: {
    C4: { label: 'Programme(s) / CCI', hint: 'Art. 3(1) and (2) DR.' },
    C5: { label: 'Accounting year' },
    C6: { label: 'Sampling unit (e.g. operation, declaration of expenditure, payment claim)' },
    D8: { label: 'Book value of period 1 (actual) (BV_h1)' },
    D9: { label: 'Forecast book value of period 2 (BV_h2)' },
    D10: { label: 'Forecast number of units in period 2 (N_h2)' },
    C11: { label: 'Forecast book value of the accounting year (BV_1+2)' },
    C12: { label: 'Reliability of the management and control system (high / average / low)', hint: 'Annex I point 2: evaluation taking into account the results of system audits, so that the combined level of assurance is high.' },
    C13: { label: 'Confidence level', hint: 'Annex I point 2: high ≥ 60 %, low ≥ 90 %; selection from sheet 01.' },
    C14: { label: 'Type of testing (bilateral / unilateral)', hint: 'Annex I point 3; Art. 2(17) and (18) DR.' },
    C15: { label: "Coefficient z from a normal distribution (z / z')", hint: 'Annex I point 3, table of z values (95 % is outside the table, see sheet 01).' },
    C16: { label: 'Check of the confidence level against the system assessment', hint: 'Annex I point 2 only sets the minimum levels for high and low reliability; for “average” the confidence level must be justified.' },
    C17: { label: 'Materiality threshold (maximum 2 %)', hint: 'Annex I point 1 in conjunction with point 5.9 of Annex XX to Regulation (EU) 2021/1060.' },
    C18: { label: 'Check of the materiality threshold' },
    C19: { label: 'Tolerable error (TE = materiality threshold × BV)', hint: 'Annex II: TE maximum 2 % of the total expenditure.' },
    C20: { label: 'Anticipated error rate', hint: 'Annex I point 4: pilot sample, historical data or professional judgement.' },
    C21: { label: 'Anticipated error (AE = anticipated error rate × BV)' },
    C22: { label: 'Check TE > AE' },
    D24: { label: 'Anticipated standard deviation of error rates in period 1 (σ_rh1)' },
    D25: { label: 'Anticipated standard deviation of error rates in period 2 (σ_rh2)' },
    D26: { label: 'Auxiliary row BV_h1·σ²_rh1 + BV_h2·σ²_rh2' },
    C27: { label: 'Weighted standard deviation √(σ²_rw1 + σ²_rw2) (σ_rw1+2)' },
    C28: {
      label: 'Approach to the recalculation of the sample size',
      hint: 'Art. 5(6)(a) (standard) or (b) (global); with a capped sample size also Art. 5(7), fourth subparagraph, point (a) (increase).',
      interpretation: INCREASE_NOTE,
    },
    C29: { label: 'Calculated total sample size (n_1+2)', interpretation: ROUNDING_INTERPRETATION_EN },
    C30: { label: 'Category of the programme under Table 2 of Annex XI to Regulation (EU) 2021/1060 (1–4)', hint: 'Art. 5(7), first subparagraph DR; recital 10.' },
    C31: { label: 'Enhanced proportionate arrangements pursuant to Art. 83 of Regulation (EU) 2021/1060 (Yes/No)', hint: 'Annex I point (a) DR: sample of 30 sampling units.' },
    C32: { label: 'Apply the capped sample size (Yes/No)', hint: 'Art. 5(7): applied to a sample for the whole population (second subparagraph).' },
    C33: { label: 'Admissibility of the capped sample size' },
    C34: { label: 'Capped sample size (units) (n_lim)', hint: 'All units in random strata and only high value units in exhaustive strata count for the capped sample size (Art. 5(7), third subparagraph).' },
    C35: { label: 'Total sample size to be applied (at least 30; capped where applicable)' },
    D37: { label: 'Sample size for period 1 per stratum (BV_h1/BV · n) (n_h1)' },
    D38: { label: 'Planned sample size for period 2 per stratum (n_h2)' },
    ...period(40, 1),
    D44: { label: 'Random units to be selected (n_hs)', interpretation: HIGH_VALUE_INTERPRETATION_EN },
    D51: { label: 'Book value of period 2 (actual) (BV_h2)' },
    D52: { label: 'Number of units in period 2 (actual) (N_h2)' },
    D53: { label: 'Updated standard deviation for period 2 (σ_rh2)' },
    C54: { label: 'Updated anticipated error rate (empty = value from section I)' },
    C55: { label: 'Book value of the accounting year (BV)' },
    C56: { label: 'Tolerable error (updated) (TE)' },
    C57: { label: 'Anticipated error (updated) (AE)' },
    D59: { label: 'Standard deviation of period 1 (s, substituted by σ where not available) (s_rh1)' },
    D60: { label: 'Auxiliary row BV²_h1/n_h1 · s²_rh1' },
    D61: { label: 'Auxiliary row BV_h2 · σ²_rh2' },
    C62: { label: 'Denominator (TE − AE)² − z²·Σ BV²_h1/n_h1·s²_rh1' },
    C63: { label: 'Standard: n₂ = z²·BV₂·Σ(BV_h2·σ²_rh2) / denominator (n_2)' },
    D64: { label: 'Auxiliary row global: BV_h1·s²_rh1 + BV_h2·σ²_rh2' },
    C65: { label: 'Global: calculated total sample size' },
    C66: { label: 'Global: total sample size to be applied' },
    D68: { label: 'Global: additional units in period 1 per stratum' },
    D69: { label: 'Sample size to be applied for period 2 per stratum (at least 3) (n_h2)', interpretation: INCREASE_NOTE },
    D70: { label: 'Final sample size for period 1 per stratum (n_h1)' },
    C71: { label: 'Compliance with the capped sample size' },
    C72: { label: 'Minimum sample size of the accounting year' },
    ...period(74, 2),
    D84: { label: 'Final random units of period 1 per stratum (n_h1s)' },
    D86: { label: 'Error of the exhaustive strata (P1 + P2) (EE_eh)' },
    D87: { label: 'Extrapolated error of the random strata (P1 + P2) (EE_sh)' },
    D88: { label: 'Auxiliary row BV²_h1s/n_h1s·s²_rh1 + BV²_h2s/n_h2s·s²_rh2' },
    C89: { label: 'Extrapolated error EE' },
    C90: { label: 'Sampling precision SE = z·√(Σ…)' },
    C91: { label: 'Delimited systemic errors (amount)', hint: ERRORS },
    C92: { label: 'Uncorrected anomalous errors (amount)', hint: ERRORS },
    C93: { label: 'Upper error limit (EE + SE + delimited systemic + uncorrected anomalous errors)', hint: 'Art. 2(20) DR.' },
    C94: { label: 'Lower error limit (EE − SE + delimited systemic + uncorrected anomalous errors)', hint: 'Art. 2(21) in conjunction with points (17) and (24) DR: bilateral testing only.' },
    C95: { label: 'Relative precision (SE / BV)' },
    C96: { label: 'Extrapolated random error rate (EE / BV)' },
    C97: { label: 'Total error rate ((EE + delimited systemic + uncorrected anomalous errors) / BV)', hint: 'Art. 8(1) DR; final calculation including the flat rate for technical assistance and Annex III in sheet 18.' },
    C98: { label: 'Upper error limit in % of BV' },
    C99: { label: 'Assessment against the materiality threshold', interpretation: UPPER_LIMIT_INTERPRETATION_EN },
  },
  summary: {
    primary: 'Total sample size to be applied',
    unit: 'units',
    rows: { C70: 'Sample size for period 1 (sum of n_h1)', C69: 'Sample size for period 2 (sum of n_h2)', C89: 'Extrapolated error', C90: 'Sampling precision SE', C97: 'Total error rate', C98: 'Upper error limit' },
  },
  values: { ...VALUES_EN, 'MUS-Standardansatz, 2 Zeiträume, geschichtet': 'MUS standard approach, 2 periods, stratified' },
  webHints: withNotApplicableNoteEn({
    ...delvoHintsEn(globalMarginId()),
    'limited-size-open': HINTS_EN['limited-size-open'],
    'strata-sum-exceeds-size': HINTS_EN['strata-sum-exceeds-size'],
    ...perStratum('size-exceeds-population-2', 'sample size for period 2 exceeds the number of units of the stratum'),
    ...perStratum(
      'no-planned-size',
      'without a forecast for period 2 there is no planned sample size on which this approach builds. Where all required inputs are present, the web version shows, like the template, the minimum size of 3 as the sample size of the stratum for period 2 and continues to calculate with it; the result is not reliable',
    ),
    'negative-denominator':
      'Denominator of the standard recalculation is not positive: the standard approach yields no sample size per stratum for period 2. Where all required inputs are present, the web version shows, like the template, a sample size of 0 for period 2 and the check “✔ ≥ 3” without any units and continues to calculate with them; the result is not reliable. Recommended: global recalculation',
    'second-period-empty':
      'No actual book value has been entered for period 2: the template continues to calculate with period 1 alone. Where all required inputs are present, the web version shows the same values; recalculation, extrapolation and total error rate are then not reliable. Where a required input is missing, they remain open',
    'confidence-outside-annex': HINTS_EN['confidence-outside-annex'],
    'strata-beyond-template': HINTS_EN['strata-beyond-template'],
  }),
}
