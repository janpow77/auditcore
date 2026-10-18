/**
 * Auslegungen der Vorlage, die die Vorlage selbst nicht kennzeichnet
 * (DelVO-Abgleich vom 17.10.2026, Abschnitt 6). Die Webfassung kennzeichnet sie
 * wie die übrigen Auslegungen am Feld (`interpretation`): „Auslegung der
 * Vorlage – …“ in neutraler Farbe, sobald das Feld einen Wert hat. Kein
 * Rechenwert ändert sich.
 */

/** Aufrunden aller Stichprobenumfänge. */
export const ROUNDING_INTERPRETATION =
  'Die DelVO legt nicht fest, wie ein rechnerischer Stichprobenumfang zu runden ist; die Vorlage rundet jeden Umfang auf die nächste ganze Zahl auf (zwingend für ganze Einheiten und vorsichtig).'
export const ROUNDING_INTERPRETATION_EN =
  'The Delegated Regulation does not lay down how a computed sample size is to be rounded; the template rounds every sample size up to the next whole number (necessary for whole units, and prudent).'

/** Vergleich der oberen Fehlergrenze mit der Schwelle in der Würdigung. */
export const UPPER_LIMIT_INTERPRETATION =
  'Anhang I Nr. 1 DelVO und Anhang XX Nr. 5.9 VO (EU) 2021/1060 vergleichen die Gesamtfehlerquote mit der Signifikanzschwelle; den zusätzlichen Vergleich der oberen Fehlergrenze („⚠“) legt die Vorlage aus der Prüfpraxis fest.'
export const UPPER_LIMIT_INTERPRETATION_EN =
  'Annex I point 1 to the Delegated Regulation and Annex XX point 5.9 to Regulation (EU) 2021/1060 compare the total error rate with the materiality threshold; the additional comparison of the upper error limit (“⚠”) is laid down by the template from audit practice.'

/** MUS-Standardansatz: n schließt die hochwertigen Einheiten ein. */
export const HIGH_VALUE_INTERPRETATION =
  'Dass der Stichprobenumfang die hochwertigen Einheiten einschließt und die Zufallsschicht den Rest erhält (n_s = n − n_e), legt die Vorlage fest (wie EGESIF_16-0014-01); Art. 5 Abs. 2 DelVO regelt das nicht ausdrücklich.'
export const HIGH_VALUE_INTERPRETATION_EN =
  'That the sample size includes the high value units and the random stratum receives the rest (n_s = n − n_e) is laid down by the template (as in EGESIF_16-0014-01); Art. 5(2) of the Delegated Regulation does not expressly regulate this.'

/** Einfache Zufallsstichprobe: Anrechnung der umfassenden Schicht auf den Mindestumfang 30. */
export const EXHAUSTIVE_MINIMUM_INTERPRETATION =
  'Art. 5 Abs. 5 DelVO verlangt mindestens 30 Einheiten; dass die Einheiten der umfassenden Schicht darauf angerechnet werden (Zufallsschicht mindestens 30 − N_e, wenigstens 3), legt die Vorlage fest.'
export const EXHAUSTIVE_MINIMUM_INTERPRETATION_EN =
  'Art. 5(5) of the Delegated Regulation requires at least 30 units; that the units of the exhaustive stratum count towards them (random stratum at least 30 − N_e, at least 3) is laid down by the template.'

/** Blatt 11: Aufteilung von Zeitraum 2 auf die Schichten. */
export const PERIOD2_ALLOCATION_INTERPRETATION =
  'Für die Aufteilung des Umfangs von Zeitraum 2 auf die Schichten nennt Anhang II Nr. 2.2 DelVO keine Formel; die Vorlage teilt sinngemäß nach Nr. 1.2 im Verhältnis N_h2 / N_2 auf.'
export const PERIOD2_ALLOCATION_INTERPRETATION_EN =
  'Annex II point 2.2 to the Delegated Regulation gives no formula for allocating the sample size of period 2 to the strata; the template allocates by analogy with point 1.2 in proportion N_h2 / N_2.'

/** Blätter 14 und 16: proportionale Aufteilung beim nichtstatistischen Verfahren. */
export const NONSTATISTICAL_ALLOCATION_INTERPRETATION =
  'Art. 6 Abs. 1 UAbs. 2 DelVO verlangt nur, dass die Stichprobe Einheiten aus jeder Schicht enthält; die proportionale Aufteilung (mindestens 1 je Schicht) legt die Vorlage fest.'
export const NONSTATISTICAL_ALLOCATION_INTERPRETATION_EN =
  'Art. 6(1), second subparagraph, of the Delegated Regulation only requires the sample to contain units from each stratum; the proportional allocation (at least 1 per stratum) is laid down by the template.'

/** Blatt 15: Prüfhinweis „mindestens 3 Einheiten“ beim nichtstatistischen PPS-Verfahren. */
export const NONSTATISTICAL_THREE_INTERPRETATION =
  'Art. 5 Abs. 5 DelVO (mindestens drei Einheiten je Zufallsschicht) betrifft das statistische Stichprobenverfahren; Art. 6 verweist für die Auswahl nur auf den Ansatz nach Art. 5 Abs. 2. Die Vorlage prüft trotzdem auf mindestens 3 Einheiten (strenger als die DelVO).'
export const NONSTATISTICAL_THREE_INTERPRETATION_EN =
  'Art. 5(5) of the Delegated Regulation (at least three units per random stratum) concerns statistical sampling; Art. 6 refers for the selection only to the approach under Art. 5(2). The template nevertheless checks for at least 3 units (stricter than the Delegated Regulation).'

/**
 * Allgemeine Auslegungen: Sie beschreiben eine Rechenregel des Verfahrens, nicht
 * eine Einschränkung des einzelnen Ergebnisses. Sie stehen am Blatt selbst und
 * reisen nicht in Blatt 18, den Bericht und den Export mit (deutsch und englisch).
 */
export const GENERAL_INTERPRETATIONS: ReadonlySet<string> = new Set([
  ROUNDING_INTERPRETATION,
  ROUNDING_INTERPRETATION_EN,
  UPPER_LIMIT_INTERPRETATION,
  UPPER_LIMIT_INTERPRETATION_EN,
  HIGH_VALUE_INTERPRETATION,
  HIGH_VALUE_INTERPRETATION_EN,
  EXHAUSTIVE_MINIMUM_INTERPRETATION,
  EXHAUSTIVE_MINIMUM_INTERPRETATION_EN,
  NONSTATISTICAL_ALLOCATION_INTERPRETATION,
  NONSTATISTICAL_ALLOCATION_INTERPRETATION_EN,
  NONSTATISTICAL_THREE_INTERPRETATION,
  NONSTATISTICAL_THREE_INTERPRETATION_EN,
])
