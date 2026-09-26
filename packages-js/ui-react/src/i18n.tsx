import { createContext, useContext, useMemo, useSyncExternalStore, type ReactNode } from 'react'
import { getDefaultLocale, subscribeDefaultLocale, translator, type Catalogs, type Locale, type Translate } from '@flowaudit/ui-core'

const LocaleContext = createContext<Locale | null>(null)

/** Sprache für alle Komponenten im Teilbaum (Gegenstück zu `provideLocale` in Vue). */
export function LocaleProvider({ locale, children }: { locale: Locale; children?: ReactNode }) {
  return <LocaleContext.Provider value={locale}>{children}</LocaleContext.Provider>
}

/** Sprache: Prop vor Provider vor Standardsprache (`setDefaultLocale`). */
export function useLocale(override?: Locale): Locale {
  const provided = useContext(LocaleContext)
  const fallback = useSyncExternalStore(subscribeDefaultLocale, getDefaultLocale, getDefaultLocale)
  return override ?? provided ?? fallback
}

export interface UseTranslation<K extends string> {
  t: Translate<K>
  locale: Locale
}

/** Übersetzung mit den Katalogen aus `@flowaudit/ui-core` (gleiche Texte wie die Vue-Fassung). */
export function useTranslation<K extends string>(catalogs: Catalogs<K>, override?: Locale): UseTranslation<K> {
  const locale = useLocale(override)
  const t = useMemo(() => translator(catalogs, locale), [catalogs, locale])
  return { t, locale }
}
