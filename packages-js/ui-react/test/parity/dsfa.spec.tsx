import { FaDsfa } from '@flowaudit/ui'
import { flushPromises } from '@vue/test-utils'
import { act, fireEvent } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { dsfaCases } from '../../../ui-core/test/parity/cases-dsfa'
import { fakePort } from '../../../ui-core/test/dataprotection/fake-port'
import { normalizeDom, formState } from '../../../ui-core/test/parity/dom'
import { FlowauditDsfa } from '../../src/dataprotection/FlowauditDsfa'
import { expectParity, renderBoth, tick, type Rendered } from './setup'

async function settle(): Promise<void> {
  await flushPromises()
  await tick()
  await flushPromises()
}

/** Dieselbe Eingabe an beiden Fassungen, danach beide DOM-Bäume vergleichen. */
async function both(rendered: Rendered, action: (root: HTMLElement) => void): Promise<void> {
  await act(async () => {
    action(rendered.vue)
    action(rendered.react)
  })
  await settle()
}

function expectSame(rendered: Rendered): void {
  expect(normalizeDom(rendered.react)).toBe(normalizeDom(rendered.vue))
  expect(formState(rendered.react)).toEqual(formState(rendered.vue))
}

async function renderDraft(props: Record<string, unknown> = {}): Promise<Rendered> {
  const all = { port: fakePort(), actor: 'daten-b', activityId: 'foerderung', ...props }
  return renderBoth(FaDsfa, all, <FlowauditDsfa {...all} />)
}

describe('Parität DSFA Vue ↔ React', () => {
  for (const entry of dsfaCases) {
    it(entry.name, async () => {
      const props = entry.props()
      const rendered = await renderBoth(FaDsfa, { ...props }, <FlowauditDsfa {...props} />)
      expectParity(rendered, entry.expect)
    })
  }

  it('nach Tabwechsel per Pfeiltaste und Ende (freigegebene Fassung)', async () => {
    const rendered = await renderDraft({ activityId: 'pruefung' })
    await both(rendered, (root) => fireEvent.keyDown(root.querySelector('[role="tablist"]')!, { key: 'ArrowRight' }))
    expect(rendered.react.querySelector('[data-testid="dsfa-risk"]')).not.toBeNull()
    expectSame(rendered)
    await both(rendered, (root) => fireEvent.keyDown(root.querySelector('[role="tablist"]')!, { key: 'End' }))
    expect(rendered.react.querySelector('[data-testid="dsfa-decision"]')).not.toBeNull()
    expectSame(rendered)
  })

  it('nach geänderter Antwort mit Vorschau der Bibliothek', async () => {
    const rendered = await renderDraft()
    await both(rendered, (root) => (root.querySelector('[data-question="art35_3_a"] input[value="ja"]') as HTMLInputElement).click())
    // Vorschau nach der Wartezeit der Bibliothek (previewDelay 400 ms) in beiden Fassungen.
    await act(() => new Promise<void>((resolve) => setTimeout(resolve, 450)))
    await settle()
    expect(rendered.react.textContent).toContain('Vorschau der Bibliothek')
    expectSame(rendered)
  })

  it('nach gewählter Entscheidung mit Abweichungshinweis', async () => {
    const rendered = await renderDraft({ actor: 'daten-a' })
    await both(rendered, (root) => fireEvent.click(root.querySelectorAll('[role="tab"]')[2]!))
    await both(rendered, (root) => fireEvent.change(root.querySelector('[data-testid="dsfa-decision"] select')!, { target: { value: 'freigabe_mit_auflagen' } }))
    expect(rendered.react.querySelector('[data-testid="dsfa-four-eyes"]')).not.toBeNull()
    expectSame(rendered)
  })
})
