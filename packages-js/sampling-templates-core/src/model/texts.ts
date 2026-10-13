/**
 * Texte eines Blatts je Sprache. Deutsch ist der Wortlaut der Vorlage und
 * steht in der Methodendefinition und im Rechenkern. Weitere Sprachen sind
 * Arbeitsübersetzungen: Sie liegen je Blatt in `texts.<sprache>.ts`, ersetzen
 * nur die Anzeige und ändern weder Zellschlüssel noch gespeicherte Werte.
 * Fehlt ein Text, bleibt der deutsche stehen.
 */
import type { MethodDefinition, SummaryDefinition } from './definition'
import type { CellAddress } from './types'

/** Sprachen neben Deutsch. */
export type TranslationLocale = 'en'

/** Übersetzte Texte eines Felds. */
export interface FieldTexts {
  label?: string
  hint?: string
  formula?: string
  interpretation?: string
}

/** Übersetzung eines Blatts; Schlüssel sind Abschnittsbuchstaben, Zelladressen und deutsche Wortlaute. */
export interface SheetTexts {
  title?: string
  shortTitle?: string
  legalBasis?: string
  /** Abschnitte nach Kennbuchstabe. */
  sections?: Readonly<Record<string, { title?: string; reference?: string }>>
  /** Felder nach Zelle (bei Schichtzeilen die Zelle der ersten Schicht). */
  fields?: Readonly<Record<CellAddress, FieldTexts>>
  /** Ergebnisspalte: Hauptgröße und Zeilen nach Zelle. */
  summary?: { primary?: string; unit?: string; rows?: Readonly<Record<CellAddress, string>> }
  /**
   * Texte, die der Rechenkern liefert (Prüfhinweise, „TE ≤ AE“, Methodenname) und
   * Einträge eigener Auswahllisten: deutscher Wortlaut → Übersetzung.
   */
  values?: Readonly<Record<string, string>>
  /** Hinweise der Webfassung nach Kennung. */
  webHints?: Readonly<Record<string, string>>
}

export type SheetTranslations = Readonly<Partial<Record<TranslationLocale, SheetTexts>>>

/** Methodendefinition mit übersetzten Texten; Zellen, Arten und Formate bleiben unverändert. */
export function localizeDefinition(definition: MethodDefinition, texts: SheetTexts | undefined): MethodDefinition {
  if (!texts) return definition
  return {
    ...definition,
    title: texts.title ?? definition.title,
    shortTitle: texts.shortTitle ?? definition.shortTitle,
    legalBasis: texts.legalBasis ?? definition.legalBasis,
    sections: definition.sections.map((section) => ({
      ...section,
      ...texts.sections?.[section.id],
      fields: section.fields.map((field) => ({ ...field, ...texts.fields?.[field.cell] })),
    })),
    summary: localizeSummary(definition.summary, texts.summary),
  }
}

function localizeSummary(summary: SummaryDefinition, texts: SheetTexts['summary']): SummaryDefinition {
  if (!texts) return summary
  const rows = texts.rows ?? {}
  return {
    ...summary,
    primary: { ...summary.primary, label: texts.primary ?? summary.primary.label, unit: texts.unit ?? summary.primary.unit },
    rows: summary.rows.map((row) => ({ ...row, label: rows[row.cell] ?? row.label })),
  }
}

/** Anzeige eines Texts aus dem Rechenkern oder eines Listeneintrags in der Sprache der Oberfläche. */
export function translateValue(texts: SheetTexts | undefined, value: string): string {
  return texts?.values?.[value] ?? value
}
