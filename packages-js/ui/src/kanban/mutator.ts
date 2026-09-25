/**
 * Optimistische Änderungen mit fester Reihenfolge: die lokale Kernoperation
 * wirkt sofort, der Port-Aufruf läuft in einer Warteschlange. Das Ergebnis des
 * Ports gilt, sobald keine weitere Änderung aussteht; ein Fehler rollt zurück
 * bzw. lädt nach allen ausstehenden Änderungen neu (auch bei Versionskonflikt).
 */
import type { ShallowRef } from 'vue'
import type { Board, BoardPort, CommandContext, CommandResult, KanbanError, MutationResult } from '@flowaudit/kanban-core'

export type LocalChange = ((current: Board, ctx: CommandContext) => CommandResult) | null
export type RemoteChange = (port: BoardPort, boardId: string) => Promise<MutationResult>

export interface MutatorHooks {
  board: ShallowRef<Board | null>
  port: () => BoardPort | null | undefined
  context: () => CommandContext
  fail: (caught: unknown) => KanbanError
  settled: (result: MutationResult) => void
  reload: () => void
}

export function createMutator(hooks: MutatorHooks) {
  let queue: Promise<unknown> = Promise.resolve()
  let pending = 0
  let resync = false

  function rollback(before: Board, caught: unknown): void {
    const failure = hooks.fail(caught)
    if (pending === 1 && failure.code !== 'VERSION_CONFLICT') hooks.board.value = before
    else resync = true
  }

  function finish(): void {
    pending -= 1
    if (pending === 0 && resync) {
      resync = false
      hooks.reload()
    }
  }

  async function send(port: BoardPort, before: Board, remote: RemoteChange): Promise<MutationResult | null> {
    try {
      const result = await remote(port, before.id)
      if (pending === 1) hooks.board.value = result.board
      hooks.settled(result)
      return result
    } catch (caught) {
      rollback(before, caught)
      return null
    } finally {
      finish()
    }
  }

  return function mutate(local: LocalChange, remote: RemoteChange): Promise<MutationResult | null> {
    const port = hooks.port()
    const before = hooks.board.value
    if (!port || !before) return Promise.resolve(null)
    try {
      if (local) hooks.board.value = local(before, hooks.context()).board
    } catch (caught) {
      hooks.fail(caught)
      return Promise.resolve(null)
    }
    pending += 1
    const run = () => send(port, before, remote)
    const next = queue.then(run, run)
    queue = next
    return next
  }
}
