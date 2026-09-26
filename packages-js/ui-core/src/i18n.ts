/**
 * Framework-freier Kern der Sprachunterstützung: Kataloge, Platzhalter,
 * Rückfall auf Deutsch. Vue (`useI18n` in `@flowaudit/ui`) und React
 * (`useTranslation` in `@flowaudit/ui-react`) setzen darauf auf.
 */
export type Locale = 'de' | 'en'
export const LOCALES: readonly Locale[] = ['de', 'en']
export const DEFAULT_LOCALE: Locale = 'de'

export type MessageParams = Readonly<Record<string, string | number>>

/** Kataloge je Sprache; Deutsch ist vollständig, Englisch darf (noch) lückenhaft sein. */
export interface Catalogs<K extends string> {
  de: Readonly<Record<K, string>>
  en: Readonly<Partial<Record<K, string>>>
}

export type Translate<K extends string> = (key: K, params?: MessageParams) => string

/** Typisiert Kataloge einer Komponente; die Schlüssel ergeben sich aus dem deutschen Katalog. */
export function defineMessages<K extends string>(catalogs: Catalogs<K>): Catalogs<K> {
  return catalogs
}

/** Ersetzt {name}-Platzhalter; unbekannte Platzhalter bleiben sichtbar stehen. */
export function interpolate(template: string, params?: MessageParams): string {
  if (!params) return template
  return template.replace(/\{(\w+)\}/g, (match, name: string) => {
    const value = params[name]
    return value === undefined ? match : String(value)
  })
}

/** Übersetzt mit Rückfall auf Deutsch und zuletzt auf den Schlüssel. */
export function translate<K extends string>(
  catalogs: Catalogs<K>,
  locale: Locale,
  key: K,
  params?: MessageParams,
): string {
  const template = (locale === 'en' ? catalogs.en[key] : undefined) ?? catalogs.de[key] ?? key
  return interpolate(template, params)
}

/** Übersetzungsfunktion für eine feste Sprache. */
export function translator<K extends string>(catalogs: Catalogs<K>, locale: Locale): Translate<K> {
  return (key, params) => translate(catalogs, locale, key, params)
}

export function isLocale(value: unknown): value is Locale {
  return typeof value === 'string' && (LOCALES as readonly string[]).includes(value)
}

let defaultLocale: Locale = DEFAULT_LOCALE
const listeners = new Set<() => void>()

/** Sprache ohne Provider (Web Components, React ohne `LocaleProvider`). */
export function setDefaultLocale(locale: Locale): void {
  if (locale === defaultLocale) return
  defaultLocale = locale
  for (const listener of listeners) listener()
}

export function getDefaultLocale(): Locale {
  return defaultLocale
}

/** Meldet Änderungen der Standardsprache; liefert die Abmeldung. */
export function subscribeDefaultLocale(listener: () => void): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}
