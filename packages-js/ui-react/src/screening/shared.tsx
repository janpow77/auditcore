import type { ReactNode } from 'react'
import { screeningMessages, type BadgeTone, type ScreeningKey, type ScreeningTranslate } from '@flowaudit/ui-core'
import { useTranslation } from '../i18n'

/** Übersetzung der Screening-Texte in der Sprache des umgebenden `LocaleProvider` (wie `provideLocale` in Vue). */
export function useScreeningText(): { t: ScreeningTranslate; locale: 'de' | 'en' } {
  return useTranslation(screeningMessages)
}

/** Katalogschlüssel aus Präfix und Vertragscode (`status_open`, `kind_pep` …) wie die Vue-Vorlage. */
export function codeKey(prefix: string, code: string): ScreeningKey {
  return `${prefix}_${code}` as ScreeningKey
}

/** Badge mit optionalem Tooltip (in Vue als durchgereichtes Attribut `title` an `FaBadge`). */
export function TitledBadge({ tone = 'neutral', title, children }: { tone?: BadgeTone; title?: string; children?: ReactNode }) {
  return <span className={`fa-badge fa-badge--${tone}`} title={title}>{children}</span>
}

/** Fehlerliste der Formulare (role="alert"). */
export function ErrorList({ texts }: { texts: readonly string[] }) {
  if (!texts.length) return null
  return (
    <ul className="fa-screening__errors" role="alert">
      {texts.map((text) => <li key={text}>{text}</li>)}
    </ul>
  )
}
