import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { act } from '@testing-library/react'

/** Synthetic fixtures of @auditcore/bpmn-flowaudit (no user diagrams). */
export function fixture(name: string): string {
  return readFileSync(join(process.cwd(), '../bpmn-flowaudit/test/fixtures', name), 'utf-8')
}

/** Lets pending promises, timers and React updates settle. */
export const flush = () => act(() => new Promise<void>((resolve) => setTimeout(resolve, 0)))

/** Waits until the predicate holds (import and rendering are asynchronous). */
export async function until(predicate: () => boolean | Promise<boolean>, attempts = 80): Promise<void> {
  for (let i = 0; i < attempts; i += 1) {
    await flush()
    if (await predicate()) return
    await act(() => new Promise<void>((resolve) => setTimeout(resolve, 10)))
  }
  throw new Error('Bedingung nicht erfüllt')
}
