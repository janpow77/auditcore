/**
 * Source aliases for development, tests and the bundled outputs: the
 * sibling packages (core editor, FlowAudit layer and its UI core) are used
 * from source, so no build order is needed. More specific entries first.
 */

import { resolve } from 'node:path'

const here = new URL('.', import.meta.url).pathname

export function sourceAliases(): Record<string, string> {
  const flowaudit = resolve(here, '../bpmn-flowaudit/src')
  return {
    '@flowaudit/bpmn-flowaudit/profiles': `${flowaudit}/profile/bundled.ts`,
    '@flowaudit/bpmn-flowaudit/ui.css': `${flowaudit}/ui/ui.css`,
    '@flowaudit/bpmn-flowaudit/ui': `${flowaudit}/ui/index.ts`,
    '@flowaudit/bpmn-flowaudit': `${flowaudit}/index.ts`,
    '@flowaudit/bpmn-editor': resolve(here, '../bpmn-editor/src/index.ts'),
  }
}

/** Only the UI stylesheet of the core is bundled into the library CSS (all other @flowaudit imports stay external). */
export const styleAlias = { '@flowaudit/bpmn-flowaudit/ui.css': resolve(here, '../bpmn-flowaudit/src/ui/ui.css') }
export const isExternal = (id: string): boolean => /^(vue|diagram-js|bpmn-moddle)($|\/)/.test(id) || (/^@flowaudit\//.test(id) && !id.endsWith('.css'))
