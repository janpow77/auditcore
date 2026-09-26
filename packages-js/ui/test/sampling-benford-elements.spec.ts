import { flushPromises } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { defineFlowauditElements } from '../src/elements'
import analysis from '../../ui-core/test/fixtures/benford-analysis.json'
import benfordProfiles from '../../ui-core/test/fixtures/benford-profiles.json'
import samplingProfiles from '../../ui-core/test/fixtures/sampling-profiles.json'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('Web Components Stichprobe und Benford', () => {
  it('flowaudit-sampling lädt über den Port im Light DOM', async () => {
    defineFlowauditElements({ only: ['flowaudit-sampling'] })
    const element = document.createElement('flowaudit-sampling') as HTMLElement & Record<string, unknown>
    element.port = { profiles: vi.fn(async () => samplingProfiles) }
    document.body.append(element)
    await flushPromises()
    expect(element.shadowRoot).toBeNull()
    expect(element.querySelector('[data-testid="sampling-method"]')).not.toBeNull()
  })

  it('flowaudit-benford sendet analysis-completed', async () => {
    defineFlowauditElements({ only: ['flowaudit-benford'] })
    const element = document.createElement('flowaudit-benford') as HTMLElement & Record<string, unknown>
    element.port = { profiles: vi.fn(async () => benfordProfiles), analyse: vi.fn(async () => analysis) }
    element.values = [1, 2, 3]
    document.body.append(element)
    await flushPromises()
    const received: unknown[] = []
    element.addEventListener('analysis-completed', (event) => received.push((event as CustomEvent<unknown[]>).detail[0]))
    element.querySelector('form')?.dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(received).toEqual([analysis])
    expect(element.querySelectorAll('.fa-benford__bar')).toHaveLength(9)
  })
})
