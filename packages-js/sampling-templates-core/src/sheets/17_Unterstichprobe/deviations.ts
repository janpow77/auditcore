/** Begründete Abweichungen des Blatts 17: ohne Buchwert der Stichprobeneinheit zeigt die Webfassung „Angabe fehlt“. */
import type { Deviation } from '../../model/types'

const REASON = 'Ohne Buchwert der Stichprobeneinheit lässt sich nichts hochrechnen; die Vorlage rechnet mit 0 € weiter.'

export const deviations: readonly Deviation[] = ['C13', 'C16', 'C20', 'C22'].map((cell) => ({ cell, whenEmpty: ['C6'], template: 'Wert auf Grundlage eines Buchwerts von 0 €', reason: REASON }))
