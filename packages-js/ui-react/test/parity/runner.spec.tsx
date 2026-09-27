import { describe, expect, it } from 'vitest'
import RunnerConsole from '../../../ui/src/runner/RunnerConsole.vue'
import { createRunnerMemoryPort } from '../../../ui-core/src'
import { runnerCases, runnerItems } from '../../../ui-core/test/parity/cases-runner'
import { FlowauditRunnerConsole } from '../../src/runner/FlowauditRunnerConsole'
import { both } from './interact'
import { expectParity, renderBoth } from './setup'

describe('Parität RunnerConsole Vue ↔ React', () => {
  for (const entry of runnerCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(RunnerConsole, { ...entry.props() }, <FlowauditRunnerConsole {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

describe('Parität RunnerConsole nach Interaktion', () => {
  it('Eintrag auswählen', async () => {
    const port = createRunnerMemoryPort(runnerItems)
    const rendered = await renderBoth(RunnerConsole, { port }, <FlowauditRunnerConsole port={port} />)
    await both(rendered, (root) => root.querySelectorAll('button')[1], { kind: 'click' })
    expect(rendered.react.querySelectorAll('[aria-pressed="true"]')).toHaveLength(1)
  })
})
