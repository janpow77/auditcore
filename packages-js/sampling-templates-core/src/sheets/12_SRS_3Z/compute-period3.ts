/**
 * Rechenkern Blatt 12_SRS_3Z, Abschnitt N: Neuberechnung nach Zeitraum 2 für
 * Zeitraum 3 und endgültige Umfänge des Geschäftsjahres (C97–C120). Jede
 * Zuweisung bildet die Formel der gleichnamigen Zelle der Vorlage nach.
 */
import { guard, isBlank, isNumber, minus, n, required } from '../../excel/index'
import type { CellAddress, Cells, SheetContext } from '../../model/types'
import { type Pending, type Recalculation, additionalUnits, appliedRandomSize, auditedTerm, checkAnnualMinimum, globalComputedSize, increasedSize, minimumRandomSize, netLimitedSize, periodSize, share, standardSize, weightedDeviation } from '../shared/srs'
import { blockedGlobal } from '../shared/periods'

/** Ist-Werte des Zeitraums 3 und endgültige Größen des Geschäftsjahres (C97–C104). */
function updated(c: Cells): void {
  c.C97 = guard(() => minus(required(c.C92), n(c.C94)))
  c.C98 = guard(() => minus(required(c.C93), n(c.C95)))
  c.C101 = guard(() => required(c.C7) + required(c.C53) + required(c.C92))
  c.C102 = guard(() => required(c.C25) * required(c.C101))
  // =IF(C100="";IF(C64="";C28;C64);C100)*C101 – leer = vorheriger Wert.
  const previous = isBlank(c.C64) ? c.C28 : c.C64
  c.C103 = guard(() => required(isBlank(c.C100) ? previous : c.C100) * required(c.C101))
  // =IF(C89="";C62;C89) – s aus der Stichprobe, ersatzweise σ.
  c.C104 = (isBlank(c.C89) ? c.C62 : c.C89) ?? null
}

/** Standardansatz (C105, C106) und globaler Ansatz (C107–C114). */
function approaches(c: Cells, pending: Pending): void {
  c.C105 = guard(() => minus(minus(minus(required(c.C102), required(c.C103)) ** 2, auditedTerm(c.C23, c.C13, c.C86, c.C68)), auditedTerm(c.C23, c.C59, c.C84, c.C104)))
  c.C106 = standardSize(c.C23, c.C98, c.C99, c.C105)
  c.C107 = guard(() => required(c.C13) + required(c.C59) + required(c.C98))
  c.C108 = weightedDeviation([[c.C13, c.C68], [c.C59, c.C104], [c.C98, c.C99]], c.C107)
  c.C109 = globalComputedSize(c.C23, c.C107, c.C108, c.C102, c.C103)
  c.C110 = netLimitedSize(c.C41, c.C11, c.C57, c.C96)
  c.C111 = appliedRandomSize(c.C109, minimumRandomSize(9, c.C10, c.C56, c.C95), c.C110, pending('C109'))
  c.C112 = additionalUnits(c.C13, c.C107, c.C111, c.C86)
  c.C113 = additionalUnits(c.C59, c.C107, c.C111, c.C84)
  c.C114 = share(c.C98, c.C107, c.C111)
}

/** Zelle des Umfangs für Zeitraum 3 nach dem gewählten Ansatz (C35). */
const CHOSEN: Readonly<Record<Recalculation, CellAddress>> = { standard: 'C106', global: 'C114', increase: 'C115', none: 'C47' }

/**
 * Erhöhung bei begrenztem Umfang und endgültige Umfänge (C115–C120).
 * C118 = MAX(gewählter Umfang;3;30 − bisherige Umfänge − umfassende Schichten):
 * Steht im gewählten Umfang der Text „✖ nicht anwendbar (Nenner ≤ 0)“ (C106),
 * übergeht `MAX` den Bezug; es bleiben 3 und die Auffüllung auf 30 Einheiten.
 * Fehlt der gewählte Umfang ganz, sind sie ein Wert ohne Grundlage (`periodSize`).
 */
function applied(c: Cells, pending: Pending, approach: Recalculation, context: SheetContext): void {
  c.C115 = guard(() => increasedSize(c.C85, [[c.C92, c.C60], [c.C98, c.C61]]))
  const chosen = c[CHOSEN[approach]]
  c.C116 = guard(() => required(c.C86) + (approach === 'global' ? required(c.C112) : 0))
  c.C117 = guard(() => required(c.C84) + (approach === 'global' ? required(c.C113) : 0))
  const exhaustive = [c.C10, c.C56, c.C95].map(n)
  const shortfall = (): number => exhaustive.reduce((rest, units) => minus(rest, units), minus(minus(30, required(c.C116)), required(c.C117)))
  const blocked = approach === 'global' && (blockedGlobal(c, 'C77', pending) || blockedGlobal(c, 'C109', pending))
  c.C118 = periodSize(chosen, { open: pending(CHOSEN[approach]) || blocked, notApplicable: typeof chosen === 'string' }, context, shortfall)
  c.C119 = guard(() => exhaustive.reduce((total, units) => total + units, required(c.C116) + required(c.C117) + required(c.C118)))
  c.C120 = isNumber(c.C118) && isNumber(c.C119) ? checkAnnualMinimum(c.C119) : null
}

/** Abschnitt N: Neuberechnung nach Zeitraum 2 („Dritter Zeitraum“). */
export function thirdPeriod(c: Cells, pending: Pending, approach: Recalculation, context: SheetContext): void {
  updated(c)
  approaches(c, pending)
  applied(c, pending, approach, context)
}
