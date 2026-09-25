import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import SamplingPanel from '../../src/sampling/SamplingPanel.vue'
import type { SamplingCatalogue, SamplingPort, SelectionResult, SizeResult } from '../../src/sampling/types'
import profiles from '../fixtures/sampling-profiles.json'
import selection from '../fixtures/sampling-selection.json'
import size from '../fixtures/sampling-size.json'

const items = Array.from({ length: 30 }, (_, i) => ({ id: `B-${i + 1}`, value: ((i * 37) % 900) + 10, stratum: i % 3 ? 'Los 1' : 'Los 2' }))

function fakePort(): SamplingPort & { calls: Record<string, unknown[]> } {
  const calls: Record<string, unknown[]> = { size: [], selection: [], export: [] }
  return {
    calls,
    profiles: vi.fn(async () => profiles as unknown as SamplingCatalogue),
    size: vi.fn(async (request) => {
      calls.size?.push(request)
      return size as unknown as SizeResult
    }),
    allocation: vi.fn(),
    selection: vi.fn(async (request) => {
      calls.selection?.push(request)
      return selection as unknown as SelectionResult
    }),
    exportSelection: vi.fn(async (request, format) => {
      calls.export?.push([request, format])
      return { blob: new Blob(['x']), filename: 'stichprobe.csv', mediaType: 'text/csv' }
    }),
  }
}

async function mounted(port = fakePort()) {
  const wrapper = mount(SamplingPanel, { props: { port, items }, attachTo: document.body })
  await flushPromises()
  return { wrapper, port }
}

afterEach(() => {
  document.body.innerHTML = ''
})

describe('SamplingPanel', () => {
  it('lädt die Profile und wählt die empfohlene Methode sichtbar vor', async () => {
    const { wrapper } = await mounted()
    const select = wrapper.get('[data-testid="sampling-method"]').element as HTMLSelectElement
    expect(select.value).toBe('portal.mus_poisson')
    expect(wrapper.text()).toContain('Empfohlen')
    expect(wrapper.text()).toContain('n = ⌈RF · V / max(M − V · r, M / 2)⌉')
  })

  it('meldet fehlende Pflichtangaben mit role=alert statt zu raten', async () => {
    const { wrapper, port } = await mounted()
    await wrapper.get('form').trigger('submit')
    expect(port.size).not.toHaveBeenCalled()
    expect(wrapper.findAll('[role="alert"]').length).toBeGreaterThanOrEqual(3)
    expect(wrapper.get('[data-testid="sampling-materiality"]').attributes('aria-invalid')).toBe('true')
  })

  it('berechnet den Umfang mit Herleitung und sendet size-calculated', async () => {
    const { wrapper, port } = await mounted()
    await wrapper.get('[data-testid="sampling-population_value"]').setValue('475.478,94')
    await wrapper.get('[data-testid="sampling-materiality"]').setValue('50.000')
    await wrapper.get('[data-testid="sampling-expected_error_rate"]').setValue('0,5')
    await wrapper.get('[data-testid="sampling-confidence"]').setValue('0.95')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(port.calls.size).toEqual([{ method: 'portal.mus_poisson', population_value: 475478.94, materiality: 50000, expected_error_rate: 0.005, confidence_level: 0.95 }])
    expect(wrapper.get('[data-testid="sampling-size"]').text()).toBe('n = 30')
    expect(wrapper.text()).toContain('Präzision')
    expect(wrapper.emitted('size-calculated')?.[0]).toEqual([size])
    expect((wrapper.get('[data-testid="sampling-sample-size"]').element as HTMLInputElement).value).toBe('30')
  })

  it('zieht mit Aufteilung je Schicht, zeigt den Seed und exportiert', async () => {
    const { wrapper, port } = await mounted()
    await wrapper.get('[data-testid="sampling-sample-size"]').setValue('6')
    await wrapper.get('[data-testid="sampling-draw"]').trigger('submit')
    await wrapper.get('[data-testid="sampling-draw"]').element.closest('form')?.dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(wrapper.text()).toContain('Aufteilung auf Schichten wählen.')
    await wrapper.get('[data-testid="sampling-allocation"]').setValue('proportional')
    await wrapper.get('[data-testid="sampling-draw"]').element.closest('form')?.dispatchEvent(new Event('submit'))
    await flushPromises()
    expect(port.calls.selection?.[0]).toMatchObject({ method: 'mus', variant: 'portal', sample_size: 6, allocation: 'proportional' })
    expect(port.calls.selection?.[0]).not.toHaveProperty('seed')
    expect(wrapper.get('[data-testid="sampling-seed-used"]').text()).toContain('Seed 42')
    expect((wrapper.get('[data-testid="sampling-seed"]').element as HTMLInputElement).value).toBe('42')
    expect(wrapper.findAll('[data-testid="sampling-rows"] tbody tr')).toHaveLength(selection.rows.length)
    URL.createObjectURL = vi.fn(() => 'blob:x')
    URL.revokeObjectURL = vi.fn()
    await wrapper.get('[data-testid="sampling-export-csv"]').trigger('click')
    await flushPromises()
    expect(port.calls.export?.[0]).toEqual([expect.objectContaining({ seed: 42 }), 'csv'])
    expect(URL.createObjectURL).toHaveBeenCalled()
  })

  it('zeigt Serverfehler und sendet error', async () => {
    const port = fakePort()
    port.size = vi.fn(async () => {
      throw new Error('Konfidenzniveau 0.93 ist nicht definiert')
    })
    const { wrapper } = await mounted(port)
    for (const [key, value] of [['population_value', '1'], ['materiality', '1'], ['expected_error_rate', '0']]) {
      await wrapper.get(`[data-testid="sampling-${key}"]`).setValue(value)
    }
    await wrapper.get('[data-testid="sampling-confidence"]').setValue('0.95')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(wrapper.text()).toContain('Anfrage abgelehnt: Konfidenzniveau 0.93 ist nicht definiert')
    expect(wrapper.emitted('error')?.[0]).toEqual(['Konfidenzniveau 0.93 ist nicht definiert'])
  })

  it('übersetzt Beschriftungen mit locale=en und fällt sonst auf Deutsch zurück', async () => {
    const wrapper = mount(SamplingPanel, { props: { port: fakePort(), items, locale: 'en' } })
    await flushPromises()
    expect(wrapper.text()).toContain('Calculate sample size')
    expect(wrapper.text()).toContain('Draw sample')
    expect(wrapper.text()).toContain('Grundgesamtheit')
  })
})
