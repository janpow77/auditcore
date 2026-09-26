/**
 * Source aliases for tests and the build: sibling packages are used from
 * source (no build order); only the core stylesheet is bundled into the
 * library CSS, all other @auditcore imports stay external.
 */

import { resolve } from 'node:path'

const here = new URL('.', import.meta.url).pathname
const flowaudit = resolve(here, '../bpmn-flowaudit/src')

export const styleAlias = { '@auditcore/bpmn-flowaudit/ui.css': `${flowaudit}/ui/ui.css` }

export function sourceAliases(): Record<string, string> {
  return {
    '@auditcore/bpmn-flowaudit/profiles': `${flowaudit}/profile/bundled.ts`,
    ...styleAlias,
    '@auditcore/bpmn-flowaudit/ui': `${flowaudit}/ui/index.ts`,
    '@auditcore/bpmn-flowaudit': `${flowaudit}/index.ts`,
    '@auditcore/bpmn-editor': resolve(here, '../bpmn-editor/src/index.ts'),
    '@auditcore/bpmn-vue': resolve(here, '../bpmn-vue/src/index.ts'),
    '@auditcore/ui-core': resolve(here, '../ui-core/src/index.ts'),
    '@auditcore/kanban-core': resolve(here, '../kanban-core/src/index.ts'),
    '@auditcore/common/browser': resolve(here, '../common/src/browser.ts'),
    '@auditcore/common': resolve(here, '../common/src/index.ts'),
  }
}

export const isExternal = (id: string): boolean => /^(react|react-dom)($|\/)/.test(id) || /^(diagram-js|bpmn-moddle)($|\/)/.test(id) || (/^@auditcore\//.test(id) && !id.endsWith('.css'))
