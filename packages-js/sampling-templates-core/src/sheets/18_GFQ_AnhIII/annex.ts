/**
 * Anpassung nach Anhang III bei Ausschluss oder Ersetzung (Art. 80 Abs. 3 VO
 * (EU) 2021/1060) nach den Vorgaben der KOM (Entscheidung des Inhabers vom
 * 17.10.2026; Anhang III DelVO (EU) 2023/67 und KOM-Leitfaden
 * EGESIF_16-0014-01, Abschnitte 7.10.2 und 7.10.3; `docs/abweichungen.md` Nr. 16).
 *
 * Der Leitfaden passt je Schicht an: Der Zufallsteil wird mit dem Verhältnis der
 * Zufallsschicht BV_s / BV_s,r angepasst, die hochwertige bzw. umfassende Schicht
 * über EE_e = EE_e,r · BV_e / BV_e,r (Beispiele 7.10.3.1 b, 7.10.3.2, 7.10.3.4).
 * Dafür braucht es die Lage der berührten Einheiten (Abschnitt F, freiwillig).
 * Ohne sie rechnet die Webfassung wie die Vorlage mit dem Gesamtfaktor
 * BV / BV_r (Ausschluss) bzw. mit der Gesamt-Näherung (Ersetzung, Tabelle 2)
 * und weist darauf hin.
 */
import { divide, eq, guard, isBlank, isNumber, left, minus, n, plus, required, sameText } from '../../excel/index'
import { unfounded } from '../../model/policy'
import type { CellMap, CellValue, Cells, SheetContext } from '../../model/types'

/** Blatt, aus dem die Grundgesamtheiten stammen. */
const POPULATION_SHEET = '02_Grundgesamtheit'

/** Text der Vorlage, wenn es keine Genauigkeit gibt (nichtstatistische Verfahren). */
export const NOT_APPLICABLE = 'n. a.'

/** `LEFT($C$15;10)="Ausschluss"` */
export const isExclusion = (c: CellMap): boolean => sameText(left(c.C15, 10), 'Ausschluss')

/** Ersetzung bei einem Verfahren der Tabelle 2 (einfache Zufallsstichprobe/Auswahl mit gleicher Wahrscheinlichkeit). */
export const isReplacementTable2 = (c: CellMap): boolean => sameText(left(c.C15, 9), 'Ersetzung') && sameText(left(c.C11, 9), 'Tabelle 2')

/** Lage der berührten Einheiten (Abschnitt F): Einheiten und Buchwert der hochwertigen bzw. umfassenden Schicht, davon berührt. */
export interface Location {
  units: number
  bookValue: number
  affectedUnits: number
  affectedBookValue: number
}

/** Abschnitt F, nur wenn alle vier Angaben eingetragen sind (freiwillige Gruppe). */
export function locationOf(c: CellMap): Location | null {
  const values = [c.C31, c.C32, c.C33, c.C34]
  if (!values.every(isNumber)) return null
  const [units, bookValue, affectedUnits, affectedBookValue] = values as [number, number, number, number]
  return { units, bookValue, affectedUnits, affectedBookValue }
}

/**
 * Abschnitt F, abgeleitete Größen (C35–C38): berührte Einheiten der
 * Zufallsschicht A_s = A − A_e, Buchwert der Zufallsschicht ursprünglich
 * BV_s = BV_u − BV_e und reduziert BV_s,r = BV_s − (BV_A − BV_A,e), Faktor
 * der Zufallsschicht BV_s / BV_s,r.
 */
export function randomStratum(c: Cells, context: SheetContext): void {
  const location = locationOf(c)
  const population = context.sheets[POPULATION_SHEET] ?? {}
  c.C35 = location ? guard(() => minus(required(population.C47), location.affectedUnits)) : null
  c.C36 = location ? guard(() => minus(required(c.C14), location.bookValue)) : null
  c.C37 = location ? guard(() => minus(required(c.C36), minus(required(c.C16), location.affectedBookValue))) : null
  c.C38 = location ? guard(() => divide(required(c.C36), required(c.C37))) : null
}

/** Faktor der hochwertigen bzw. umfassenden Schicht BV_e / BV_e,r (1, wenn keine ihrer Einheiten berührt ist). */
function exhaustiveFactor(location: Location): number {
  return eq(location.affectedBookValue, 0) ? 1 : divide(location.bookValue, minus(location.bookValue, location.affectedBookValue))
}

/** C24 nach KOM mit erfasster Lage: EE_e · BV_e/BV_e,r + Zufallsteil, beim Ausschluss mal BV_s/BV_s,r. */
function errorByStratum(c: Cells, location: Location): CellValue {
  return guard(() => {
    const random = minus(required(c.C6), required(c.C7))
    return plus(required(c.C7) * exhaustiveFactor(location), isExclusion(c) ? random * required(c.C38) : random)
  })
}

/** C24 wie die Vorlage: Ausschluss EE · BV/BV_r; mit Abschnitt C nur der Zufallsteil skaliert, dazu EE_e aus C23. */
function errorLikeTemplate(c: Cells): CellValue {
  const exclusion = isExclusion(c)
  if (!sameText(c.C20, 'Ja')) return exclusion ? guard(() => required(c.C6) * required(c.C18)) : (c.C6 ?? null)
  return guard(() => {
    const random = minus(required(c.C6), required(c.C7))
    return plus(exclusion ? random * required(c.C18) : random, required(c.C23))
  })
}

/** C24: angepasster extrapolierter Fehler nach Anhang III. */
export function adjustedError(c: Cells): CellValue {
  const location = locationOf(c)
  return location ? errorByStratum(c, location) : errorLikeTemplate(c)
}

/**
 * Genauigkeit bei Ersetzung, Tabelle 2 (Anhang III Tabelle 2; Leitfaden 7.10.2,
 * Fußnote 70): für die reduzierte Grundgesamtheit berechnen, dann mit
 * BV(h) ursprünglich / BV(h) reduziert anpassen. Das Methodenblatt rechnet mit
 * N_s der ursprünglichen Zufallsschicht; die Genauigkeit ist proportional zu N,
 * reduziert also SE · (N_s − A_s)/N_s, danach · BV_s/BV_s,r. Ohne erfasste Lage
 * Gesamt-Näherung SE · (N − A)/N · BV/BV_r – exakt nur ohne hochwertige bzw.
 * umfassende Schicht.
 */
function replacementPrecision(c: Cells, context: SheetContext, location: Location | null): CellValue {
  const population = context.sheets[POPULATION_SHEET] ?? {}
  return guard(() => {
    const units = location ? minus(required(population.C52), location.units) : required(population.C52)
    const affected = location ? required(c.C35) : n(population.C47)
    return required(c.C8) * divide(minus(units, affected), units) * required(location ? c.C38 : c.C18)
  })
}

/** C25: angepasste Genauigkeit; ohne Genauigkeit im Methodenblatt „n. a.“. */
export function adjustedPrecision(c: Cells, context: SheetContext): CellValue {
  // Ohne Wert in C8 zeigt die Vorlage „n. a.“ – auch dann, wenn das Methodenblatt nur noch keine Genauigkeit liefert.
  if (isBlank(c.C8)) return unfounded(context, NOT_APPLICABLE)
  if (!isNumber(c.C8)) return NOT_APPLICABLE
  const location = locationOf(c)
  // Ausschluss: Genauigkeit der reduzierten Grundgesamtheit mal BV_s/BV_s,r (mit Lage) bzw. BV/BV_r wie die Vorlage.
  if (isExclusion(c)) return guard(() => required(c.C8) * required(location ? c.C38 : c.C18))
  // Ersetzung, Tabelle 1: für die ursprüngliche Grundgesamtheit, ohne Anpassung.
  return isReplacementTable2(c) ? replacementPrecision(c, context, location) : c.C8
}
