/** Begründete Abweichungen des Blatts 17: ohne Buchwert der Stichprobeneinheit bzw. ohne Umfang der Unterstichprobe (Variante 2) zeigt die Webfassung „Angabe fehlt“. */
import type { Deviation } from '../../model/types'

const REASON = 'Ohne Buchwert der Stichprobeneinheit lässt sich nichts hochrechnen; die Vorlage rechnet mit 0 € weiter.'

const SIZE = 'Ohne Umfang der Unterstichprobe gibt es kein Auswahlintervall; mit 0 abzüglich der hochwertigen Einheiten entstünden ein negatives Intervall und ein negativer Fehler.'

export const deviations: readonly Deviation[] = [
  ...['C13', 'C16', 'C20', 'C22'].map((cell) => ({ cell, whenEmpty: ['C6'], template: 'Wert auf Grundlage eines Buchwerts von 0 €', reason: REASON })),
  ...['C20', 'C22', 'C23'].map((cell) => ({ cell, whenEmpty: ['C15'], template: 'Wert auf Grundlage eines Umfangs von 0 (bei vorhandenen hochwertigen Einheiten negativ)', reason: SIZE })),
]
