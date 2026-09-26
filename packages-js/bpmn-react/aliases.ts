/**
 * Source aliases for tests and the build: sibling packages are used from
 * source (no build order); only the core stylesheet is bundled into the
 * library CSS, all other @flowaudit imports stay external.
 */

import { resolve } from 'node:path'

const here = new URL('.', import.meta.url).pathname
const flowaudit = resolve(here, '../bpmn-flowaudit/src')

export const styleAlias = { '@flowaudit/bpmn-flowaudit/ui.css': `${flowaudit}/ui/ui.css` }

export function sourceAliases(): Record<string, string> {
  return {
    '@flowaudit/bpmn-flowaudit/profiles': `${flowaudit}/profile/bundled.ts`,
    ...styleAlias,
    '@flowaudit/bpmn-flowaudit/ui': `${flowaudit}/ui/index.ts`,
    '@flowaudit/bpmn-flowaudit': `${flowaudit}/index.ts`,
    '@flowaudit/bpmn-editor': resolve(here, '../bpmn-editor/src/index.ts'),
    '@flowaudit/bpmn-vue': resolve(here, '../bpmn-vue/src/index.ts'),
    '@flowaudit/ui-core': resolve(here, '../ui-core/src/index.ts'),
    '@flowaudit/common/browser': resolve(here, '../common/src/browser.ts'),
    '@flowaudit/common': resolve(here, '../common/src/index.ts'),
  }
}

export const isExternal = (id: string): boolean => /^(react|react-dom)($|\/)/.test(id) || /^(diagram-js|bpmn-moddle)($|\/)/.test(id) || (/^@flowaudit\//.test(id) && !id.endsWith('.css'))
