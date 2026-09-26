import { describe, expect, it } from 'vitest'
import FaDbKanban from '../../../ui/src/dbkanban/FaDbKanban.vue'
import { recordPort } from '../../../ui-core/test/dbkanban/fixtures'
import { dbKanbanCases } from '../../../ui-core/test/parity/cases-dbkanban'
import { FlowauditDbKanban } from '../../src/dbkanban/FlowauditDbKanban'
import { both } from './interact'
import { expectParity, renderBoth } from './setup'

describe('Parität Datenbankansicht Vue ↔ React', () => {
  for (const entry of dbKanbanCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(FaDbKanban, { ...entry.props() }, <FlowauditDbKanban {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

describe('Parität Datenbankansicht nach Interaktion', () => {
  it('Gruppierung wechseln, suchen, Eintrag anlegen', async () => {
    const vuePort = recordPort()
    const reactPort = recordPort()
    const rendered = await renderBoth(FaDbKanban, { port: vuePort }, <FlowauditDbKanban port={reactPort} />)
    await both(rendered, (root) => root.querySelector('select'), { kind: 'change', value: 'fonds' })
    expect(rendered.react.querySelectorAll('.fa-db-kanban-column')).toHaveLength(4)
    await both(rendered, (root) => root.querySelector('[data-column="JTF"] .fa-db-kanban-column__add'), { kind: 'click' })
    expect(reactPort.addRow.mock.calls).toEqual(vuePort.addRow.mock.calls)
    await both(rendered, (root) => root.querySelector('input[type="search"]'), { kind: 'input', value: 'esf+' })
    expect(rendered.react.querySelectorAll('.fa-db-kanban-card')).toHaveLength(1)
  })
})
