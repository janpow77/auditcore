import { fireEvent as domEvent } from '@testing-library/dom'
import { fireEvent, render } from '@testing-library/react'
import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import PdfRedaction from '../../../ui/src/redaction/PdfRedaction.vue'
import { fakeRedactionPort, fakeUrls, redactionEmptyPlan, syntheticPdf, type RedactionFake } from '../../../ui-core/test/redaction/fake-port'
import { redactionCases } from '../../../ui-core/test/parity/cases-redaction'
import { formState, normalizeDom } from '../../../ui-core/test/parity/dom'
import { FlowauditPdfRedaction } from '../../src/redaction/FlowauditPdfRedaction'
import { both, byTestId, type Step } from './interact'
import { expectParity, renderBoth, tick, type Rendered } from './setup'

describe('Parität PDF schwärzen Vue ↔ React', () => {
  for (const entry of redactionCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(PdfRedaction, { ...entry.props() }, <FlowauditPdfRedaction {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

type Events = typeof domEvent | typeof fireEvent

/** Gleiche Ereignisfolge in beiden Fassungen, danach DOM und Formularzustand vergleichen. */
async function each(rendered: Rendered, act: (root: HTMLElement, events: Events) => void): Promise<void> {
  for (const [root, events] of [[rendered.vue, domEvent], [rendered.react, fireEvent]] as const) {
    act(root, events)
    await flushPromises()
    await tick()
    await flushPromises()
    await tick()
  }
  expect(normalizeDom(rendered.react)).toBe(normalizeDom(rendered.vue))
  expect(formState(rendered.react)).toEqual(formState(rendered.vue))
}

const select = (selector: string): Step => (root) => root.querySelector(selector)
const text = (rendered: Rendered, selector: string): string => rendered.react.querySelector(selector)?.textContent?.trim() ?? ''

async function start(): Promise<{ rendered: Rendered; vuePort: RedactionFake; reactPort: RedactionFake }> {
  const vuePort = fakeRedactionPort()
  const reactPort = fakeRedactionPort()
  const rendered = await renderBoth(PdfRedaction, { port: vuePort, urls: fakeUrls() }, <FlowauditPdfRedaction port={reactPort} urls={fakeUrls()} />)
  return { rendered, vuePort, reactPort }
}

async function toReview(rendered: Rendered): Promise<void> {
  await each(rendered, (root, events) => events.change(root.querySelector('[data-testid="redaction-file"]') as HTMLInputElement, { target: { files: [syntheticPdf()] } }))
  await both(rendered, select('input[data-pattern="email"]'), { kind: 'click' })
  await both(rendered, byTestId('redaction-terms'), { kind: 'input', value: 'Prüfvermerk' })
  await both(rendered, byTestId('redaction-search'), { kind: 'submit' })
}

describe('Parität PDF schwärzen nach Interaktion', () => {
  it('bereitgestellte Datei und Vorgaben bis zur Prüfansicht und zurück', async () => {
    const vuePort = fakeRedactionPort()
    const reactPort = fakeRedactionPort()
    const file = syntheticPdf('arbeitsfassung.pdf')
    const vorgaben = { filename: 'Akte 2026-17.pdf', terms: ['Prüfvermerk'], patterns: ['email'] }
    const rendered = await renderBoth(
      PdfRedaction,
      { port: vuePort, urls: fakeUrls(), file, ...vorgaben },
      <FlowauditPdfRedaction port={reactPort} urls={fakeUrls()} file={file} {...vorgaben} />,
    )
    expect(rendered.react.querySelector('[data-testid="redaction-file"]')).toBeNull()
    expect(text(rendered, '[data-testid="redaction-file-provided"] .fa-redaction__value')).toBe('Akte 2026-17.pdf')
    await both(rendered, byTestId('redaction-search'), { kind: 'submit' })
    expect(reactPort.calls).toEqual(vuePort.calls)
    expect(reactPort.calls[0]).toEqual(['plan', 'Akte 2026-17.pdf', JSON.stringify({ patterns: ['email'], terms: ['Prüfvermerk'], case_sensitive: false, whole_word: true })])
    expect(rendered.react.querySelectorAll('[data-testid="redaction-review"]')).toHaveLength(1)
    expect(normalizeDom(rendered.react)).toBe(normalizeDom(rendered.vue))
  })

  it('Kriterien prüfen, Plan holen, Auswahl ändern, Seiten wechseln', async () => {
    const { rendered, vuePort, reactPort } = await start()
    await both(rendered, byTestId('redaction-search'), { kind: 'submit' })
    expect(text(rendered, '.fa-redaction__error')).toBe('Bitte eine PDF-Datei wählen.')
    await toReview(rendered)
    expect(reactPort.calls).toEqual(vuePort.calls)
    expect(reactPort.calls[0]).toEqual(['plan', 'vermerk.pdf', JSON.stringify({ patterns: ['email'], terms: ['Prüfvermerk'], case_sensitive: false, whole_word: true })])
    expect(rendered.react.querySelector('img.fa-redaction__image')?.getAttribute('src')).toBe('blob:fa-test/image/png/7')
    expect(text(rendered, '[data-testid="redaction-summary"]')).toBe('9 von 9 Fundstellen ausgewählt')

    await both(rendered, select('[data-candidate]'), { kind: 'click' })
    expect(rendered.react.querySelectorAll('.fa-redaction__box--off')).toHaveLength(1)
    await both(rendered, select('[data-source="email"]'), { kind: 'click' })
    expect(text(rendered, '[data-testid="redaction-summary"]')).toBe('5 von 9 Fundstellen ausgewählt')
    await both(rendered, select('.fa-redaction__group-toggle'), { kind: 'click' })
    await both(rendered, select('.fa-redaction__items input'), { kind: 'click' })
    await both(rendered, select('.fa-redaction__group-head input'), { kind: 'click' })
    await both(rendered, byTestId('redaction-deselect-all'), { kind: 'click' })
    await both(rendered, byTestId('redaction-select-all'), { kind: 'click' })
    await both(rendered, select('.fa-redaction__items .fa-redaction__link'), { kind: 'click' })
    expect(text(rendered, '.fa-redaction__pager-text')).toBe('Seite 1 von 3')
    await both(rendered, byTestId('redaction-next'), { kind: 'click' })
    await both(rendered, byTestId('redaction-next'), { kind: 'click' })
    expect(text(rendered, '.fa-redaction__pager-text')).toBe('Seite 3 von 3')
    await both(rendered, byTestId('redaction-previous'), { kind: 'click' })
    await both(rendered, select('.fa-redaction__page-link'), { kind: 'click' })
    expect(rendered.react.querySelector('[aria-current="page"]')?.textContent).toBe('1')
    expect(reactPort.calls).toEqual(vuePort.calls)
    expect(reactPort.calls.filter((call) => call[0] === 'preview').map((call) => call[2])).toEqual([1, 2, 3])
    await both(rendered, byTestId('redaction-back'), { kind: 'click' })
    expect(rendered.react.querySelector('[data-testid="redaction-form"]')).not.toBeNull()
  })

  it('eigene Bereiche mit Zeiger und Tastatur, schwärzen, Ergebnis', async () => {
    const { rendered, vuePort, reactPort } = await start()
    await toReview(rendered)
    for (const root of [rendered.vue, rendered.react]) {
      const overlay = root.querySelector('[data-testid="redaction-overlay"]') as HTMLElement
      overlay.getBoundingClientRect = () => ({ left: 0, top: 0, width: 1000, height: 1000, right: 1000, bottom: 1000, x: 0, y: 0, toJSON: () => ({}) })
    }
    await each(rendered, (root, events) => {
      const overlay = root.querySelector('[data-testid="redaction-overlay"]') as HTMLElement
      events.pointerDown(overlay, { clientX: 100, clientY: 100, button: 0, pointerId: 1 })
      events.pointerMove(overlay, { clientX: 300, clientY: 200, pointerId: 1 })
    })
    expect(rendered.react.querySelector('.fa-redaction__draft')).not.toBeNull()
    await each(rendered, (root, events) => events.pointerUp(root.querySelector('[data-testid="redaction-overlay"]') as HTMLElement, { clientX: 300, clientY: 200, pointerId: 1 }))
    expect(rendered.react.querySelector('.fa-redaction__draft')).toBeNull()
    expect(rendered.react.querySelector('[data-area="1"]')?.getAttribute('style')).toContain('width: 20%')
    await each(rendered, (root, events) => {
      const overlay = root.querySelector('[data-testid="redaction-overlay"]') as HTMLElement
      events.pointerDown(root.querySelector('.fa-redaction__area-resize') as HTMLElement, { clientX: 300, clientY: 200, button: 0, pointerId: 2 })
      events.pointerMove(overlay, { clientX: 400, clientY: 250, pointerId: 2 })
      events.pointerUp(overlay, { clientX: 400, clientY: 250, pointerId: 2 })
    })
    expect(rendered.react.querySelector('[data-area="1"]')?.getAttribute('style')).toContain('width: 30%')
    await each(rendered, (root, events) => {
      const overlay = root.querySelector('[data-testid="redaction-overlay"]') as HTMLElement
      events.pointerDown(overlay, { clientX: 100, clientY: 100, button: 2, pointerId: 3 })
      events.pointerDown(root.querySelector('[data-candidate]') as HTMLElement, { clientX: 100, clientY: 100, button: 0, pointerId: 3 })
      events.pointerCancel(overlay, { pointerId: 3 })
    })
    await both(rendered, byTestId('redaction-add-area'), { kind: 'click' })
    await each(rendered, (root, events) => {
      const area = root.querySelector('[data-area="2"]') as HTMLElement
      events.keyDown(area.querySelector('.fa-redaction__area-move') as HTMLElement, { key: 'ArrowDown', shiftKey: true })
      events.keyDown(area.querySelector('.fa-redaction__area-move') as HTMLElement, { key: 'Enter' })
      events.keyDown(area.querySelector('.fa-redaction__area-resize') as HTMLElement, { key: 'ArrowRight' })
      events.keyDown(area.querySelector('.fa-redaction__area-resize') as HTMLElement, { key: 'a' })
    })
    expect(rendered.react.querySelector('[data-area="2"]')?.getAttribute('style')).toBe('left: 33%; top: 48%; width: 30.5%; height: 8%;')
    await each(rendered, (root, events) => {
      const overlay = root.querySelector('[data-testid="redaction-overlay"]') as HTMLElement
      events.pointerDown(root.querySelector('[data-area="2"] .fa-redaction__area-move') as HTMLElement, { clientX: 400, clientY: 500, button: 0, pointerId: 4 })
      events.pointerMove(overlay, { clientX: 500, clientY: 500, pointerId: 4 })
      events.pointerUp(overlay, { clientX: 500, clientY: 500, pointerId: 4 })
    })
    expect(rendered.react.querySelector('[data-area="2"]')?.getAttribute('style')).toContain('left: 43%')
    await both(rendered, byTestId('redaction-add-area'), { kind: 'click' })
    await each(rendered, (root, events) => events.keyDown(root.querySelector('[data-area="3"] .fa-redaction__area-move') as HTMLElement, { key: 'Delete' }))
    await both(rendered, select('[data-area="2"] .fa-redaction__area-remove'), { kind: 'click' })
    expect(document.activeElement?.getAttribute('data-testid')).toBe('redaction-add-area')
    expect(text(rendered, '[data-testid="redaction-summary"]')).toBe('9 von 9 Fundstellen ausgewählt, 1 eigener Bereich')
    await both(rendered, byTestId('redaction-sanitize'), { kind: 'click' })
    await both(rendered, byTestId('redaction-apply'), { kind: 'click' })
    expect(reactPort.calls).toEqual(vuePort.calls)
    const apply = reactPort.calls.at(-1)!
    expect(apply[0]).toBe('apply')
    expect(apply[2]).toMatchObject({ sanitize: false, areas: [{ page: 1, rect: [0.1, 0.1, 0.4, 0.25] }] })
    expect(text(rendered, '[data-report="areas"]')).toBe('1')
    const link = rendered.react.querySelector('[data-testid="redaction-download"]')
    expect(link?.getAttribute('href')).toBe('blob:fa-test/application/pdf/20')
    expect(link?.getAttribute('download')).toBe('vermerk_geschwärzt.pdf')
    await both(rendered, byTestId('redaction-edit'), { kind: 'click' })
    expect(rendered.react.querySelector('[data-testid="redaction-review"]')).not.toBeNull()
    await both(rendered, byTestId('redaction-apply'), { kind: 'click' })
    await both(rendered, byTestId('redaction-reset'), { kind: 'click' })
    expect(rendered.react.querySelector('[data-testid="redaction-form"]')).not.toBeNull()
  })

  it('leerer Plan, Optionen, Seitenbildfehler', async () => {
    const vuePort = { ...fakeRedactionPort({ plan: redactionEmptyPlan }), preview: async () => { throw new Error('Vorschau gesperrt') } }
    const reactPort = { ...fakeRedactionPort({ plan: redactionEmptyPlan }), preview: async () => { throw new Error('Vorschau gesperrt') } }
    const rendered = await renderBoth(PdfRedaction, { port: vuePort, urls: fakeUrls(), locale: 'de' }, <FlowauditPdfRedaction port={reactPort} urls={fakeUrls()} locale="de" />)
    await each(rendered, (root, events) => events.change(root.querySelector('[data-testid="redaction-file"]') as HTMLInputElement, { target: { files: [syntheticPdf()] } }))
    await both(rendered, byTestId('redaction-case'), { kind: 'click' })
    await both(rendered, byTestId('redaction-whole-word'), { kind: 'click' })
    await both(rendered, byTestId('redaction-terms'), { kind: 'input', value: 'gibt es nicht' })
    await both(rendered, byTestId('redaction-search'), { kind: 'submit' })
    expect(text(rendered, '.fa-redaction__page .fa-redaction__error')).toBe('Seitenbild nicht verfügbar: Vorschau gesperrt')
    expect(rendered.react.textContent).toContain('Keine Fundstellen. Sie können trotzdem eigene Bereiche markieren.')
    expect(rendered.react.querySelector('[data-testid="redaction-select-all"]')?.hasAttribute('disabled')).toBe(true)
  })
})

describe('Parität PDF schwärzen bei geänderten Vorgaben', () => {
  it('Dateiwechsel, nur neuer Name und neues Array gleichen Inhalts nach eigener Eingabe', async () => {
    const vuePort = fakeRedactionPort()
    const reactPort = fakeRedactionPort()
    const urls = fakeUrls()
    const first = syntheticPdf('a.pdf')
    const host = document.createElement('div')
    document.body.append(host)
    const wrapper = mount(PdfRedaction, { props: { port: vuePort, urls, file: first, filename: 'A.pdf', terms: ['Erika'] }, attachTo: host })
    const view = (props: { file: Blob; filename: string; terms: string[] }) => <FlowauditPdfRedaction port={reactPort} urls={urls} {...props} />
    const { container, rerender } = render(view({ file: first, filename: 'A.pdf', terms: ['Erika'] }))
    const rendered: Rendered = { vue: wrapper.element as HTMLElement, react: container.firstElementChild as HTMLElement }
    const update = async (props: { file: Blob; filename: string; terms: string[] }): Promise<void> => {
      await wrapper.setProps(props as never)
      rerender(view(props))
      await flushPromises()
      await tick()
      await flushPromises()
      expect(normalizeDom(rendered.react)).toBe(normalizeDom(rendered.vue))
      expect(formState(rendered.react)).toEqual(formState(rendered.vue))
    }
    await flushPromises()
    await tick()
    const name = (root: HTMLElement): string => root.querySelector('.fa-redaction__value')?.textContent ?? ''
    const terms = (root: HTMLElement): string => (root.querySelector('[data-testid="redaction-terms"]') as HTMLTextAreaElement).value

    await both(rendered, byTestId('redaction-terms'), { kind: 'input', value: 'eigene Eingabe' })
    await update({ file: first, filename: 'A.pdf', terms: ['Erika'] })
    expect([terms(rendered.vue), terms(rendered.react)]).toEqual(['eigene Eingabe', 'eigene Eingabe'])

    await update({ file: first, filename: 'A neu.pdf', terms: ['Erika'] })
    expect([name(rendered.vue), name(rendered.react)]).toEqual(['A neu.pdf', 'A neu.pdf'])

    await update({ file: syntheticPdf('b.pdf'), filename: 'B.pdf', terms: ['Max'] })
    expect([name(rendered.vue), name(rendered.react)]).toEqual(['B.pdf', 'B.pdf'])
    expect([terms(rendered.vue), terms(rendered.react)]).toEqual(['Max', 'Max'])
    wrapper.unmount()
  })
})

