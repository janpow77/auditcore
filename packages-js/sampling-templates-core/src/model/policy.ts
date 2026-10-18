/**
 * Richtlinie für fehlende Angaben – die eine Stelle, an der sich für alle
 * Blätter umstellen lässt, was die Webfassung zeigt, wenn eine Eingabe fehlt
 * und die Vorlage trotzdem einen Wert zeigt.
 *
 * Die Blätter selbst kennen nur die Fallarten: Sie liefern für eine fehlende
 * Pflichteingabe keinen Wert und führen die Zelle als begründete Abweichung
 * (`deviations`), sie melden mit 0 gerechnete Eingaben (`zeroAssumed`), und sie
 * geben einen Prüfhinweis ohne Grundlage über `unfounded` zurück. Was daraus in
 * der Anzeige wird, entscheidet `evaluateSheet` anhand dieser Tabelle.
 */
import type { CellValue, MissingPolicy, SheetContext } from './types'

/**
 * Geltende Richtlinie (vorläufige Vorgabe des Auftraggebers):
 *
 * - `requiredInput` – eine Pflichteingabe fehlt, die Vorlage rechnet mit 0
 *   weiter: Die Webfassung zeigt „Angabe fehlt“ und nennt die Eingabe.
 * - `sampleDeviation` – die Standardabweichung der Stichprobe (s_r, s_q, s der
 *   Differenzen) fehlt in der Auswertung: wie die Vorlage mit 0 gerechnet und
 *   als „Keine Angabe, daher mit 0 berechnet.“ ausgewiesen (entschieden).
 * - `partialErrorSum` – die Fehlersumme einer von mehreren belegten Schichten
 *   fehlt, während eine andere Schicht eine trägt: wie die Vorlage mit 0
 *   gerechnet und ebenso ausgewiesen.
 * - `withoutBasis` – die Vorlage zeigt einen Wert ohne Grundlage: einen
 *   bestandenen Prüfhinweis („✔“), obwohl die geprüfte Größe fehlt, oder die
 *   Summe 0 über eine Schichtzeile, in der keine Schicht einen Wert trägt.
 *   Verbindliche Regel (Entscheidung nach der Gesamtabnahme): Sind alle
 *   Pflichteingaben vorhanden, zeigt die Webfassung IMMER, was die Vorlage zeigt
 *   – auch diesen Wert –, kennzeichnet ihn mit einem Hinweis in Warnfarbe und
 *   stellt eine bestandene Würdigung nicht uneingeschränkt grün dar; unterdrückt
 *   wird nichts. Offen (`'open'`) bleibt der Wert ausschließlich, solange eine
 *   Pflichteingabe FEHLT. Das gilt einheitlich für alle Blätter (`evaluateSheet`).
 *
 * Pflichteingaben sind die Eingaben, die ein Blatt in seinen begründeten
 * Abweichungen als Auslöser nennt. Daneben gibt es stille Lücken
 * (`model/dependence.ts`): leere, nicht freiwillige Eingaben, von denen ein
 * gezeigtes Ergebnis abhängt, ohne dass die Vorlage es zeigt. Die Webfassung
 * rechnet dort wie die Vorlage und weist die Eingabe in Warnfarbe aus.
 *
 * Freiwillige Eingaben (Entscheidung des Inhabers vom 17.10.2026): Was die
 * Vorlage als freiwillig kennzeichnet oder leer als 0 liest – systembedingte und
 * anomale Fehler, hochwertige Einheiten, Iteration, die Abzüge in Blatt 02 und
 * J6–J8 in Blatt 20 –, ist freiwillig; leer heißt „keine“ (0), ohne Hinweis
 * „Angabe fehlt“. Die Einstufung je Feld steht in `model/dependence.ts`.
 *
 * Zum Umstellen genügt es, hier einen Wert zu ändern; kein Blatt wird angefasst.
 */
export const MISSING_POLICY: MissingPolicy = {
  requiredInput: 'missing',
  sampleDeviation: 'zero',
  partialErrorSum: 'zero',
  withoutBasis: 'open',
}

/** Anzeige der Vorlage und Begründung für die Hochrechnung der Zufallsschicht ohne Fehlersumme (Abweichung `withoutBasis`). */
export const PROJECTION_WITHOUT_ERRORS = {
  template: '0,00 € (die Fehlersumme der Stichprobe fehlt; N(…) zählt sie als 0)',
  reason: 'Ohne Fehlersumme der Stichprobe gibt es nichts hochzurechnen; ein extrapolierter Fehler von 0 € sähe wie ein Prüfergebnis aus.',
  kind: 'withoutBasis',
} as const

/** Variante „wie die Vorlage“: jede fehlende Angabe mit 0 gerechnet und ausgewiesen, Prüfhinweise wie in der Vorlage. */
export const TEMPLATE_POLICY: MissingPolicy = {
  requiredInput: 'zero',
  sampleDeviation: 'zero',
  partialErrorSum: 'zero',
  withoutBasis: 'template',
}

/** Variante „streng“: jede fehlende Angabe lässt die abhängigen Werte offen. */
export const STRICT_POLICY: MissingPolicy = {
  requiredInput: 'missing',
  sampleDeviation: 'missing',
  partialErrorSum: 'missing',
  withoutBasis: 'open',
}

/** Richtlinie des Kontexts; ohne Angabe die geltende. */
export function policyOf(context: Pick<SheetContext, 'policy'> | undefined): MissingPolicy {
  return context?.policy ?? MISSING_POLICY
}

/**
 * Wert ohne Grundlage: `shown` ist, was die Vorlage zeigt, obwohl die geprüfte
 * bzw. summierte Größe fehlt (z. B. „✔ ≥ 3“ ohne Stichprobenumfang, weil sie
 * eine leere Textzelle im Vergleich größer als jede Zahl wertet; 0 als Summe
 * leerer Schichten). Die Zelle gehört zusätzlich mit `kind: 'withoutBasis'` in
 * die Abweichungen des Blatts, `whenEmpty` nennt die fehlende Größe.
 */
export function unfounded(context: Pick<SheetContext, 'policy'> | undefined, shown: CellValue): CellValue {
  return policyOf(context).withoutBasis === 'template' ? shown : null
}

/**
 * Hochrechnung der Zufallsschicht: Ist keine Fehlersumme eingetragen (`entered`),
 * rechnet die Vorlage mit `N(…)` = 0 und zeigt 0 € – ein Wert ohne Grundlage.
 */
export function projectionWithoutErrors(context: Pick<SheetContext, 'policy'> | undefined, entered: boolean, projected: CellValue): CellValue {
  return entered ? projected : unfounded(context, projected)
}
