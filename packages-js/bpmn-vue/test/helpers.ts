import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { flushPromises } from '@vue/test-utils'

/** Synthetic fixtures of @auditcore/bpmn-flowaudit (no user diagrams). */
export function fixture(name: string): string {
  return readFileSync(join(process.cwd(), '../bpmn-flowaudit/test/fixtures', name), 'utf-8')
}

/** Waits until the predicate holds (import and rendering are asynchronous). */
export async function until(predicate: () => boolean | Promise<boolean>, attempts = 50): Promise<void> {
  for (let i = 0; i < attempts; i += 1) {
    await flushPromises()
    if (await predicate()) return
    await new Promise((resolve) => setTimeout(resolve, 10))
  }
  throw new Error('Bedingung nicht erfüllt')
}
