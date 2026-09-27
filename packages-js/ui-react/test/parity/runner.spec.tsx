import { describe, expect, it } from 'vitest'
import RunnerConsole from '../../../ui/src/runner/RunnerConsole.vue'
import { runnerBeispielPort, runnerCases } from '../../../ui-core/test/parity/cases-runner'
import { FlowauditRunnerConsole } from '../../src/runner/FlowauditRunnerConsole'
import { both, type Step } from './interact'
import { expectParity, renderBoth } from './setup'

const byRole = (role: string, name: string): Step => (root) =>
  Array.from(root.querySelectorAll(`[role="${role}"], ${role === 'button' ? 'button' : role}`)).find(
    (element) => (element.getAttribute('aria-label') ?? element.textContent ?? '').trim() === name,
  )
const byLabel = (text: string): Step => (root) => {
  const label = Array.from(root.querySelectorAll('label')).find((element) => element.textContent?.trim() === text)
  return label ? root.querySelector(`#${CSS.escape(label.getAttribute('for') ?? '')}`) : null
}

describe('Parität RunnerConsole Vue ↔ React', () => {
  for (const entry of runnerCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(RunnerConsole, { ...entry.props() }, <FlowauditRunnerConsole {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

describe('Parität RunnerConsole nach Interaktion', () => {
  it('Reiter wechseln, Feld ändern, prüfen', async () => {
    const port = runnerBeispielPort()
    const rendered = await renderBoth(RunnerConsole, { port }, <FlowauditRunnerConsole port={port} />)
    await both(rendered, byRole('tab', 'Einstellungen'), { kind: 'click' })
    await both(rendered, (root) => root.querySelectorAll('input[type="number"]')[0], { kind: 'input', value: '6' })
    expect(rendered.react.textContent).toContain('Nicht angewendete Änderungen')
    await both(rendered, byRole('button', 'Prüfen'), { kind: 'submit' })
    expect(rendered.react.textContent).toContain('Vorschau der Änderungen')
  })

  it('Schalter und Auswahl', async () => {
    const port = runnerBeispielPort()
    const rendered = await renderBoth(RunnerConsole, { port, ansicht: 'einstellungen' }, <FlowauditRunnerConsole port={port} ansicht="einstellungen" />)
    await both(rendered, byLabel('Vorrang interaktiver Nutzung'), { kind: 'click' })
    await both(rendered, byLabel('Soll-Quelle'), { kind: 'change', value: 'statisch' })
    expect((byLabel('Soll-Quelle')(rendered.react) as HTMLSelectElement).value).toBe('statisch')
  })

  it('Priorität verschieben und Werkzeug abschalten', async () => {
    const port = runnerBeispielPort()
    const rendered = await renderBoth(RunnerConsole, { port, ansicht: 'prioritaeten' }, <FlowauditRunnerConsole port={port} ansicht="prioritaeten" />)
    await both(rendered, byRole('button', 'Nach unten: cpu'), { kind: 'click' })
    expect(rendered.react.querySelector('ol > li strong')?.textContent).toBe('gpu')
    await both(rendered, byRole('tab', 'Werkzeuge'), { kind: 'click' })
    await both(rendered, (root) => root.querySelector('input[aria-label="Aktiv: ruff"]'), { kind: 'click' })
    expect(rendered.react.querySelector<HTMLButtonElement>('.fa-button--primary')?.disabled).toBe(false)
  })
})
