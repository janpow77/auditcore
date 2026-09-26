import { computed, inject, provide, ref, type ComputedRef, type InjectionKey, type Ref } from 'vue'
import { getDefaultLocale, subscribeDefaultLocale, translate, type Catalogs, type Locale, type Translate } from '@auditcore/ui-core'

/** Sprachkern (Kataloge, Platzhalter, Rückfall) aus `@auditcore/ui-core`; hier nur die Vue-Anbindung. */
export {
  DEFAULT_LOCALE,
  LOCALES,
  defineMessages,
  interpolate,
  isLocale,
  setDefaultLocale,
  translate,
  type Catalogs,
  type Locale,
  type MessageParams,
  type Translate,
} from '@auditcore/ui-core'

export const LOCALE_KEY: InjectionKey<Ref<Locale>> = Symbol('flowaudit-locale')
const fallbackLocale = ref<Locale>(getDefaultLocale())
subscribeDefaultLocale(() => {
  fallbackLocale.value = getDefaultLocale()
})

/** Stellt die Sprache für alle Nachfahren bereit (App-Ebene oder Teilbaum). */
export function provideLocale(locale: Ref<Locale>): void {
  provide(LOCALE_KEY, locale)
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
