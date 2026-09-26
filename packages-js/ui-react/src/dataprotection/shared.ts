import { intlFormatDate } from '@auditcore/common'
import { dataprotectionMessages, type DataProtectionTranslate, type Locale } from '@auditcore/ui-core'
import { useTranslation } from '../i18n'

export {
  dataprotectionStatusLabel as statusLabel,
  dataprotectionLabel as prefixedLabel,
} from '@auditcore/ui-core'

export interface DataProtectionText {
  t: DataProtectionTranslate
  locale: Locale
  /** Datum (mit Uhrzeit, wenn `withTime`) wie `formatDate` der Vue-Fassung; leer bei fehlendem Wert. */
  when: (value: string | null | undefined, withTime?: boolean) => string
}

/** Texte von VVT und DSFA in der Sprache des umgebenden `LocaleProvider`. */
export function useDataProtectionText(): DataProtectionText {
  const { t, locale } = useTranslation(dataprotectionMessages)
  return { t, locale, when: (value, withTime = true) => intlFormatDate(value ?? null, locale, withTime) }
}
