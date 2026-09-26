/**
 * Optimistische Änderungen mit fester Reihenfolge: die lokale Kernoperation
 * wirkt sofort, der Port-Aufruf läuft in einer Warteschlange. Das Ergebnis des
 * Ports gilt, sobald keine weitere Änderung aussteht; ein Fehler rollt zurück
 * bzw. lädt nach allen ausstehenden Änderungen neu (auch bei Versionskonflikt).
 */
import type { CommandContext, CommandResult } from '../commands'
import type { KanbanError } from '../errors'
import type { Board } from '../model'
import type { BoardPort, MutationResult } from '../port'

export type LocalChange = ((current: Board, ctx: CommandContext) => CommandResult) | null
export type RemoteChange = (port: BoardPort, boardId: string) => Promise<MutationResult>
export type Mutate = (local: LocalChange, remote: RemoteChange) => Promise<MutationResult | null>

export interface MutatorHooks {
  getBoard: () => Board | null
  setBoard: (board: Board) => void
  port: () => BoardPort | null | undefined
  context: () => CommandContext
  fail: (caught: unknown) => KanbanError
  settled: (result: MutationResult) => void
  reload: () => void
}

export function createMutator(hooks: MutatorHooks): Mutate {
  let queue: Promise<unknown> = Promise.resolve()
  let pending = 0
  let resync = false

  function rollback(before: Board, caught: unknown): void {
    const failure = hooks.fail(caught)
    if (pending === 1 && failure.code !== 'VERSION_CONFLICT') hooks.setBoard(before)
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
      if (pending === 1) hooks.setBoard(result.board)
      hooks.settled(result)
      return result
    } catch (caught) {
      rollback(before, caught)
      return null
    } finally {
      finish()
    }
  }

  return function mutate(local, remote) {
    const port = hooks.port()
    const before = hooks.getBoard()
    if (!port || !before) return Promise.resolve(null)
    try {
      if (local) hooks.setBoard(local(before, hooks.context()).board)
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
