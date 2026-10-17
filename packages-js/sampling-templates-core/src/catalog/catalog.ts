/**
 * Katalog der Verfahrensfamilien und ihrer Varianten nach Blatt 00 der
 * Vorlage (Blatt, Inhalt, Rechtsgrundlage, Bezug zur Vorlage von 2017).
 * Welche Varianten rechenbar sind, ergibt sich aus dem Blattregister.
 */
import type { TranslationLocale } from '../model/texts'
import type { SheetId } from '../model/types'
import { en, type CatalogTexts } from './texts.en'

/** Eine Variante = ein Blatt der Vorlage. */
export interface Variant {
  sheet: SheetId
  /** Blattnummer (`03`, `X1a`). */
  number: string
  name: string
  /** Fundstelle in der DelVO bzw. in Anhang II. */
  reference: string
  /** Entsprechung in der Vorlage von 2017. */
  template2017: string
  /** Anzahl der Stichprobenzeiträume (nur in Matrixfamilien). */
  periods?: 1 | 2 | 3
  stratified?: boolean
}

/** Kombination der Matrix, für die die Vorlage kein Blatt enthält. */
export interface MatrixGap {
  periods: 1 | 2 | 3
  stratified: boolean
  note: string
}

export interface Family {
  id: string
  name: string
  reference: string
  /** `matrix`: Zeiträume × Schichtung; `list`: einfache Liste. */
  layout: 'matrix' | 'list'
  variants: readonly Variant[]
  gaps?: readonly MatrixGap[]
  /** Deutlicher Hinweis zur Familie (Altvorlagen). */
  notice?: string
}

/** Hinweis aus Blatt 00 zu geschichteten Verfahren mit drei Zeiträumen. */
const THREE_PERIODS_STRATIFIED =
  'Für geschichtete Verfahren mit drei Zeiträumen enthält Anhang II Nr. 1.3 und 2.3 Formeln; die Vorlage bildet sie nicht gesondert ab. Die nicht geschichteten Blätter 07 und 12 und die geschichteten Zwei-Zeitraum-Blätter 06 und 11 sind sinngemäß zu erweitern.'

const GAP: readonly MatrixGap[] = [{ periods: 3, stratified: true, note: THREE_PERIODS_STRATIFIED }]

export const FAMILIES: readonly Family[] = [
  {
    id: 'mus',
    name: 'MUS-Standardansatz',
    reference: 'Art. 5 Abs. 1 Buchst. a DelVO',
    layout: 'matrix',
    gaps: GAP,
    variants: [
      { sheet: '03_MUS_1Z', number: '03', name: 'MUS-Standardansatz, ein Zeitraum', reference: 'Art. 5 Abs. 1 Buchst. a, Abs. 2; Anh. II Nr. 1.1', template2017: 'Template 2', periods: 1, stratified: false },
      { sheet: '04_MUS_1Z_S', number: '04', name: 'MUS-Standardansatz, ein Zeitraum, geschichtet', reference: 'Art. 4 Abs. 2; Anh. II Nr. 1.1', template2017: 'Template 3', periods: 1, stratified: true },
      { sheet: '05_MUS_2Z', number: '05', name: 'MUS-Standardansatz, zwei Zeiträume (Standard- und globale Neuberechnung)', reference: 'Art. 5 Abs. 6; Anh. II Nr. 1.2', template2017: 'Template 4', periods: 2, stratified: false },
      { sheet: '06_MUS_2Z_S', number: '06', name: 'MUS-Standardansatz, zwei Zeiträume, geschichtet', reference: 'Art. 5 Abs. 6; Anh. II Nr. 1.2', template2017: 'Template 5', periods: 2, stratified: true },
      { sheet: '07_MUS_3Z', number: '07', name: 'MUS-Standardansatz, drei Zeiträume', reference: 'Art. 5 Abs. 6; Anh. II Nr. 1.3', template2017: 'neu', periods: 3, stratified: false },
    ],
  },
  {
    id: 'srs',
    name: 'Einfache Zufallsstichprobe',
    reference: 'Art. 5 Abs. 1 Buchst. b DelVO',
    layout: 'matrix',
    gaps: GAP,
    variants: [
      { sheet: '08_SRS_1Z', number: '08', name: 'Einfaches Zufallsstichprobenverfahren, Verhältnisschätzung, ein Zeitraum', reference: 'Art. 5 Abs. 1 Buchst. b, Abs. 3; Anh. II Nr. 2.1', template2017: 'Template 6', periods: 1, stratified: false },
      { sheet: '09_SRS_1Z_S', number: '09', name: 'Einfaches Zufallsstichprobenverfahren, geschichtet', reference: 'Art. 4 Abs. 2; Anh. II Nr. 2.1', template2017: 'Template 7', periods: 1, stratified: true },
      { sheet: '10_SRS_2Z', number: '10', name: 'Einfaches Zufallsstichprobenverfahren, zwei Zeiträume', reference: 'Art. 5 Abs. 6; Anh. II Nr. 2.2', template2017: 'Template 8', periods: 2, stratified: false },
      { sheet: '11_SRS_2Z_S', number: '11', name: 'Einfaches Zufallsstichprobenverfahren, zwei Zeiträume, geschichtet', reference: 'Art. 5 Abs. 6; Anh. II Nr. 2.2', template2017: 'Template 9', periods: 2, stratified: true },
      { sheet: '12_SRS_3Z', number: '12', name: 'Einfaches Zufallsstichprobenverfahren, drei Zeiträume', reference: 'Art. 5 Abs. 6; Anh. II Nr. 2.3', template2017: 'neu', periods: 3, stratified: false },
    ],
  },
  {
    id: 'ns-equal',
    name: 'Nichtstatistisch, gleiche Wahrscheinlichkeit',
    reference: 'Art. 6 Abs. 1 Buchst. b DelVO',
    layout: 'list',
    variants: [
      { sheet: '13_NS_GW', number: '13', name: 'Nichtstatistisch, gleiche Wahrscheinlichkeit (Verhältnisschätzung)', reference: 'Art. 6 Abs. 1 Buchst. b; Art. 8 Abs. 2', template2017: 'Template 13', stratified: false },
      { sheet: '14_NS_GW_S', number: '14', name: 'Nichtstatistisch, gleiche Wahrscheinlichkeit, geschichtet', reference: 'Art. 6 Abs. 1 UAbs. 2; Art. 8 Abs. 2', template2017: 'Template 14', stratified: true },
    ],
  },
  {
    id: 'ns-pps',
    name: 'Nichtstatistisch, PPS',
    reference: 'Art. 6 Abs. 1 Buchst. a DelVO',
    layout: 'list',
    variants: [
      { sheet: '15_NS_PPS', number: '15', name: 'Nichtstatistisch, PPS', reference: 'Art. 6 Abs. 1 Buchst. a; Art. 8 Abs. 2', template2017: 'Template 15', stratified: false },
      { sheet: '16_NS_PPS_S', number: '16', name: 'Nichtstatistisch, PPS, geschichtet', reference: 'Art. 6 Abs. 1 Buchst. a; Art. 8 Abs. 2', template2017: 'Template 16', stratified: true },
    ],
  },
  {
    id: 'other',
    name: 'Weitere Methoden nach Art. 79',
    reference: 'nur Art. 79 VO (EU) 2021/1060 (ErwG 15)',
    layout: 'list',
    notice: 'Keine gebrauchsfertige Methode der DelVO (EU) 2023/67. Die Altvorlagen von 2017 sind nur mit methodischer Begründung anzuwenden (ErwG 15).',
    variants: [
      { sheet: 'X1_KonsMUS_2017', number: 'X1', name: 'Konservativer MUS-Ansatz', reference: 'nur Art. 79 VO (EU) 2021/1060 (ErwG 15)', template2017: 'Template 1, unverändert' },
      { sheet: 'X1a_RF_2017', number: 'X1a', name: 'Zuverlässigkeitsfaktoren', reference: 'nur Art. 79 VO (EU) 2021/1060 (ErwG 15)', template2017: 'Template 1.1, unverändert' },
      { sheet: 'X2_DiffSch_2017', number: 'X2', name: 'Differenzschätzung', reference: 'nur Art. 79 VO (EU) 2021/1060 (ErwG 15)', template2017: 'Template 10, unverändert' },
      { sheet: 'X3_DiffSch_S_2017', number: 'X3', name: 'Differenzschätzung, geschichtet', reference: 'nur Art. 79 VO (EU) 2021/1060 (ErwG 15)', template2017: 'Template 11, unverändert' },
      { sheet: 'X4_DiffSch_2Z_2017', number: 'X4', name: 'Differenzschätzung, zwei Zeiträume', reference: 'nur Art. 79 VO (EU) 2021/1060 (ErwG 15)', template2017: 'Template 12, unverändert' },
    ],
  },
]

/** Schritt des Arbeitsablaufs der Vorlage. */
export interface WorkflowStep {
  id: 'population' | 'method' | 'subsamples' | 'totalErrorRate' | 'report'
  /** Blatt des Schritts; der Schritt „Verfahren“ zeigt das gewählte Methodenblatt. */
  sheet?: SheetId
}

/** Arbeitsablauf: Grundgesamtheit → Verfahren → Unterstichproben → Gesamtfehlerquote → Bericht. */
export const WORKFLOW_STEPS: readonly WorkflowStep[] = [
  { id: 'population', sheet: '02_Grundgesamtheit' },
  { id: 'method' },
  { id: 'subsamples', sheet: '17_Unterstichprobe' },
  { id: 'totalErrorRate', sheet: '18_GFQ_AnhIII' },
  { id: 'report', sheet: '20_Druck_KOM' },
]

/** Variante zu einem Blatt. */
export function findVariant(sheet: SheetId, families: readonly Family[] = FAMILIES): Variant | undefined {
  return families.flatMap((family) => [...family.variants]).find((variant) => variant.sheet === sheet)
}

/** Familie, zu der ein Blatt gehört. */
export function familyOf(sheet: SheetId, families: readonly Family[] = FAMILIES): Family | undefined {
  return families.find((family) => family.variants.some((variant) => variant.sheet === sheet))
}

/** Arbeitsübersetzungen des Katalogs je Sprache. */
export const CATALOG_TEXTS: Readonly<Record<TranslationLocale, CatalogTexts>> = { en }

/** Katalog in der Sprache der Oberfläche; Deutsch und fehlende Texte bleiben unverändert. */
export function localizeFamilies(families: readonly Family[], locale: 'de' | TranslationLocale): readonly Family[] {
  if (locale === 'de') return families
  const texts = CATALOG_TEXTS[locale]
  return families.map((family) => ({
    ...family,
    ...texts.families[family.id],
    variants: family.variants.map((variant) => ({ ...variant, ...texts.variants[variant.sheet] })),
    gaps: family.gaps?.map((gap) => ({ ...gap, note: texts.notes[gap.note] ?? gap.note })),
  }))
}
