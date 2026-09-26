import { KanbanBoard, KanbanBoardList } from '@auditcore/ui'
import { describe, it } from 'vitest'
import { boardListCases, kanbanCases } from '../../../kanban-core/test/parity/cases'
import { FlowauditKanbanBoard } from '../../src/kanban/FlowauditKanbanBoard'
import { FlowauditKanbanBoards } from '../../src/kanban/FlowauditKanbanBoards'
import { expectParity, renderBoth } from './setup'

describe('Parität Kanban-Board Vue ↔ React', () => {
  for (const entry of kanbanCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(KanbanBoard, { ...entry.props() }, <FlowauditKanbanBoard {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

describe('Parität Kanban-Boardliste Vue ↔ React', () => {
  for (const entry of boardListCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(KanbanBoardList, { ...entry.props() }, <FlowauditKanbanBoards {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})
