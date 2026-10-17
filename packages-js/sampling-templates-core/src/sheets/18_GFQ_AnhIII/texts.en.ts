/**
 * Englische Fassung zu Blatt 18_GFQ_AnhIII.
 * Vermerk: nicht amtliche Arbeitsübersetzung; maßgeblich ist der deutsche Wortlaut der Vorlage.
 * Fachbegriffe nach der englischen Fassung der Delegierten Verordnung (EU) 2023/67
 * (Art. 3, Art. 8, Anhang III): audit population, extrapolated error, sampling
 * precision, exclusion/replacement of sampling units, reduced/original population.
 *
 * Die Hinweise der Webfassung sind nach Kennung übersetzt. Zwei deutsche Hinweise
 * nennen das Blatt bzw. die fehlenden Größen im Satz; die englische Fassung
 * nennt sie allgemein, weil `SheetTexts` je Kennung nur einen festen Text trägt.
 */
import type { SheetTexts } from '../../model/texts'
import { UPPER_LIMIT_INTERPRETATION_EN } from '../shared/interpretations'

export const en: SheetTexts = {
  title: 'Total error rate, technical assistance and single audit arrangements',
  shortTitle: 'Total error rate',
  legalBasis: 'Art. 3(5) and (6); Art. 8(1), (4) and (5); Annex III of Delegated Regulation (EU) 2023/67; Art. 36(5), Art. 80(3) of Regulation (EU) 2021/1060',
  sections: {
    A: { title: 'Values taken over from the method sheet' },
    B: { title: 'Populations', reference: 'from sheet 02' },
    C: { title: 'Adjustment of the high value stratum', reference: 'Annex III, optional' },
    D: { title: 'Adjusted extrapolated error and adjusted precision', reference: 'Annex III' },
    E: { title: 'Total error rate', reference: 'Art. 8(1) and (5)' },
  },
  fields: {
    C4: { label: 'Method sheet applied', hint: 'Selection list; the values are taken over from the results summary (columns M:N).' },
    C5: { label: 'Book value of the extrapolation basis in the method sheet (BV)' },
    C6: { label: 'Extrapolated error (including the exhaustive stratum) (EE)' },
    C7: { label: 'of which error of the exhaustive stratum (EE_e)' },
    C8: { label: 'Sampling precision (SE)' },
    C9: { label: 'Delimited systemic errors' },
    C10: { label: 'Uncorrected anomalous errors' },
    C11: { label: 'Method family for Annex III' },
    C12: { label: 'Audit population for the total error rate (Art. 3(5))' },
    C13: { label: 'Flat-rate financing for technical assistance (Art. 36(5) of Regulation (EU) 2021/1060)' },
    C14: { label: 'Extrapolation basis excluding technical assistance (Art. 8(5)) (BV_u)' },
    C15: { label: 'Treatment of the units that cannot be audited under Art. 80(3)' },
    C16: { label: 'Book value of the units that cannot be audited under Art. 80(3)' },
    C17: { label: 'Reduced population (BV_r)' },
    C18: { label: 'Adjustment factor BV_original / BV_reduced', hint: 'Annex III, Tables 1 and 2.' },
    C19: { label: 'Reconciliation of the extrapolation basis of the method sheet' },
    C20: { label: 'Apply the extrapolation to high value units not audited (Yes/No)' },
    C21: { label: 'Book value of the original high value stratum (BV_e,u)' },
    C22: { label: 'Book value of the audited units of the high value stratum (BV_e,r)' },
    C23: { label: 'EE_e', formula: 'EE_e,reduced · BV_e,original / BV_e,reduced' },
    C24: {
      label: 'Adjusted extrapolated error (EE)',
      hint: 'Exclusion: EE × factor; replacement: extrapolation to the original population. Where section C is applied, only the random part is scaled (interpretation).',
      interpretation: 'Where section C is applied, only the random part of the extrapolated error is scaled by the adjustment factor.',
    },
    C25: { label: 'Adjusted precision (SE)', hint: 'Table 2, replacement: calculate the precision for the reduced population and adjust it by the factor.' },
    C26: {
      label: 'Total error rate',
      formula: '(EE + delimited systemic + uncorrected anomalous errors) / BV excluding TA',
      hint: 'Art. 8(1); under Art. 8(5) the rate is also the total error rate for the population including TA.',
    },
    C27: { label: 'Amount of error in relation to the audit population including TA' },
    C28: { label: 'Upper error limit in % (including sampling precision)', hint: 'Art. 2(20).' },
    C29: { label: 'Materiality threshold' },
    C30: { label: 'Assessment', interpretation: UPPER_LIMIT_INTERPRETATION_EN },
  },
  summary: {
    primary: 'Total error rate',
    unit: '',
    rows: {
      C28: 'Upper error limit (including sampling precision)',
      C24: 'Adjusted extrapolated error (EE)',
      C25: 'Adjusted precision (SE)',
      C27: 'Amount of error including TA',
      C14: 'Extrapolation basis excluding technical assistance (BV_u)',
    },
  },
  values: {
    'Tabelle 1 (MUS/PPS)': 'Table 1 (MUS/PPS)',
    'Tabelle 2 (SRS/gleiche Wahrscheinlichkeit)': 'Table 2 (SRS/equal probability selection)',
    '✔ Basis stimmt mit der erwarteten Grundgesamtheit überein': '✔ basis agrees with the expected population',
    '⚠ Basis weicht ab – Ausschluss: reduzierte, Ersetzung/keine: ursprüngliche Grundgesamtheit': '⚠ basis differs – exclusion: reduced population; replacement/none: original population',
    '✖ Gesamtfehlerquote über der Signifikanzschwelle': '✖ total error rate above the materiality threshold',
    '⚠ GFQ unter, obere Fehlergrenze über der Schwelle': '⚠ total error rate below, upper error limit above the threshold',
    '✔ unter der Signifikanzschwelle': '✔ below the materiality threshold',
    'n. a.': 'n/a',
    'n. a. (Art. 8 Abs. 2)': 'n/a (Art. 8(2))',
  },
  webHints: {
    'no-method': 'No method chosen: nothing is taken over from a method sheet; rows 4 to 11 remain empty',
    'method-without-summary':
      'The chosen sheet has no results summary and is not in the selection list of the template (2017 legacy template or auxiliary sheet): nothing is taken over; rows 4 to 11 remain empty',
    'method-incomplete':
      'The method sheet does not yet supply every value to be taken over (book value of the extrapolation basis BV, extrapolated error EE, sampling precision SE). Inputs are missing there',
    'population-missing': 'Sheet 02 does not supply an audit population (inputs are missing there); extrapolation basis, adjustment factor and total error rate remain open',
    'treatment-missing':
      'No treatment of the units that cannot be audited under Art. 80(3) has been chosen in sheet 02; as in the template, the calculation is made without exclusion and without replacement',
    'reduced-population-not-positive': 'The reduced population (BV_r) is not positive; the adjustment factor is then not meaningful',
    'replacement-precision-not-scaled':
      'Replacement with a method of Table 2: under Annex III, Table 2, to Delegated Regulation (EU) 2023/67 the precision is to be calculated for the reduced population and then adjusted by the ratio BV original / BV reduced, even where no affected unit has been drawn. The template takes over the precision of the method sheet, calculated there for the original population, without adjustment (its comparison with “Tabelle 2” never matches). Effect: precision and upper error limit do not follow the calculation path of the Delegated Regulation. The web version calculates like the template – assess the adjusted precision and the upper error limit with professional judgement',
    'stratified-single-factor':
      'Stratified method with exclusion or replacement under Art. 80(3): Annex III to Delegated Regulation (EU) 2023/67 describes the adjustment by the ratio “BV(h) original” / “BV(h) reduced”, i.e. per stratum. The template uses a single adjustment factor for the whole population; where the affected units are unevenly distributed over the strata, the result departs from the calculation path of the Delegated Regulation. The web version calculates like the template',
    'high-value-incomplete': 'Adjustment of the high value stratum chosen, but the book value of the original (BV_e,u) or of the audited high value stratum (BV_e,r) is missing',
  },
}
