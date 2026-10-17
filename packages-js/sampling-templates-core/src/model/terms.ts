/**
 * Amtliche Begriffe statt der Begriffe der Vorlage (Entscheidung des Inhabers
 * vom 17.10.2026, DelVO-Abgleich Abschnitt 7). Die Vorlage sagt
 * „Wesentlichkeitsschwelle“; amtlich ist „Signifikanzschwelle“ (Anhang I Nr. 1
 * DelVO (EU) 2023/67, Anhang XX Nr. 5.9 VO (EU) 2021/1060). Die Webfassung
 * verwendet den amtlichen Begriff in Bezeichnungen, Texten, Hinweisen, Bericht
 * und Export; beim ersten Vorkommen je Blatt steht der Begriff der Vorlage in
 * Klammern. Beim Lesen einer Arbeitsmappe gelten beide Begriffe als gleich.
 * Englisch bleibt „materiality threshold“ wie in der englischen DelVO.
 */
import type { MethodDefinition } from './definition'
import type { CellValue } from './types'

/** Amtlicher Begriff (DelVO, deutsche Fassung). */
export const OFFICIAL_THRESHOLD_TERM = 'Signifikanzschwelle'

/** Begriff der Vorlage. */
export const TEMPLATE_THRESHOLD_TERM = 'Wesentlichkeitsschwelle'

/** Erstes Vorkommen je Blatt: amtlicher Begriff mit dem Begriff der Vorlage in Klammern. */
export const THRESHOLD_TERM_FIRST = `${OFFICIAL_THRESHOLD_TERM} (Vorlage: ${TEMPLATE_THRESHOLD_TERM})`

/** Text mit dem amtlichen Begriff statt des Begriffs der Vorlage; andere Werte bleiben. */
export function officialWording<T extends CellValue | boolean>(value: T): T {
  return (typeof value === 'string' ? value.replaceAll(TEMPLATE_THRESHOLD_TERM, OFFICIAL_THRESHOLD_TERM) : value) as T
}

/**
 * Definition mit dem Begriff der Vorlage in Klammern an der ersten Bezeichnung
 * des Blatts, die den amtlichen Begriff trägt (Reihenfolge der Abschnitte und Felder).
 */
export function withTemplateTerm(definition: MethodDefinition): MethodDefinition {
  let done = false
  const sections = definition.sections.map((section) => ({
    ...section,
    fields: section.fields.map((field) => {
      if (done || !field.label.includes(OFFICIAL_THRESHOLD_TERM)) return field
      done = true
      return { ...field, label: field.label.replace(OFFICIAL_THRESHOLD_TERM, THRESHOLD_TERM_FIRST) }
    }),
  }))
  return done ? { ...definition, sections } : definition
}
