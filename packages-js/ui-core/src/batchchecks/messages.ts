import { defineMessages } from '../i18n'

/** Texte von BatchChecks (Vue) und FlowauditBatchChecks (React); sichtbare Texte nur hier. */
export const batchchecksMessages = defineMessages({
  de: {
    title: 'BatchChecks',
    loading: 'Einträge werden geladen …',
    empty: 'Keine Einträge vorhanden.',
    failed: 'Anfrage abgelehnt: {message}',
  },
  en: {
    title: 'BatchChecks',
    loading: 'Loading entries …',
    empty: 'No entries.',
    failed: 'Request rejected: {message}',
  },
})

export type BatchchecksMessageKey = keyof typeof batchchecksMessages.de
