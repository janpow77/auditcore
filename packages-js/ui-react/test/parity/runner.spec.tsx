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

  it('Klasse hinzufügen, umbenennen und Art auf gpu stellen', async () => {
    const port = runnerBeispielPort()
    const rendered = await renderBoth(RunnerConsole, { port, ansicht: 'einstellungen' }, <FlowauditRunnerConsole port={port} ansicht="einstellungen" />)
    const neu: Step = (root) => root.querySelector('input[id$="-neue-klasse"]')
    await both(rendered, neu, { kind: 'input', value: 'Falsch!' })
    expect(rendered.react.textContent).toContain('Klassenname: a–z, 0–9, Bindestrich, höchstens 31 Zeichen')
    await both(rendered, neu, { kind: 'input', value: 'nacht' })
    await both(rendered, byRole('button', 'Klasse hinzufügen'), { kind: 'click' })
    expect(rendered.react.textContent).toContain('Klasse nacht')
    await both(rendered, (root) => root.querySelector('input[id$="-klasse-nacht-name"]'), { kind: 'input', value: 'nacht-gpu' })
    await both(rendered, (root) => root.querySelector('input[id$="-klasse-nacht-name"]')?.parentElement?.querySelector('button'), { kind: 'click' })
    await both(rendered, (root) => root.querySelector('select[id$="klassen.nacht-gpu.art"]'), { kind: 'change', value: 'gpu' })
    expect(rendered.react.querySelector('input[id$="klassen.nacht-gpu.vram_mb"]')).toBeTruthy()
  })
})
