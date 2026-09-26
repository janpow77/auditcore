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
    '@auditcore/bpmn-flowaudit/profiles': `${flowaudit}/profile/bundled.ts`,
    '@auditcore/bpmn-flowaudit/ui.css': `${flowaudit}/ui/ui.css`,
    '@auditcore/bpmn-flowaudit/ui': `${flowaudit}/ui/index.ts`,
    '@auditcore/bpmn-flowaudit': `${flowaudit}/index.ts`,
    '@auditcore/bpmn-editor': resolve(here, '../bpmn-editor/src/index.ts'),
    '@auditcore/ui-core': resolve(here, '../ui-core/src/index.ts'),
    '@auditcore/kanban-core': resolve(here, '../kanban-core/src/index.ts'),
    '@auditcore/common/browser': resolve(here, '../common/src/browser.ts'),
    '@auditcore/common': resolve(here, '../common/src/index.ts'),
  }
}

/** Only the UI stylesheet of the core is bundled into the library CSS (all other @auditcore imports stay external). */
export const styleAlias = { '@auditcore/bpmn-flowaudit/ui.css': resolve(here, '../bpmn-flowaudit/src/ui/ui.css') }
export const isExternal = (id: string): boolean => /^(vue|diagram-js|bpmn-moddle)($|\/)/.test(id) || (/^@auditcore\//.test(id) && !id.endsWith('.css'))
