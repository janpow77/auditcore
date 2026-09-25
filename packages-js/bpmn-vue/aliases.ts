/**
 * Source aliases for development, tests and the bundled outputs: the
 * sibling packages (core editor and FlowAudit layer) are used from source,
 * so no build order is needed.
 */

import { resolve } from 'node:path'

const here = new URL('.', import.meta.url).pathname

export function sourceAliases(): Record<string, string> {
  const aliases: Record<string, string> = {
    '@flowaudit/bpmn-flowaudit/profiles': resolve(here, '../bpmn-flowaudit/src/profile/bundled.ts'),
    '@flowaudit/bpmn-flowaudit': resolve(here, '../bpmn-flowaudit/src/index.ts'),
  }
  aliases['@flowaudit/bpmn-editor'] = resolve(here, '../bpmn-editor/src/index.ts')
  return aliases
}
