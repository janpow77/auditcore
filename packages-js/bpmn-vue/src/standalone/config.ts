/**
 * Configuration of the standalone app, in this order: `window.FLOWAUDIT_CONFIG`
 * (set by the hosting server), `<meta name="flowaudit-…">` tags, query
 * parameters (`?api=…&locale=en&profile=…`). Default API base: `./api`.
 */

import type { Locale } from '../i18n/useI18n'

export interface StandaloneConfig {
  apiBase: string
  locale: Locale
  profile?: string
  author?: string
  title?: string
}

type Source = Partial<Record<keyof StandaloneConfig, string>>

const KEYS: (keyof StandaloneConfig)[] = ['apiBase', 'locale', 'profile', 'author', 'title']
const QUERY: Record<keyof StandaloneConfig, string> = { apiBase: 'api', locale: 'locale', profile: 'profile', author: 'author', title: 'title' }
const META: Record<keyof StandaloneConfig, string> = { apiBase: 'flowaudit-api-base', locale: 'flowaudit-locale', profile: 'flowaudit-profile', author: 'flowaudit-author', title: 'flowaudit-title' }

function fromMeta(doc: Document): Source {
  return Object.fromEntries(KEYS.map((key) => [key, doc.querySelector<HTMLMetaElement>(`meta[name="${META[key]}"]`)?.content]).filter(([, value]) => value))
}

function fromQuery(search: string): Source {
  const params = new URLSearchParams(search)
  return Object.fromEntries(KEYS.map((key) => [key, params.get(QUERY[key])]).filter(([, value]) => value))
}

export function readConfig(win: Window & { FLOWAUDIT_CONFIG?: Source } = window): StandaloneConfig {
  const merged: Source = { ...fromMeta(win.document), ...(win.FLOWAUDIT_CONFIG ?? {}), ...fromQuery(win.location.search) }
  return {
    apiBase: merged.apiBase || './api',
    locale: merged.locale === 'en' ? 'en' : 'de',
    profile: merged.profile,
    author: merged.author,
    title: merged.title,
  }
}
