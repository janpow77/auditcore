/** Sprachen der FlowAudit-Oberflächen (gleich `Locale` in `@auditcore/ui`). */
export type AppLocale = 'de' | 'en'

/** Alle unterstützten Sprachen. */
export const APP_LOCALES: readonly AppLocale[] = ['de', 'en']

const TAGS: Readonly<Record<AppLocale, string>> = { de: 'de-DE', en: 'en-GB' }

/** BCP-47-Tag für `Intl`: `de` → `de-DE`, `en` → `en-GB`. */
export function localeTag(locale: AppLocale): string {
  return TAGS[locale]
}

/** Zeitzone aller Anzeigeformatierer, unabhängig von der Rechnerzeit (Festlegung `display_timezone`). */
export const DISPLAY_TIME_ZONE = 'Europe/Berlin'

/** Ersatzwert jedes Anzeigeformatierers für fehlende oder ungültige Werte (Festlegung `empty_value`). */
export const EMPTY_VALUE = '—'

/** Gemeinsame Optionen der Anzeigeformatierer. */
export interface DisplayOptions {
  /** Sprache der Ausgabe (Standard `de`). */
  locale?: AppLocale
  /** Ersatzwert für leer/ungültig (Standard `EMPTY_VALUE`). */
  empty?: string
}

/** `null`, `undefined`, leere Zeichenkette oder `NaN` – Werte, für die Formatierer den Ersatzwert zeigen. */
export function isEmptyValue(value: unknown): value is null | undefined | '' {
  return value === null || value === undefined || value === '' || (typeof value === 'number' && Number.isNaN(value))
}

/** Zahl aus `number` oder Dezimal-String (`"1234.5"`, Backend-Decimal); sonst `null`. */
export function toFiniteNumber(value: unknown): number | null {
  if (typeof value === 'number') return Number.isFinite(value) ? value : null
  if (typeof value === 'bigint') return Number(value)
  if (typeof value !== 'string' || !/^\s*[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?\s*$/.test(value)) return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}
