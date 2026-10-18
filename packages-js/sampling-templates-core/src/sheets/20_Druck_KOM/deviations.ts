/**
 * Begründete Abweichungen des Blatts 20 vom Verhalten der Vorlage. Die Webfassung
 * zeigt nie einen anderen Wert als die Vorlage, höchstens keinen.
 *
 * - Pflichteingaben anderer Blätter, die Blatt 20 unmittelbar liest (Anzahl der
 *   Datensätze und Betrag laut SFC2021 aus Blatt 02, Signifikanzschwelle aus
 *   Blatt 18): Die Vorlage rechnet mit der leeren Zelle als 0.
 * - Werte ohne Grundlage (`withoutBasis`): Blatt 02, Blatt 18 oder das Methodenblatt
 *   zeigen in der Webfassung „Angabe fehlt“, die Vorlage rechnet dort mit 0 weiter
 *   und der Bericht übernimmt das Ergebnis. Gegenprobe im Abgleich: Rechnet der
 *   ganze Arbeitsstand „wie die Vorlage“, zeigt die Zelle genau den Wert der Vorlage.
 */
import type { CellAddress, Deviation } from '../../model/types'

const UPSTREAM_TEMPLATE = 'Wert auf Grundlage der in Blatt 02, im Methodenblatt bzw. in Blatt 18 mit 0 gerechneten leeren Eingaben; ohne Zahl in Blatt 18 „nicht berechnet“'
const UPSTREAM_REASON = 'Das liefernde Blatt zeigt für die Größe „Angabe fehlt“; der Bericht übernimmt keinen Wert, der dort keine Grundlage hat.'

/** Zelle des Berichts → Zellen, deren fehlender Wert sie leert (bei F14 der Stichprobenumfang N10 des aktiven Verfahrens, der in keinem festen Blatt steht). */
const UPSTREAM: readonly (readonly [cell: CellAddress, whenEmpty: readonly string[]])[] = [
  ['F12', ['02_Grundgesamtheit!C52']],
  ['G12', ['02_Grundgesamtheit!C51']],
  ['F14', ['F14']],
  ['G32', ['18_GFQ_AnhIII!C26']],
  ['G33', ['18_GFQ_AnhIII!C24']],
  ['G34', ['18_GFQ_AnhIII!C25']],
  ['G35', ['18_GFQ_AnhIII!C28']],
  ['G36', ['18_GFQ_AnhIII!C27']],
  ['A37', ['18_GFQ_AnhIII!C26']],
  ['G42', ['18_GFQ_AnhIII!C26', '18_GFQ_AnhIII!C14']],
]

const required = (cell: CellAddress, whenEmpty: string, template: string, reason: string): Deviation => ({ cell, whenEmpty: [whenEmpty], template, reason })

export const deviations: readonly Deviation[] = [
  required('F11', '02_Grundgesamtheit!C23', '0 (leere Zelle zählt als 0)', 'Ohne Anzahl der Datensätze in Blatt 02 ist sie unbekannt, nicht 0.'),
  required('G11', '02_Grundgesamtheit!C16', '0,00 € (leere Zelle zählt als 0)', 'Ohne Betrag laut SFC2021 in Blatt 02 ist er unbekannt, nicht 0 €.'),
  required('A37', '18_GFQ_AnhIII!C29', 'Satz zur Würdigung gegen eine Schwelle von 0 %', 'Ohne Signifikanzschwelle in Blatt 18 gibt es nichts zu würdigen.'),
  ...UPSTREAM.map(([cell, whenEmpty]): Deviation => ({ cell, whenEmpty, template: UPSTREAM_TEMPLATE, reason: UPSTREAM_REASON, kind: 'withoutBasis' })),
  {
    cell: 'G43',
    whenEmpty: ['G42'],
    template: 'Betrag der Korrektur, obwohl die Restfehlerquote fehlt (Excel wertet die leere Textzelle im Vergleich größer als 0,02)',
    reason: 'Ohne Restfehlerquote steht nicht fest, ob eine Korrektur erforderlich ist; ein Betrag hätte keine Grundlage.',
    kind: 'withoutBasis',
  },
]
