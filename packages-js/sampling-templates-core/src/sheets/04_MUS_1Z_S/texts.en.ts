/**
 * Englische Fassung zu Blatt 04_MUS_1Z_S.
 * Vermerk: nicht amtliche Arbeitsübersetzung; maßgeblich ist der deutsche Wortlaut der Vorlage.
 * Fachbegriffe nach der englischen Fassung der Delegierten Verordnung (EU) 2023/67 („DR“).
 */
import type { SheetTexts } from '../../model/texts'
import { HINTS_EN, VALUES_EN } from '../shared/mus'
import { HIGH_VALUE_INTERPRETATION_EN, ROUNDING_INTERPRETATION_EN, UPPER_LIMIT_INTERPRETATION_EN } from '../shared/interpretations'
import { APPROXIMATION_EN_TEXT, komHintsEn } from '../shared/kom'
import { definition } from './definition'

const ERRORS = 'Art. 2(20), (21); Art. 8(1) DR.'

export const en: SheetTexts = {
  title: 'MUS standard approach – one sampling period, stratified',
  shortTitle: 'MUS, 1 period, stratified',
  legalBasis: 'Art. 4(2) and (3); Art. 5(1)(a), (2), (4), (5) and (7); Art. 8; Annex I; Annex II point 1.1 of Delegated Regulation (EU) 2023/67',
  sections: {
    H: { title: 'Audit population', reference: 'Art. 3, Art. 4(2)' },
    I: { title: 'Sampling parameters', reference: 'Annex I' },
    J: { title: 'Sample size', reference: 'Annex II point 1.1; Art. 5(5) and (7)' },
    K: { title: 'Sample selection per stratum (PPS)' },
    L: { title: 'Audit results per stratum' },
    M: { title: 'Extrapolation and precision', reference: 'Annex II point 1.1; Art. 8' },
  },
  fields: {
    C4: { label: 'Programme(s) / CCI', hint: 'Art. 3(1) and (2) DR.' },
    C5: { label: 'Accounting year' },
    C6: { label: 'Sampling unit (e.g. operation, declaration of expenditure, payment claim)' },
    C7: { label: 'Stratification criterion (e.g. programme, Fund, intermediate body, risk)', hint: 'Art. 4(2) DR.' },
    D9: { label: 'Book value per stratum (BV_h)', hint: 'Sum = adjusted population (reconciliation with sheet 02 below).' },
    D10: { label: 'Number of sampling units per stratum (N_h)' },
    C11: { label: 'Difference from the adjusted population in sheet 02' },
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
    D24: { label: 'Anticipated standard deviation of error rates per stratum (σ_rh)', hint: 'Annex I point 4.' },
    D25: { label: 'Auxiliary row BV_h · σ²_rh' },
    C26: { label: 'Weighted standard deviation √(Σ BV_h/BV · σ²_rh) (σ_rw)', hint: 'Annex II point 1.1, stratified.' },
    C27: { label: 'Calculated sample size', interpretation: ROUNDING_INTERPRETATION_EN },
    C28: { label: 'Category of the programme under Table 2 of Annex XI to Regulation (EU) 2021/1060 (1–4)', hint: 'Art. 5(7), first subparagraph DR; recital 10.' },
    C29: { label: 'Enhanced proportionate arrangements pursuant to Art. 83 of Regulation (EU) 2021/1060 (Yes/No)', hint: 'Annex I point (a) DR: sample of 30 sampling units.' },
    C30: { label: 'Apply the capped sample size (Yes/No)', hint: 'Art. 5(7): applied to a sample for the whole population (second subparagraph).' },
    C31: { label: 'Admissibility of the capped sample size' },
    C32: { label: 'Capped sample size (units) (n_lim)', hint: 'All units in random strata and only high value units in exhaustive strata count for the capped sample size (Art. 5(7), third subparagraph).' },
    C33: { label: 'Sample size to be applied (at least 30; capped where applicable)', hint: 'Art. 5(5) and (7).' },
    D35: { label: 'Sample size per stratum (rounded up)', hint: 'Rounding up per stratum may raise the sum above n; adjust manually where a capped sample size applies.' },
    D36: { label: 'Cut-off value per stratum (BV_h/n_h)' },
    D37: { label: 'Number of high value units per stratum (n_eh)' },
    D38: { label: 'Book value of the high value units per stratum (BV_eh)' },
    D39: { label: 'Book value of the random stratum per stratum (BV_hs)' },
    D40: { label: 'Units to be selected in the random stratum (n_hs)', interpretation: HIGH_VALUE_INTERPRETATION_EN },
    D41: { label: 'At least three units in each random stratum', hint: 'Art. 5(5) DR.' },
    D42: { label: 'Interval of selection per stratum (BV_hs / n_hs) (SI_h)' },
    D43: { label: 'Units with BV > interval of selection (iteration)', hint: 'Reassign and recalculate where necessary.' },
    D45: { label: 'Sum of the errors in high value units (ΣE_eh)' },
    D46: { label: 'Sum of the error rates of the random stratum (Σ E/BV)' },
    D47: { label: 'Standard deviation of the error rates of the random stratum (s_rh)' },
    D49: { label: 'Error of the exhaustive stratum (EE_eh)' },
    D50: { label: 'Extrapolated error of the random stratum (BV_hs/n_hs · Σ E/BV) (EE_sh)' },
    D51: { label: 'Extrapolated error per stratum (EE_h)' },
    D52: { label: 'Auxiliary row BV²_hs / n_hs · s²_rh' },
    C53: { label: 'Extrapolated error' },
    C54: { label: 'Sampling precision' },
    C55: { label: 'Delimited systemic errors (amount)', hint: ERRORS },
    C56: { label: 'Uncorrected anomalous errors (amount)', hint: ERRORS },
    C57: { label: 'Upper error limit (EE + SE + delimited systemic + uncorrected anomalous errors)', hint: 'Art. 2(20) DR.' },
    C58: { label: 'Lower error limit (EE − SE + delimited systemic + uncorrected anomalous errors)', hint: 'Art. 2(21) in conjunction with points (17) and (24) DR: bilateral testing only.' },
    C59: { label: 'Relative precision (SE / BV)' },
    C60: { label: 'Extrapolated random error rate (EE / BV)' },
    C61: { label: 'Total error rate ((EE + delimited systemic + uncorrected anomalous errors) / BV)', hint: 'Art. 8(1) DR; final calculation including the flat rate for technical assistance and Annex III in sheet 18.' },
    C62: { label: 'Upper error limit in % of BV' },
    C63: { label: 'Assessment against the materiality threshold', interpretation: UPPER_LIMIT_INTERPRETATION_EN },
  },
  summary: {
    primary: 'Sample size to be applied',
    unit: 'units',
    rows: { C35: 'Sum of the sample sizes per stratum n_h', C37: 'of which high value', C40: 'Random strata n_hs', C53: 'Extrapolated error', C54: 'Sampling precision SE', C61: 'Total error rate', C62: 'Upper error limit' },
  },
  values: { ...VALUES_EN, 'MUS-Standardansatz, 1 Zeitraum, geschichtet': 'MUS standard approach, 1 period, stratified' },
  webHints: {
    ...komHintsEn(definition),
    ...APPROXIMATION_EN_TEXT,
    'strata-sum-exceeds-size': HINTS_EN['strata-sum-exceeds-size'],
    'size-exceeds-population': HINTS_EN['size-exceeds-population'],
    'confidence-outside-annex': HINTS_EN['confidence-outside-annex'],
    'strata-beyond-template': HINTS_EN['strata-beyond-template'],
  },
}
