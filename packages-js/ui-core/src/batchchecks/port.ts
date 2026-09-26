import type { BatchchecksItem, BatchchecksPort } from './types'

/**
 * Port im Arbeitsspeicher (Demo, Tests). Eine REST-Umsetzung baut auf
 * `requestJson` aus `@auditcore/common` auf (Vorbild: `extrapolation/rest-port.ts`).
 */
export function createBatchchecksMemoryPort(items: readonly BatchchecksItem[]): BatchchecksPort {
  return { list: async () => items }
}
