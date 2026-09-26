import { FaSynopsis, FaTable } from '@auditcore/ui'
import { describe, it } from 'vitest'
import { synopsisCases, tableCases } from '../../../ui-core/test/parity/cases'
import { FlowauditSynopsis } from '../../src/synopsis/FlowauditSynopsis'
import { FlowauditTable } from '../../src/table/FlowauditTable'
import { expectParity, renderBoth } from './setup'

describe('Parität Synopse Vue ↔ React', () => {
  for (const entry of synopsisCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(FaSynopsis, { ...entry.props() }, <FlowauditSynopsis {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

describe('Parität Tabelle Vue ↔ React', () => {
  for (const entry of tableCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(FaTable, { ...entry.props() }, <FlowauditTable {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})
