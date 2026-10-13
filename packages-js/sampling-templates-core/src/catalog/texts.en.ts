/**
 * Englische Fassung des Katalogs: Familien nach Kennung, Varianten nach Blatt.
 * Vermerk: nicht amtliche Arbeitsübersetzung; maßgeblich ist der deutsche Wortlaut der Vorlage.
 * Fachbegriffe nach der englischen Fassung der Delegierten Verordnung (EU) 2023/67.
 */
export interface CatalogTexts {
  families: Readonly<Record<string, { name?: string; reference?: string; notice?: string }>>
  variants: Readonly<Record<string, { name?: string; reference?: string; template2017?: string }>>
  /** Hinweis zu Kombinationen ohne Blatt: deutscher Wortlaut → Übersetzung. */
  notes: Readonly<Record<string, string>>
}

const ONLY_79 = 'only Art. 79 of Regulation (EU) 2021/1060 (recital 15)'

export const en: CatalogTexts = {
  families: {
    mus: { name: 'MUS standard approach', reference: 'Art. 5(1)(a) DR' },
    srs: { name: 'Simple random sampling', reference: 'Art. 5(1)(b) DR' },
    'ns-equal': { name: 'Non-statistical, equal probability', reference: 'Art. 6(1)(b) DR' },
    'ns-pps': { name: 'Non-statistical, PPS', reference: 'Art. 6(1)(a) DR' },
    other: {
      name: 'Other methods under Art. 79',
      reference: ONLY_79,
      notice: 'Not an off-the-shelf sampling methodology of Delegated Regulation (EU) 2023/67. The 2017 templates may only be applied with a methodological justification (recital 15).',
    },
  },
  variants: {
    '03_MUS_1Z': { name: 'MUS standard approach, one period', reference: 'Art. 5(1)(a), (2); Annex II point 1.1' },
    '04_MUS_1Z_S': { name: 'MUS standard approach, one period, stratified', reference: 'Art. 4(2); Annex II point 1.1' },
    '05_MUS_2Z': { name: 'MUS standard approach, two periods (standard and global recalculation)', reference: 'Art. 5(6); Annex II point 1.2' },
    '06_MUS_2Z_S': { name: 'MUS standard approach, two periods, stratified', reference: 'Art. 5(6); Annex II point 1.2' },
    '07_MUS_3Z': { name: 'MUS standard approach, three periods', reference: 'Art. 5(6); Annex II point 1.3', template2017: 'new' },
    '08_SRS_1Z': { name: 'Simple random sampling, ratio estimation, one period', reference: 'Art. 5(1)(b), (3); Annex II point 2.1' },
    '09_SRS_1Z_S': { name: 'Simple random sampling, stratified', reference: 'Art. 4(2); Annex II point 2.1' },
    '10_SRS_2Z': { name: 'Simple random sampling, two periods', reference: 'Art. 5(6); Annex II point 2.2' },
    '11_SRS_2Z_S': { name: 'Simple random sampling, two periods, stratified', reference: 'Art. 5(6); Annex II point 2.2' },
    '12_SRS_3Z': { name: 'Simple random sampling, three periods', reference: 'Art. 5(6); Annex II point 2.3', template2017: 'new' },
    '13_NS_GW': { name: 'Non-statistical, equal probability (ratio estimation)', reference: 'Art. 6(1)(b); Art. 8(2)' },
    '14_NS_GW_S': { name: 'Non-statistical, equal probability, stratified', reference: 'Art. 6(1), second subparagraph; Art. 8(2)' },
    '15_NS_PPS': { name: 'Non-statistical, PPS', reference: 'Art. 6(1)(a); Art. 8(2)' },
    '16_NS_PPS_S': { name: 'Non-statistical, PPS, stratified', reference: 'Art. 6(1)(a); Art. 8(2)' },
    X1_KonsMUS_2017: { name: 'Conservative MUS approach', reference: ONLY_79, template2017: 'Template 1, unchanged' },
    X1a_RF_2017: { name: 'Reliability factors', reference: ONLY_79, template2017: 'Template 1.1, unchanged' },
    X2_DiffSch_2017: { name: 'Difference estimation', reference: ONLY_79, template2017: 'Template 10, unchanged' },
    X3_DiffSch_S_2017: { name: 'Difference estimation, stratified', reference: ONLY_79, template2017: 'Template 11, unchanged' },
    X4_DiffSch_2Z_2017: { name: 'Difference estimation, two periods', reference: ONLY_79, template2017: 'Template 12, unchanged' },
  },
  notes: {
    'Für geschichtete Verfahren mit drei Zeiträumen enthält Anhang II Nr. 1.3 und 2.3 Formeln; die Vorlage bildet sie nicht gesondert ab. Die nicht geschichteten Blätter 07 und 12 und die geschichteten Zwei-Zeitraum-Blätter 06 und 11 sind sinngemäß zu erweitern.':
      'For stratified methods with three periods, Annex II points 1.3 and 2.3 contain formulas; the template does not reproduce them separately. The non-stratified sheets 07 and 12 and the stratified two-period sheets 06 and 11 are to be extended accordingly.',
  },
}
