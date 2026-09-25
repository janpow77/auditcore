import { translate } from '../../src/i18n/i18n'
import { synopsisMessages } from '../../src/synopsis/messages'
import type { Comparison } from '../../src/synopsis/types'
import type { SynopsisTranslate } from '../../src/synopsis/viewModel'
import articleJson from '../../demo/pages/synopsis/article.json'
import checklistJson from '../../demo/pages/synopsis/checklist.json'
import standardJson from '../../demo/pages/synopsis/standard.json'

/** Echte Ergebnisse von auditcore_documents.web (Demo-Daten, siehe demo/pages/synopsis). */
export const standard = standardJson as unknown as Comparison
export const checklist = checklistJson as unknown as Comparison
export const article = articleJson as unknown as Comparison
export const t: SynopsisTranslate = (key, params) => translate(synopsisMessages, 'de', key, params)
