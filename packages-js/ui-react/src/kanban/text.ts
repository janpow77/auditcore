import { kanbanDialogMessages, kanbanMessages, type Locale } from '@flowaudit/ui-core'
import { useTranslation } from '../i18n'

/** Texte der Kanban-Komponenten (dieselben Kataloge wie die Vue-Fassung). */
export const useKanbanText = (locale?: Locale) => useTranslation(kanbanMessages, locale)
export const useKanbanDialogText = (locale?: Locale) => useTranslation(kanbanDialogMessages, locale)
