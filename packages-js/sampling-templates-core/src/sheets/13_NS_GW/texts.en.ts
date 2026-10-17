/**
 * Englische Fassung zu Blatt 13_NS_GW.
 * Vermerk: nicht amtliche Arbeitsübersetzung; maßgeblich ist der deutsche Wortlaut der Vorlage.
 * Fachbegriffe nach der englischen Fassung der Delegierten Verordnung (EU) 2023/67 (Art. 2, 5–8,
 * Anhang II): extrapolated error, exhaustive/random stratum, high value units,
 * interval of selection, sampling precision, audit population.
 */
import type { SheetTexts } from '../../model/texts'
import { HINTS_EN, VALUES_EN } from '../shared/nonstatistical'

export const en: SheetTexts = {
  title: 'Non-statistical sampling – selection with equal probability, non-stratified',
  shortTitle: 'Non-statistical, equal probability',
  legalBasis: 'Art. 6(1)(b), (2) and (3); Art. 8(2); Annex II point 2.1 (ratio estimation) of Delegated Regulation (EU) 2023/67',
  sections: {
    H: { title: 'Audit population', reference: 'Art. 3' },
    I: { title: 'Sample' },
    J: { title: 'Audit results' },
    K: { title: 'Extrapolation', reference: 'ratio estimation; Art. 8(2)' },
  },
  fields: {
    C4: { label: 'Programme(s) / CCI', hint: 'Art. 3(1) and (2) DR.' },
    C5: { label: 'Accounting year' },
    C6: { label: 'Sampling unit (e.g. operation, declaration of expenditure, payment claim)' },
    C7: { label: 'Book value of the adjusted population (BV)', hint: 'Pre-filled from sheet 02.' },
    C8: { label: 'Number of sampling units (N)', hint: 'Pre-filled from sheet 02.' },
    C9: { label: 'Admissibility of non-statistical sampling (N < 300)' },
    C10: { label: 'Book value of the exhaustive stratum (optional) (BV_e)', hint: 'Art. 6(1), third subparagraph; Art. 5(3).' },
    C11: { label: 'Number of units of the exhaustive stratum (N_e)' },
    C12: { label: 'Book value of the random stratum (BV_s)' },
    C13: { label: 'Size of the random sample (professional judgement)', hint: 'Art. 79(2) of Regulation (EU) 2021/1060: sufficient for a valid audit opinion.' },
    C14: { label: 'Total sample (random sample + exhaustive stratum)' },
    C15: { label: 'Minimum coverage 10 % of the sampling units (rounded up)', hint: 'Art. 79(2) of Regulation (EU) 2021/1060; Art. 6(2) DR: units of exhaustive strata are included. Where the method is changed under Art. 6(3), the minimum size refers to the whole accounting year.' },
    C16: { label: 'Check of minimum coverage' },
    C17: { label: 'Sum of book values of the sample of the random stratum (Σ BV_i)' },
    C18: { label: 'Sum of errors of the sample of the random stratum (Σ E_i)' },
    C19: { label: 'Sum of errors in the exhaustive stratum (ΣE_e)' },
    C20: { label: 'Error of the exhaustive stratum (EE_e)' },
    C21: { label: 'Extrapolated error of the random stratum (EE_s)' },
    C22: { label: 'Extrapolated error EE' },
    C23: { label: 'Delimited systemic errors (amount)', hint: 'Art. 2(20), (21); Art. 8(1) DR.' },
    C24: { label: 'Uncorrected anomalous errors (amount)', hint: 'Art. 2(20), (21); Art. 8(1) DR.' },
    C25: { label: 'Extrapolated random error rate', formula: 'EE / BV' },
    C26: { label: 'Total error rate', formula: '(EE + delimited systemic + uncorrected anomalous errors) / BV', hint: 'Art. 8(1) DR; final calculation including the flat rate for technical assistance and Annex III in sheet 18.' },
    C27: { label: 'Materiality threshold', hint: 'Annex I point 1 DR.' },
    C28: { label: 'Assessment against the materiality threshold', hint: 'For non-statistical sampling, sampling precision and upper error limit are not calculated (Art. 8(2)).' },
  },
  summary: {
    primary: 'Total error rate (sheet-related)',
    unit: '',
    rows: { C14: 'Total sample', C15: 'Minimum coverage (10 %)', C12: 'Book value of the random stratum', C21: 'Extrapolated error of the random stratum', C22: 'Extrapolated error EE', C25: 'Extrapolated random error rate' },
  },
  values: { ...VALUES_EN, 'Nichtstatistisch, gleiche Wahrscheinlichkeit': 'Non-statistical, equal probability' },
  webHints: {
    'size-exceeds-population': HINTS_EN['size-exceeds-population'],
  },
}
