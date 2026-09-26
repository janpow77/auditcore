import { describe, expect, it } from 'vitest'
import BatchChecks from '../../../ui/src/batchchecks/BatchChecks.vue'
import { createBatchchecksMemoryPort } from '../../../ui-core/src'
import { batchchecksCases, batchchecksItems } from '../../../ui-core/test/parity/cases-batchchecks'
import { FlowauditBatchChecks } from '../../src/batchchecks/FlowauditBatchChecks'
import { both } from './interact'
import { expectParity, renderBoth } from './setup'

describe('Parität BatchChecks Vue ↔ React', () => {
  for (const entry of batchchecksCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(BatchChecks, { ...entry.props() }, <FlowauditBatchChecks {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

describe('Parität BatchChecks nach Interaktion', () => {
  it('Eintrag auswählen', async () => {
    const port = createBatchchecksMemoryPort(batchchecksItems)
    const rendered = await renderBoth(BatchChecks, { port }, <FlowauditBatchChecks port={port} />)
    await both(rendered, (root) => root.querySelectorAll('button')[1], { kind: 'click' })
    expect(rendered.react.querySelectorAll('[aria-pressed="true"]')).toHaveLength(1)
  })
})
