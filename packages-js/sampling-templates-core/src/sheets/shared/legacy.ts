/**
 * Gemeinsame Bausteine der Altvorlagen von 2017 (Blätter X1–X4, „Weitere
 * Methoden nach Art. 79“). Die Altvorlagen kennen weder farbige Eingabezellen
 * noch Prüfhinweise noch `N(…)`: Jede leere Zelle zählt in der Rechnung 0,
 * Fehlerwerte werden zu `""`. Die Rechenkerne trennen deshalb zwei Fragen:
 *
 * 1. **Was rechnet die Vorlage?** Die Formel jeder Zelle wird mit leeren
 *    Eingaben als 0 nachgebildet (`LegacyCells.input`); eine Formelzelle ohne
 *    Wert ist in der Rechnung ein Fehlerwert (`LegacyCells.value`).
 * 2. **Fehlt eine Angabe?** Liest eine Zelle – unmittelbar oder über andere
 *    Zellen – eine leere Pflichteingabe, zeigt die Webfassung „Angabe fehlt“
 *    (`null`) statt des mit 0 gerechneten Werts (docs/abweichungen.md).
 *
 * Sind alle Pflichteingaben belegt, entscheidet allein die erste Frage; so
 * besteht jede begründete Abweichung die Gegenprobe des Golden-Abgleichs.
 *
 * Fallarten der Richtlinie für fehlende Angaben (`model/policy.ts`) in den
 * Altvorlagen: Pflichteingaben sind `requiredInput` (`LegacyCells`, Abweichung
 * ohne `kind`); die Standardabweichung der Stichprobe, die nur die Genauigkeit
 * betrifft, ist `sampleDeviation` (X2: C15, X3: Zeile 21, X4: C35); die
 * Fehlersumme einer Schicht bzw. eines Zeitraums neben einer eingetragenen ist
 * `partialErrorSum` (X3: Zeile 19, X4: C21/C34); eine Summe über Schichten
 * ohne Wert samt Folgezellen ist `withoutBasis` (X3: D23–D25).
 */
import { FormulaError, eq, guard, gt, isBlank, isNumber, le, lt, required } from '../../excel/index'
import type { ZeroAssumption } from '../../model/sheet'
import { EXTRA_STRATA } from '../../model/strata'
import type { SheetTexts } from '../../model/texts'
import type { CellAddress, CellValue, Cells, Deviation, WebHint } from '../../model/types'

/** Hinweis der Vorlage in jedem Blatt der Altvorlagen (X1: G1, X2: E1, X3: M1, X4: F1), wörtlich. */
export const LEGACY_NOTICE =
  'Altvorlage 2014–2020 (Fassung 30.06.2017), rechnerisch unverändert (nur Unterdrückung von Fehlerwerten bei leeren Eingaben). Keine gebrauchsfertige Methode im Sinne der DelVO (EU) 2023/67. Anwendung nur als eigene Methode nach Art. 79 VO (EU) 2021/1060 (ErwG 15 DelVO) mit methodischer Begründung; z-Werte nur zweiseitig, Fehlergrenze ohne systembedingte und anomale Fehler.'

/** Bezeichnung der Hinweiszeile: der Anfang des Hinweises der Vorlage (die Zelle hat keine Nachbarbezeichnung). */
export const LEGACY_NOTICE_LABEL = 'Altvorlage 2014–2020 (Fassung 30.06.2017)'

/** Rechtsgrundlage laut Blatt 00, Zeile „X1–X4 (grau)“. */
export const LEGACY_LEGAL_BASIS = 'nur Art. 79 VO (EU) 2021/1060 (ErwG 15)'

/** Wesentlichkeitsschwelle: in den Altvorlagen eine feste Zelle (2 %), keine Eingabe. */
export const LEGACY_MATERIALITY = 0.02

/** Mindeststichprobenumfang der Altvorlagen X1–X3. */
export const LEGACY_MINIMUM_SIZE = 30

/** Stufen eines Faktors nach dem Konfidenzniveau: `[Niveau, Faktor]`. */
export type LevelSteps = readonly (readonly [level: number, factor: number])[]

/** z der Normalverteilung, zweiseitig (X2: C6, X3: D10, X4: C11). */
export const LEGACY_Z: LevelSteps = [
  [0.6, 0.842],
  [0.7, 1.036],
  [0.8, 1.282],
  [0.9, 1.645],
  [0.95, 1.96],
]

/** Zuverlässigkeitsfaktor RF des konservativen MUS-Ansatzes (X1: C5). */
export const LEGACY_RELIABILITY_FACTOR: LevelSteps = [
  [0.6, 0.92],
  [0.7, 1.21],
  [0.8, 1.61],
  [0.9, 2.31],
  [0.95, 3],
]

/** Erweiterungsfaktor EF des konservativen MUS-Ansatzes (X1: C6). */
export const LEGACY_EXPANSION_FACTOR: LevelSteps = [
  [0.6, 1.1],
  [0.7, 1.2],
  [0.8, 1.3],
  [0.9, 1.5],
  [0.95, 1.6],
]

/**
 * Faktor zum Konfidenzniveau. Die Vorlage fragt die fünf Stufen nacheinander
 * ab; trifft keine zu, liefert sie den Wahrheitswert FALSCH, der in der
 * Rechnung 0 zählt (die neu berechnete Mappe speichert ihn als 0).
 */
export function levelFactor(level: unknown, steps: LevelSteps): number {
  if (!isNumber(level)) return 0
  return steps.find(([step]) => eq(step, level))?.[1] ?? 0
}

/** Mindestumfang: Ein rechnerischer Umfang unter 30 wird 30 (auch ein negativer). */
export function atLeastMinimum(size: number): number {
  return lt(size, LEGACY_MINIMUM_SIZE) ? LEGACY_MINIMUM_SIZE : size
}

/**
 * Zellen eines Blatts der Altvorlagen während der Berechnung. `mandatory`
 * nennt die Pflichteingaben; Eingaben, die die Webfassung wie die Vorlage mit
 * 0 rechnet (Standardabweichung der Stichprobe), gehören nicht dazu.
 */
export class LegacyCells {
  private readonly open = new Set<CellAddress>()

  constructor(
    readonly cells: Cells,
    private readonly mandatory: ReadonlySet<CellAddress>,
  ) {}

  /** Eingabezelle in einer Rechnung: leer zählt 0 wie in der Vorlage, Text ist ein Fehlerwert. */
  input(cell: CellAddress): number {
    const value = this.cells[cell]
    if (isBlank(value)) return 0
    if (!isNumber(value)) throw new FormulaError('#WERT!')
    return value
  }

  /** Formelzelle in einer Rechnung: Zeigt sie keinen Wert, ist das Ergebnis ein Fehlerwert. */
  value(cell: CellAddress): number {
    return required(this.cells[cell])
  }

  /** Ist die Zelle offen: eine leere Pflichteingabe oder eine Formelzelle, die von einer abhängt? */
  isOpen(cell: CellAddress): boolean {
    return this.open.has(cell) || (this.mandatory.has(cell) && isBlank(this.cells[cell]))
  }

  /**
   * Formelzelle setzen. `reads` nennt die Zellen, die die Formel liest; ist
   * eine davon offen, bleibt auch diese Zelle offen („Angabe fehlt“).
   */
  set(cell: CellAddress, reads: readonly CellAddress[], formula: () => CellValue): void {
    if (reads.some((read) => this.isOpen(read))) {
      this.open.add(cell)
      this.cells[cell] = null
      return
    }
    this.cells[cell] = guard(formula)
  }
}

/** Begründete Abweichungen mehrerer Zellen mit denselben auslösenden Eingaben. */
export function deviationRows(cells: readonly CellAddress[], whenEmpty: readonly CellAddress[], template: string, reason: string): Deviation[] {
  return cells.map((cell) => ({ cell, whenEmpty, template, reason }))
}

/**
 * Abweichungen der Fallart „Wert ohne Grundlage“: Die Vorlage zeigt an `cells`
 * einen Wert, obwohl die Größe in `whenEmpty` fehlt (Summe über Schichten ohne
 * Wert und was darauf aufbaut); der Rechenkern gibt ihn über `totalRow` zurück.
 */
export function unfoundedRows(cells: readonly CellAddress[], whenEmpty: readonly CellAddress[], template: string, reason: string): Deviation[] {
  return cells.map((cell) => ({ cell, whenEmpty, template, reason, kind: 'withoutBasis' }))
}

/**
 * Mit 0 gerechnete Fehlersummen (`partialErrorSum`): Von den Eingaben
 * `inputs` (Fehlersumme je Schicht bzw. je Zeitraum) trägt mindestens eine
 * einen Wert, eine andere ist leer – die Vorlage zeigt deshalb ein Ergebnis.
 * `cellsOf` nennt die Zellen, die von der leeren Eingabe abhängen. Trägt keine
 * Eingabe einen Wert, fehlt eine Pflichteingabe (`requiredInput`).
 */
export function partialErrorSums(results: Readonly<Record<CellAddress, CellValue | undefined>>, inputs: readonly CellAddress[], cellsOf: (input: CellAddress) => readonly CellAddress[]): ZeroAssumption[] {
  if (inputs.every((input) => isBlank(results[input]))) return []
  return inputs.filter((input) => isBlank(results[input])).map((input) => ({ input, cells: cellsOf(input), kind: 'partialErrorSum' }))
}

/** Schichtspalten der Altvorlage X3 (E–I „1–5“, J „…“, K „k“); die Summen stehen in Spalte D. */
export const LEGACY_TEMPLATE_STRATA: readonly string[] = ['E', 'F', 'G', 'H', 'I', 'J', 'K']

/** Schichtspalten von X3 in der Webfassung: sieben der Vorlage, danach die 8. bis 20. Schicht (AA–AM). */
export const LEGACY_STRATA: readonly string[] = [...LEGACY_TEMPLATE_STRATA, ...EXTRA_STRATA]

/** Hinweis der Webfassung in Warnfarbe. */
function warning(id: string, text: string): WebHint {
  return { id, tone: 'warning', text }
}

/** Hinweis der Webfassung: Stichprobenumfang größer als die Anzahl der Einheiten. */
export function sizeExceedsPopulation(size: CellValue | undefined, units: CellValue | undefined): WebHint[] {
  if (!isNumber(size) || !isNumber(units) || !gt(units, 0) || !gt(size, units)) return []
  return [warning('size-exceeds-population', 'Stichprobenumfang übersteigt die Anzahl der Einheiten der Grundgesamtheit')]
}

/**
 * Hinweis der Webfassung: Der zulässige Fehler ist nicht größer als der
 * voraussichtliche (X1: mal Erweiterungsfaktor). Die Altvorlagen prüfen das
 * nicht; sie zeigen dann keinen oder einen nicht belastbaren Umfang.
 */
export function tolerableNotAboveAnticipated(tolerable: CellValue | undefined, anticipated: CellValue | undefined, text: string, id = 'tolerable-error-not-above-anticipated'): WebHint[] {
  if (!isNumber(tolerable) || !isNumber(anticipated) || !gt(tolerable, 0) || !le(tolerable, anticipated)) return []
  return [warning(id, text)]
}

/** Wortlaut des Hinweises „TE ≤ AE“ der Blätter X2 und X3. */
export const TOLERABLE_HINT = 'TE ≤ AE: Die Altvorlage prüft das nicht; der ausgewiesene Stichprobenumfang ist nicht belastbar'

/** Hinweis der Webfassung: weniger als drei Stichprobeneinheiten (Fußnote der Altvorlagen X3 und X4). */
export function belowThreeUnits(sizes: readonly (CellValue | undefined)[], text: string): WebHint[] {
  return sizes.some((size) => isNumber(size) && lt(size, 3)) ? [warning('below-three-units', text)] : []
}

/** Kennung des Hinweises „weniger als drei Einheiten“ für die Schicht mit der Nummer `stratum` (X3). */
export const belowThreeUnitsId = (stratum: number): string => `below-three-units-${stratum}`

/**
 * Hinweis der Webfassung je Schicht mit weniger als drei Stichprobeneinheiten
 * (X3); er nennt die Schichtnummer. `sizes`: Schichtnummer und Umfang.
 */
export function strataBelowThreeUnits(sizes: readonly (readonly [stratum: number, size: CellValue | undefined])[]): WebHint[] {
  return sizes
    .filter(([, size]) => isNumber(size) && lt(size, 3))
    .map(([stratum]) => warning(belowThreeUnitsId(stratum), `Schicht ${stratum}: weniger als drei Stichprobeneinheiten (Fußnote der Altvorlage: mindestens 3 je Schicht)`))
}

/**
 * Hinweis der Webfassung: negativer Stichprobenumfang. Die Altvorlagen prüfen
 * den Nenner nicht und rechnen mit dem negativen Umfang weiter; die Webfassung
 * zeigt ihn wie die Vorlage und weist ihn in Warnfarbe aus.
 */
export function negativeSize(size: CellValue | undefined, id: string, text: string): WebHint[] {
  return isNumber(size) && lt(size, 0) ? [warning(id, text)] : []
}

export type { DataTable, DataTableColumn } from '../../model/table'

/** Englische Arbeitsübersetzung der Texte, die alle Altvorlagen teilen (nicht amtlich). */
export const LEGACY_NOTICE_EN =
  'Legacy template 2014–2020 (version of 30 June 2017), computationally unchanged (only error values for empty inputs are suppressed). Not a ready-to-use method within the meaning of Delegated Regulation (EU) 2023/67. To be applied only as an own method under Art. 79 of Regulation (EU) 2021/1060 (recital 15 of the Delegated Regulation) with a methodological justification; z values two-sided only, error limit without systemic and anomalous errors.'

const WEB_HINTS_EN: Readonly<Record<string, string>> = {
  'size-exceeds-population': 'Sample size exceeds the number of units in the population',
  'tolerable-error-not-above-anticipated': 'TE ≤ AE: the legacy template does not check this; the sample size shown is not reliable',
  'below-three-units': 'Fewer than three sampling units (footnote of the legacy template: minimum of 3)',
}

/** Englische Fassung der Hinweise je Schicht (`belowThreeUnitsId`) für alle Schichten von X3. */
export function strataHintsEn(): Record<string, string> {
  return Object.fromEntries(LEGACY_STRATA.map((_, index) => [belowThreeUnitsId(index + 1), `Stratum ${index + 1}: fewer than three sampling units (footnote of the legacy template: minimum of 3 per stratum)`]))
}

/**
 * Englische Arbeitsübersetzung eines Blatts der Altvorlagen. Bezeichnungen und
 * Abschnitte sind in der Vorlage von 2017 bereits englisch; übersetzt werden
 * Titel, Rechtsgrundlage, der Hinweis der Vorlage und die Hinweise der Webfassung.
 */
export function legacyTexts(noticeCell: CellAddress, title: string, shortTitle: string, webHints: Readonly<Record<string, string>> = {}): SheetTexts {
  return {
    title,
    shortTitle,
    legalBasis: 'Art. 79 of Regulation (EU) 2021/1060 only (recital 15)',
    fields: { [noticeCell]: { label: 'Legacy template 2014–2020 (version of 30 June 2017)' } },
    values: { [LEGACY_NOTICE]: LEGACY_NOTICE_EN },
    webHints: { ...WEB_HINTS_EN, ...webHints },
  }
}
