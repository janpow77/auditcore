/**
 * Hinweise zur Planung bei voraussichtlichem Fehler über oder auf der
 * Signifikanzschwelle, nach den Vorgaben der KOM (Entscheidung des Inhabers vom
 * 17.10.2026: „Es gelten die Vorgaben der KOM“, `docs/abweichungen.md` Nr. 16).
 *
 * - Anhang II DelVO (EU) 2023/67 enthält keine Bedingung TE > AE. Der
 *   KOM-Leitfaden EGESIF_16-0014-01 (Abschnitt 7.1, S. 183, Fußnote 59) plant
 *   auch bei AE > TE, mit der geplanten Genauigkeit |TE − AE|; ab AE ≥ 4 %
 *   empfiehlt er, mit 4 % zu rechnen. Die Webfassung rechnet mit dem
 *   eingegebenen Wert und weist nur darauf hin.
 * - Bei AE = TE teilt die Formel durch null; der Umfang ist nicht bestimmbar.
 *
 * Die Zellen findet das Modul über die Aliasse der Blattdefinitionen 03–12.
 */
import { ge, gt, isBlank, isNumber, left, sameText } from '../../excel/index'
import { fieldsOf, type MethodDefinition } from '../../model/definition'
import type { CellMap, CellValue, SheetContext, WebHint } from '../../model/types'
import { SIZE_NOT_APPLICABLE } from './periods'

/** Ein Berechnungsschritt mit TE, AE, Umfang und Fehlerquote (Aliasse) und dem Zusatz der Hinweiskennung. */
interface Step {
  suffix: string
  global: boolean
  tolerable: string
  anticipated: string
  size: string
  rates: readonly string[]
}

const STEPS: readonly Step[] = [
  { suffix: '', global: false, tolerable: 'tolerableError', anticipated: 'anticipatedError', size: 'computedSampleSize', rates: ['anticipatedErrorRate'] },
  { suffix: '-global', global: true, tolerable: 'updatedTolerableError', anticipated: 'updatedAnticipatedError', size: 'globalComputedSampleSize', rates: ['updatedAnticipatedErrorRate', 'anticipatedErrorRate'] },
  {
    suffix: '-global-3',
    global: true,
    tolerable: 'finalTolerableError',
    anticipated: 'finalAnticipatedError',
    size: 'finalGlobalComputedSampleSize',
    rates: ['finalAnticipatedErrorRate', 'updatedAnticipatedErrorRate', 'anticipatedErrorRate'],
  },
]

const ABOVE_FIRST =
  'AE > TE: Der Stichprobenumfang ist mit der geplanten Genauigkeit |TE − AE| berechnet (nach KOM-Leitfaden EGESIF_16-0014-01, Abschnitt 7.1, S. 183 mit Fußnote 59). Die Vorlage rechnet hier anders (sie zeigt „TE ≤ AE“ und keinen Umfang). Nahe der Schwelle wird der Umfang sehr groß; der Leitfaden empfiehlt dann, die Grundgesamtheit zu teilen'
const ABOVE_GLOBAL =
  'AE > TE bei der globalen Neuberechnung: Der Umfang beruht auf der geplanten Genauigkeit |TE − AE| (nach KOM-Leitfaden EGESIF_16-0014-01, Abschnitt 7.1, S. 183 mit Fußnote 59); die Vorlage rechnet ebenso'
const AT_LEAST_4 =
  'Voraussichtliche Fehlerquote ab 4 %: Der KOM-Leitfaden EGESIF_16-0014-01 (Abschnitt 7.1, S. 183) empfiehlt, den Stichprobenumfang mit einer voraussichtlichen Fehlerquote von 4 % zu berechnen (geplante Genauigkeit höchstens 2 %). Die Webfassung rechnet mit dem eingegebenen Wert und ersetzt ihn nicht'
const EQUAL_GLOBAL =
  'Globale Neuberechnung bei AE = TE nicht anwendbar: Die Formel des Stichprobenumfangs nach Anhang II DelVO (EU) 2023/67 teilt durch TE − AE (Division durch null). Anzuwendender Umfang, Folgezeiträume und Würdigung bleiben offen. Auch ein begrenzter Stichprobenumfang wird so nicht bestätigt; als andere Maßnahme sieht Art. 5 Abs. 7 UAbs. 4 Buchst. a DelVO die Erhöhung des Stichprobenumfangs vor. Die Vorlage zeigt keinen Umfang und rechnet mit dem begrenzten Umfang bzw. den Untergrenzen weiter'

const ABOVE_FIRST_EN =
  'AE > TE: the sample size is calculated with the planned precision |TE − AE| (in accordance with Commission guidance EGESIF_16-0014-01, section 7.1, p. 183 with footnote 59). The template calculates differently here (it shows “TE ≤ AE” and no sample size). Close to the threshold the sample size becomes very large; the guidance then recommends dividing the population'
const ABOVE_GLOBAL_EN =
  'AE > TE in the global recalculation: the sample size rests on the planned precision |TE − AE| (in accordance with Commission guidance EGESIF_16-0014-01, section 7.1, p. 183 with footnote 59); the template calculates likewise'
const AT_LEAST_4_EN =
  'Anticipated error rate of 4 % or more: Commission guidance EGESIF_16-0014-01 (section 7.1, p. 183) recommends calculating the sample size with an anticipated error rate of 4 % (planned precision of maximum 2 %). The web version calculates with the value entered and does not replace it'
const EQUAL_GLOBAL_EN =
  'Global recalculation not applicable where AE = TE: the sample size formula of Annex II to Delegated Regulation (EU) 2023/67 divides by TE − AE (division by zero). The sample size to be applied, the following periods and the assessment remain open. A capped sample size is not confirmed either; as another measure, Art. 5(7), fourth subparagraph, point (a) of the Delegated Regulation provides for increasing the sample size. The template shows no sample size and continues with the capped sample size or the lower bounds'

/** Englische Fassungen je Kennung. */
const KOM_HINTS_EN: Readonly<Record<string, string>> = Object.fromEntries(
  STEPS.flatMap((step) => [
    [`anticipated-above-tolerable${step.suffix}`, step.global ? ABOVE_GLOBAL_EN : ABOVE_FIRST_EN],
    [`anticipated-at-least-4${step.suffix}`, AT_LEAST_4_EN],
    ...(step.global ? [[`size-not-applicable${step.suffix}`, EQUAL_GLOBAL_EN]] : []),
  ]),
)

const cellOf = (definition: MethodDefinition, alias: string): string | undefined => fieldsOf(definition).find((field) => field.alias === alias)?.cell

function value(definition: MethodDefinition, results: CellMap, alias: string): CellValue {
  const cell = cellOf(definition, alias)
  return cell ? (results[cell] ?? null) : null
}

/** AE > TE mit berechnetem Umfang. */
function anticipatedAbove(tolerable: CellValue, anticipated: CellValue, size: CellValue): boolean {
  return isNumber(size) && isNumber(tolerable) && isNumber(anticipated) && gt(anticipated, tolerable)
}

/** Werte eines Berechnungsschritts: TE, AE, Umfang und die zuerst eingetragene Fehlerquote. */
function stepValues(definition: MethodDefinition, results: CellMap, step: Step): [CellValue, CellValue, CellValue, CellValue] {
  const [tolerable, anticipated, size] = [step.tolerable, step.anticipated, step.size].map((alias) => value(definition, results, alias))
  const rate = step.rates.map((alias) => value(definition, results, alias)).find((entry) => !isBlank(entry))
  return [tolerable ?? null, anticipated ?? null, size ?? null, rate ?? null]
}

/** Hinweise eines Berechnungsschritts. */
function stepHints(definition: MethodDefinition, results: CellMap, step: Step): WebHint[] {
  if (!cellOf(definition, step.size)) return []
  const [tolerable, anticipated, size, rate] = stepValues(definition, results, step)
  const hints: WebHint[] = []
  if (anticipatedAbove(tolerable, anticipated, size)) hints.push({ id: `anticipated-above-tolerable${step.suffix}`, tone: 'neutral', text: step.global ? ABOVE_GLOBAL : ABOVE_FIRST })
  if (isNumber(size) && isNumber(rate) && ge(rate, 0.04)) hints.push({ id: `anticipated-at-least-4${step.suffix}`, tone: 'neutral', text: AT_LEAST_4 })
  if (step.global && size === SIZE_NOT_APPLICABLE) hints.push({ id: `size-not-applicable${step.suffix}`, tone: 'warning', text: EQUAL_GLOBAL })
  return hints
}

/** Gewählter Ansatz der Neuberechnung ist „Global“ (`LEFT(x;6)="Global"`). */
function globalChosen(definition: MethodDefinition, results: CellMap): boolean {
  return sameText(left(value(definition, results, 'recalculationApproach'), 6), 'Global')
}

/** Hinweise zur Planung bei AE > TE, AE ≥ 4 % und AE = TE; die der globalen Neuberechnung nur, wenn sie gewählt ist. */
export function komPlanningHints(definition: MethodDefinition, results: CellMap): WebHint[] {
  const global = globalChosen(definition, results)
  return STEPS.filter((step) => !step.global || global).flatMap((step) => stepHints(definition, results, step))
}

/** Englische Fassungen der Planungshinweise, die ein Blatt erzeugen kann (nach seinen Aliassen). */
export function komHintsEn(definition: MethodDefinition): Record<string, string> {
  const present = STEPS.filter((step) => cellOf(definition, step.size))
  const ids = present.flatMap((step) => [`anticipated-above-tolerable${step.suffix}`, `anticipated-at-least-4${step.suffix}`, ...(step.global ? [`size-not-applicable${step.suffix}`] : [])])
  return Object.fromEntries(ids.map((id) => [id, KOM_HINTS_EN[id] ?? '']))
}

const APPROXIMATION =
  'Anhang III, Ausschluss bzw. Ersetzung bei mehreren Schichten oder Zeiträumen: Der KOM-Leitfaden EGESIF_16-0014-01 (Abschnitt 7.10.2) passt je Schicht bzw. Zeitraum an (BV(h)); Blatt 18 rechnet mit einem Verhältnis über die ganze Zufallsschicht, weil die Lage der berührten Einheiten je Schicht bzw. Zeitraum nicht erfasst wird. Das Ergebnis in Blatt 18 ist insoweit eine anteilige Näherung'
const APPROXIMATION_EN =
  'Annex III, exclusion or replacement with several strata or periods: Commission guidance EGESIF_16-0014-01 (section 7.10.2) adjusts per stratum or period (BV(h)); sheet 18 calculates with one ratio for the whole random stratum because the location of the affected units per stratum or period is not recorded. To that extent the result in sheet 18 is a proportional approximation'

/** Kennung des Hinweises zur anteiligen Näherung nach Anhang III. */
export const APPROXIMATION_ID = 'annex-iii-approximation'

/** Deutscher Text des Hinweises zur anteiligen Näherung (auch in Blatt 18). */
export const APPROXIMATION_TEXT = APPROXIMATION

/**
 * Hinweis an geschichteten bzw. mehrzeitigen Verfahren, wenn in Blatt 02
 * Ausschluss oder (bei der einfachen Zufallsstichprobe, Tabelle 2) Ersetzung
 * gewählt und mindestens eine Einheit berührt ist.
 */
export function annexIIIApproximation(context: SheetContext | undefined, replacementAdjusts: boolean): WebHint[] {
  const population = context?.sheets['02_Grundgesamtheit']
  if (!population || !isNumber(population.C47) || !gt(population.C47, 0)) return []
  const exclusion = sameText(left(population.C49, 10), 'Ausschluss')
  const replacement = sameText(left(population.C49, 9), 'Ersetzung')
  return exclusion || (replacement && replacementAdjusts) ? [{ id: APPROXIMATION_ID, tone: 'warning', text: APPROXIMATION }] : []
}

/** Englische Fassung des Hinweises zur anteiligen Näherung. */
export const APPROXIMATION_EN_TEXT: Readonly<Record<string, string>> = { [APPROXIMATION_ID]: APPROXIMATION_EN }
