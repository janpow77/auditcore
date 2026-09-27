import type { ReporttemplatesData } from './controller'
import type { TemplateDetail, TemplateFormat, TemplateSchema } from './types'

/** Zeile der Datenvertrags-Übersicht (oberste Ebene des Schemas). */
export interface SchemaFieldRow {
  name: string
  title: string
  type: string
  required: boolean
}

export interface TextBlockRow {
  id: string
  title: string
  required: boolean
  conditional: boolean
  legalBasis: string
}

export interface FormatOption {
  format: TemplateFormat
  available: boolean
}

function typeText(schema: TemplateSchema): string {
  const kind = Array.isArray(schema.type) ? schema.type.join(' | ') : (schema.type ?? '–')
  if (kind === 'array' && schema.items) return `Liste von ${typeText(schema.items)}`
  return schema.format ? `${kind} (${schema.format})` : String(kind)
}

export function schemaFields(detail: TemplateDetail | null): SchemaFieldRow[] {
  const properties = detail?.schema.properties ?? {}
  const required = new Set(detail?.schema.required ?? [])
  return Object.entries(properties).map(([name, schema]) => ({
    name, title: schema.title ?? '', type: typeText(schema), required: required.has(name),
  }))
}

export function textBlockRows(detail: TemplateDetail | null): TextBlockRow[] {
  return (detail?.text_blocks ?? []).map((block) => ({
    id: block.id,
    title: block.title || block.id,
    required: block.required,
    conditional: block.condition !== null && block.condition !== undefined,
    legalBasis: block.legal_basis,
  }))
}

export function formatOptions(state: ReporttemplatesData): FormatOption[] {
  return (state.detail?.formats ?? []).map((format) => ({ format, available: state.catalogue?.formats[format] !== false }))
}

/** Bericht erzeugen ist möglich: Vorlage geladen, Format gewählt und auf dem Server verfügbar. */
export function reporttemplatesCanRender(state: ReporttemplatesData): boolean {
  const option = formatOptions(state).find((entry) => entry.format === state.format)
  return state.detail !== null && option?.available === true && state.busy === null
}

/** Hinweis „keine Vorlagen“ nur nach abgeschlossener, fehlerfreier Anfrage. */
export function reporttemplatesIsEmpty(state: ReporttemplatesData): boolean {
  return state.catalogue !== null && state.catalogue.templates.length === 0
}
