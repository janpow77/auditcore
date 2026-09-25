import { computed, inject, provide, ref, type ComputedRef, type InjectionKey, type Ref } from 'vue'

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

export function isLocale(value: unknown): value is Locale {
  return typeof value === 'string' && (LOCALES as readonly string[]).includes(value)
}

export const LOCALE_KEY: InjectionKey<Ref<Locale>> = Symbol('flowaudit-locale')
const fallbackLocale = ref<Locale>(DEFAULT_LOCALE)

/** Stellt die Sprache für alle Nachfahren bereit (App-Ebene oder Teilbaum). */
export function provideLocale(locale: Ref<Locale>): void {
  provide(LOCALE_KEY, locale)
}

/** Sprache ohne Provider, z. B. für Web Components ohne umgebende Vue-App. */
export function setDefaultLocale(locale: Locale): void {
  fallbackLocale.value = locale
}

export function useLocale(): Ref<Locale> {
  return inject(LOCALE_KEY, fallbackLocale)
}

export interface UseI18n<K extends string> {
  locale: ComputedRef<Locale>
  t: Translate<K>
}

/**
 * Composable für Komponenten. `override` (z. B. eine Prop `locale`) hat Vorrang
 * vor der bereitgestellten Sprache.
 */
export function useI18n<K extends string>(
  catalogs: Catalogs<K>,
  override?: () => Locale | undefined,
): UseI18n<K> {
  const provided = useLocale()
  const locale = computed<Locale>(() => override?.() ?? provided.value)
  const t: Translate<K> = (key, params) => translate(catalogs, locale.value, key, params)
  return { locale, t }
}
