/**
 * English UI texts; missing keys fall back to German. Keys are stable English identifiers; the tables are split by
 * area to keep the files small.
 */

import { MESSAGES_EN_EDITOR } from './en.editor'
import { MESSAGES_EN_VIEWS } from './en.views'

export const MESSAGES_EN: Record<string, string> = { ...MESSAGES_EN_EDITOR, ...MESSAGES_EN_VIEWS }
