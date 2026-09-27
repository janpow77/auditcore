import { defineMessages } from '../i18n'

/** Texte von RunnerConsole (Vue) und FlowauditRunnerConsole (React); sichtbare Texte nur hier. */
export const runnerMessages = defineMessages({
  de: {
    title: 'RunnerConsole',
    loading: 'Einträge werden geladen …',
    empty: 'Keine Einträge vorhanden.',
    failed: 'Anfrage abgelehnt: {message}',
  },
  en: {
    title: 'RunnerConsole',
    loading: 'Loading entries …',
    empty: 'No entries.',
    failed: 'Request rejected: {message}',
  },
})

export type RunnerMessageKey = keyof typeof runnerMessages.de
