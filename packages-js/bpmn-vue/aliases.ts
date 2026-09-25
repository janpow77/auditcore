/**
 * Source aliases for development, tests and the bundled outputs: the
 * sibling packages are used from source so no build order is needed. The
 * core editor comes from `packages-js/bpmn-editor` or, before it exists in
 * the checkout, from `BPMN_EDITOR_SRC` (local development only).
 */

import { existsSync } from 'node:fs'
import { resolve } from 'node:path'

const here = new URL('.', import.meta.url).pathname

export function sourceAliases(): Record<string, string> {
  const aliases: Record<string, string> = {
    '@flowaudit/bpmn-flowaudit/profiles': resolve(here, '../bpmn-flowaudit/src/profile/bundled.ts'),
    '@flowaudit/bpmn-flowaudit': resolve(here, '../bpmn-flowaudit/src/index.ts'),
  }
  const sibling = resolve(here, '../bpmn-editor/src/index.ts')
  const core = existsSync(sibling) ? sibling : process.env.BPMN_EDITOR_SRC
  if (core) aliases['@flowaudit/bpmn-editor'] = core
  return aliases
}
