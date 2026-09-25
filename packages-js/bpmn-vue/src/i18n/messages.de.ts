/**
 * German UI texts (default language). Keys are stable English identifiers; the tables are split by
 * area to keep the files small.
 */

import { MESSAGES_DE_EDITOR } from './de.editor'
import { MESSAGES_DE_VIEWS } from './de.views'

export const MESSAGES_DE: Record<string, string> = { ...MESSAGES_DE_EDITOR, ...MESSAGES_DE_VIEWS }
