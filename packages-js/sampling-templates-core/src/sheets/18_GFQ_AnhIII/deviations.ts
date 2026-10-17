/**
 * Begründete Abweichungen des Blatts 18 vom Verhalten der Vorlage. Die Webfassung
 * zeigt nie einen anderen Wert als die Vorlage, höchstens keinen.
 *
 * Zwei Fallarten kommen vor:
 * - Eigene Pflichteingaben (Buchwert der ursprünglichen hochwertigen Schicht,
 *   Signifikanzschwelle, Behandlung nach Art. 80 Abs. 3 aus Blatt 02): Die
 *   Vorlage rechnet mit der leeren Zelle als 0, die Webfassung zeigt „Angabe fehlt“.
 * - Werte ohne Grundlage (`withoutBasis`): Blatt 02 oder das Methodenblatt zeigen
 *   in der Webfassung „Angabe fehlt“, während die Vorlage dort mit 0 weiterrechnet
 *   und Blatt 18 darauf aufbaut. `whenEmpty` nennt die Zellen des Blatts 18, die
 *   deshalb leer sind. Gegenprobe im Abgleich: Rechnet der ganze Arbeitsstand
 *   „wie die Vorlage“, zeigt jede dieser Zellen genau den Wert der Vorlage.
 */
import type { CellAddress, Deviation } from '../../model/types'

const UPSTREAM_TEMPLATE = 'Wert auf Grundlage der in Blatt 02 bzw. im Methodenblatt mit 0 gerechneten leeren Eingaben; ohne Genauigkeit „n. a.“'
const UPSTREAM_REASON = 'Blatt 02 bzw. das Methodenblatt zeigen für die zugrunde liegende Größe „Angabe fehlt“; ein darauf aufbauender Wert hätte keine Grundlage.'

/** Zelle des Blatts 18 → Zellen, auf denen sie unmittelbar aufbaut und die ohne Wert aus Blatt 02 bzw. dem Methodenblatt leer sind. */
const UPSTREAM: readonly (readonly [cell: CellAddress, whenEmpty: readonly string[]])[] = [
  ['C5', ['C5']],
  ['C6', ['C6']],
  ['C7', ['C7']],
  ['C8', ['C8']],
  ['C12', ['02_Grundgesamtheit!C39']],
  ['C14', ['C12']],
  ['C17', ['C14']],
  ['C18', ['C14', 'C17']],
  ['C19', ['C5', 'C14', 'C17']],
  ['C23', ['C7']],
  ['C24', ['C6', 'C7', 'C18', 'C23']],
  ['C25', ['C8', 'C18']],
  ['C26', ['C14', 'C24']],
  ['C27', ['C12', 'C26']],
  ['C28', ['C14', 'C24', 'C25']],
  ['C30', ['C26', 'C28']],
]

function entries(cells: readonly CellAddress[], whenEmpty: readonly string[], template: string, reason: string): Deviation[] {
  return cells.map((cell) => ({ cell, whenEmpty, template, reason }))
}

const HIGH_VALUE = 'Die Anpassung der hochwertigen Schicht setzt den Buchwert der ursprünglichen hochwertigen Schicht voraus; mit 0 entfiele der Fehler der umfassenden Schicht.'

export const deviations: readonly Deviation[] = [
  ...UPSTREAM.map(([cell, whenEmpty]): Deviation => ({ cell, whenEmpty, template: UPSTREAM_TEMPLATE, reason: UPSTREAM_REASON, kind: 'withoutBasis' })),
  ...entries(['C15'], ['02_Grundgesamtheit!C49'], '0 (Bezug auf die leere Auswahlzelle in Blatt 02)', 'Ohne Auswahl in Blatt 02 ist die Behandlung der nicht prüfbaren Einheiten unbekannt, nicht 0.'),
  // Die Schwelle steht vor der hochwertigen Schicht: Der Abgleich nennt die erste zutreffende Zeile, und BV_e,u ist meist leer.
  ...entries(['C30'], ['C29'], 'Würdigung gegen eine Schwelle von 0 %', 'Ohne Signifikanzschwelle gibt es nichts zu würdigen.'),
  ...entries(['C23'], ['C21'], '0,00 € (leere Zelle zählt als 0)', HIGH_VALUE),
  ...entries(['C24', 'C26', 'C27', 'C28', 'C30'], ['C21'], 'Wert ohne den Fehler der umfassenden Schicht (EE_e = 0), wenn die Anpassung mit „Ja“ gewählt ist', HIGH_VALUE),
]
