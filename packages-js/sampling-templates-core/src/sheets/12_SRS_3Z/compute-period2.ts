/**
 * Rechenkern Blatt 12_SRS_3Z, Abschnitt L: Neuberechnung nach Zeitraum 1 für
 * die Zeiträume 2 und 3 (C58–C86). Jede Zuweisung bildet die Formel der
 * gleichnamigen Zelle der Vorlage nach.
 */
import { guard, isBlank, minus, n, required } from '../../excel/index'
import type { CellAddress, Cells, SheetContext } from '../../model/types'
import { type Pending, type Recalculation, additionalUnits, appliedRandomSize, auditedTerm, globalComputedSize, increasedSize, minimumRandomSize, netLimitedSize, periodSize, share, standardSize, weightedDeviation } from '../shared/srs'
import { blockedGlobal } from '../shared/periods'

/** Ist-Werte des Zeitraums 2 und aktualisierte Größen des Geschäftsjahres (C58–C70). */
function updated(c: Cells): void {
  c.C58 = guard(() => minus(required(c.C53), n(c.C55)))
  c.C59 = guard(() => minus(required(c.C54), n(c.C56)))
  c.C65 = guard(() => required(c.C7) + required(c.C53) + required(c.C60))
  c.C66 = guard(() => required(c.C25) * required(c.C65))
  // =IF(C64="";C28;C64)*C65 – leer = Wert aus I.
  c.C67 = guard(() => required(isBlank(c.C64) ? c.C28 : c.C64) * required(c.C65))
  // =IF(C50="";C31;C50) – s aus der Stichprobe, ersatzweise σ.
  c.C68 = (isBlank(c.C50) ? c.C31 : c.C50) ?? null
  c.C69 = guard(() => required(c.C59) + required(c.C61))
  c.C70 = weightedDeviation([[c.C59, c.C62], [c.C61, c.C63]], c.C69)
}

/**
 * Standardansatz (C71–C74). Ist der Nenner nicht positiv, steht in C72 der Text
 * der Vorlage; C73 und C74 rechnen dann mit einem Text und zeigen wie die
 * Vorlage nichts (`ROUNDUP` mit Text ist ein Fehlerwert).
 */
function standard(c: Cells): void {
  c.C71 = guard(() => minus(minus(required(c.C66), required(c.C67)) ** 2, auditedTerm(c.C23, c.C13, c.C45, c.C68)))
  c.C72 = standardSize(c.C23, c.C69, c.C70, c.C71)
  c.C73 = share(c.C59, c.C69, c.C72)
  c.C74 = share(c.C61, c.C69, c.C72)
}

/** Globaler Ansatz (C75–C82). */
function global(c: Cells, pending: Pending): void {
  c.C75 = guard(() => required(c.C13) + required(c.C59) + required(c.C61))
  c.C76 = weightedDeviation([[c.C13, c.C68], [c.C59, c.C62], [c.C61, c.C63]], c.C75)
  c.C77 = globalComputedSize(c.C23, c.C75, c.C76, c.C66, c.C67)
  c.C78 = netLimitedSize(c.C41, c.C11, c.C57)
  c.C79 = appliedRandomSize(c.C77, minimumRandomSize(9, c.C10, c.C56), c.C78, pending('C77'))
  c.C80 = additionalUnits(c.C13, c.C75, c.C79, c.C45)
  c.C81 = share(c.C59, c.C75, c.C79)
  c.C82 = share(c.C61, c.C75, c.C79)
}

/** Zelle des Umfangs für Zeitraum 2 nach dem gewählten Ansatz (C35). */
const CHOSEN: Readonly<Record<Recalculation, CellAddress>> = { standard: 'C73', global: 'C81', increase: 'C83', none: 'C46' }
/** Zelle des fortgeschriebenen Planumfangs für Zeitraum 3; Erhöhung und „keine Neuberechnung“ behalten den Plan aus J. */
const PLANNED: Readonly<Record<Recalculation, CellAddress>> = { standard: 'C74', global: 'C82', increase: 'C47', none: 'C47' }

/**
 * Erhöhung bei begrenztem Umfang und Ergebnis der ersten Neuberechnung (C83–C86).
 * C84 = MAX(gewählter Umfang;3): Steht im gewählten Umfang nichts, übergeht
 * `MAX` den Bezug und liefert 3. Nach nicht positivem Nenner des Standardansatzes
 * (C72 trägt den Text der Vorlage, C73 bleibt leer) steht das wie in der Vorlage;
 * fehlt der gewählte Umfang aus anderem Grund (leeres Formular, „TE ≤ AE“), ist
 * die 3 ein Wert ohne Grundlage (`periodSize`).
 */
function applied(c: Cells, pending: Pending, approach: Recalculation, context: SheetContext): void {
  c.C83 = guard(() => increasedSize(c.C46, [[c.C53, c.C14], [c.C59, c.C15]]))
  const chosen = c[CHOSEN[approach]]
  const notApplicable = approach === 'standard' && typeof c.C72 === 'string'
  // Globaler Ansatz nach der DelVO nicht anwendbar (AE ≥ TE): Umfang offen statt Untergrenze.
  const blocked = approach === 'global' && blockedGlobal(c, 'C77', pending)
  c.C84 = periodSize(chosen, { open: pending(CHOSEN[approach]) || blocked, notApplicable }, context)
  c.C85 = c[PLANNED[approach]] ?? null
  c.C86 = guard(() => required(c.C45) + (approach === 'global' ? required(c.C80) : 0))
}

/** Abschnitt L: Neuberechnung nach Zeitraum 1 („Zweiter Zeitraum“). */
export function secondPeriod(c: Cells, pending: Pending, approach: Recalculation, context: SheetContext): void {
  updated(c)
  standard(c)
  global(c, pending)
  applied(c, pending, approach, context)
}
