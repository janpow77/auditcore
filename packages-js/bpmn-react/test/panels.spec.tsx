import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { ProfileLegalSearch, type LegalBasis, type Marker } from '@flowaudit/bpmn-flowaudit'
import { LISTS, type FieldDescriptor } from '@flowaudit/bpmn-flowaudit/ui'
import { FieldForm } from '../src/panels/FieldForm'
import { ListEditor } from '../src/panels/ListEditor'
import { LegalBasisEditor } from '../src/panels/legal/LegalBasisEditor'
import { LegalSearch } from '../src/panels/legal/LegalSearch'
import { MarkerPicker } from '../src/panels/tabs/MarkerPicker'
import { PropertiesPanel } from '../src/panels/PropertiesPanel'
import { renderInContext } from './context'
import { until } from './helpers'

afterEach(cleanup)

const noOptions = () => []

describe('FieldForm', () => {
  const fields: FieldDescriptor[] = [
    { key: 'label', label: 'field.label', kind: 'text' },
    { key: 'keyControl', label: 'field.keyControl', kind: 'checkbox' },
    { key: 'controls', label: 'field.controls', kind: 'tokens' },
    { key: 'frequency', label: 'field.frequency', kind: 'select' },
  ]

  it('reports the updated object on commit, trims text and drops empty values', () => {
    const onUpdate = vi.fn()
    const { container } = render(<FieldForm value={{ label: 'alt', frequency: 'monatlich' }} fields={fields} optionsFor={() => [{ value: 'monatlich', label: 'monatlich' }]} onUpdate={onUpdate} />)
    const last = () => onUpdate.mock.calls.at(-1)![0]
    const [label, controls] = Array.from(container.querySelectorAll<HTMLInputElement>('input.fa-input'))
    fireEvent.change(label!, { target: { value: '  neu  ' } })
    expect(onUpdate).not.toHaveBeenCalled()
    fireEvent.blur(label!)
    expect(last()).toEqual({ label: 'neu', frequency: 'monatlich' })
    fireEvent.click(container.querySelector('input[type="checkbox"]')!)
    expect(last()).toMatchObject({ keyControl: true })
    fireEvent.change(controls!, { target: { value: 'K1, K2 K3' } })
    fireEvent.keyDown(controls!, { key: 'Enter' })
    expect(last()).toMatchObject({ controls: ['K1', 'K2', 'K3'] })
    fireEvent.change(container.querySelector('select')!, { target: { value: '' } })
    expect(last()).not.toHaveProperty('frequency')
  })

  it('keeps unknown select values visible and respects disabled', () => {
    const { container } = render(<FieldForm value={{ frequency: 'alle 7 Jahre' }} fields={fields} optionsFor={noOptions} disabled onUpdate={vi.fn()} />)
    expect(container.querySelector('select')!.textContent).toContain('alle 7 Jahre')
    expect(Array.from(container.querySelectorAll('input')).every((input) => input.disabled)).toBe(true)
  })
})

describe('ListEditor', () => {
  it('adds, opens, edits and removes entries', () => {
    const onUpdate = vi.fn()
    const { container, rerender } = render(<ListEditor descriptor={LISTS.controls} items={[{ id: 'K1', label: 'Sichtprüfung' }]} optionsFor={noOptions} onUpdate={onUpdate} />)
    expect(container.textContent).toContain('Sichtprüfung')
    fireEvent.click(container.querySelector('.fa-btn')!)
    expect(onUpdate.mock.calls[0]![0]).toHaveLength(2)
    rerender(<ListEditor descriptor={LISTS.controls} items={[{ id: 'K1', label: 'Sichtprüfung' }]} optionsFor={noOptions} onUpdate={onUpdate} />)
    fireEvent.click(container.querySelector('.fa-list-editor__toggle')!)
    fireEvent.click(container.querySelector('.fa-list-editor__toggle')!)
    fireEvent.click(container.querySelector('.fa-list-editor__toggle')!)
    expect(container.querySelector('.fa-field-form')).not.toBeNull()
    const label = container.querySelectorAll<HTMLInputElement>('.fa-field-form input.fa-input')[1]!
    fireEvent.change(label, { target: { value: 'Stichprobe' } })
    fireEvent.blur(label)
    expect(onUpdate.mock.calls.at(-1)![0]).toEqual([{ id: 'K1', label: 'Stichprobe' }])
    fireEvent.click(container.querySelector('.fa-list-editor__row .fa-icon-btn')!)
    expect(onUpdate.mock.calls.at(-1)![0]).toEqual([])
  })
})

describe('legal bases', () => {
  it('takes a typed citation over in structured form', () => {
    const onChoose = vi.fn()
    const { container } = render(<LegalSearch onChoose={onChoose} />)
    fireEvent.change(container.querySelector('input')!, { target: { value: 'Art. 74 Abs. 1 VO (EU) 2021/1060' } })
    fireEvent.click(screen.getAllByRole('option')[0]!)
    const chosen = onChoose.mock.calls[0]![0] as LegalBasis
    expect(chosen).toMatchObject({ article: '74', paragraph: '1' })
    expect(chosen.act).toContain('2021/1060')
    expect(container.querySelector('input')!.value).toBe('')
  })

  it('asks the search port for suggestions (debounced)', async () => {
    const port = { search: vi.fn(async () => [{ act: 'Verordnung (EU) 2021/1060', article: '69', title: 'Verantwortlichkeiten', origin: 'Profil' }]) }
    const onChoose = vi.fn()
    const { container } = render(<LegalSearch port={port} profileId="p" onChoose={onChoose} />)
    fireEvent.change(container.querySelector('input')!, { target: { value: 'Verantwort' } })
    await until(() => container.textContent!.includes('Verantwortlichkeiten'))
    expect(port.search).toHaveBeenCalledWith('Verantwort', expect.objectContaining({ profile: 'p' }))
    fireEvent.click(screen.getAllByRole('option').find((item) => item.textContent!.includes('Verantwortlichkeiten'))!)
    expect(onChoose.mock.calls[0]![0]).toEqual({ act: 'Verordnung (EU) 2021/1060', article: '69' })
  })

  it('keeps legacy free text and splits it into structured entries on request', () => {
    const onUpdate = vi.fn()
    const { container } = render(<LegalBasisEditor items={[{ text: 'Art. 74 VO (EU) 2021/1060; interne Weisung' }]} onUpdate={onUpdate} />)
    expect(container.textContent).toContain('Altbestand')
    fireEvent.click(container.querySelector('.fa-list-editor__toggle')!)
    fireEvent.click(container.querySelector('.fa-list-editor__form .fa-btn')!)
    const updated = onUpdate.mock.calls[0]![0] as LegalBasis[]
    expect(updated[0]).toMatchObject({ article: '74' })
    expect(updated.at(-1)).toEqual({ text: 'interne Weisung' })
  })

  it('ignores duplicates and removes entries', () => {
    const onUpdate = vi.fn()
    const { container } = render(<LegalBasisEditor items={[{ act: 'Verordnung (EU) 2021/1060', article: '74' }]} port={new ProfileLegalSearch(null)} onUpdate={onUpdate} />)
    fireEvent.change(container.querySelector('input')!, { target: { value: 'Art. 74 VO (EU) 2021/1060' } })
    fireEvent.click(screen.getAllByRole('option')[0]!)
    expect(onUpdate).not.toHaveBeenCalled()
    fireEvent.click(container.querySelector('.fa-list-editor__row .fa-icon-btn')!)
    expect(onUpdate.mock.calls[0]![0]).toEqual([])
  })
})

describe('MarkerPicker', () => {
  it('toggles markers, reports the marker colour and commits the text', () => {
    const onUpdate = vi.fn()
    const onColor = vi.fn()
    const markers: Marker[] = [{ type: 'pruefpunkt' }]
    const { container } = render(<MarkerPicker markers={markers} onUpdate={onUpdate} onColor={onColor} />)
    fireEvent.click(screen.getByRole('button', { name: /^Feststellung$/ }))
    expect(onUpdate.mock.calls[0]![0]).toEqual([{ type: 'pruefpunkt' }, { type: 'feststellung' }])
    expect(onColor).toHaveBeenCalled()
    const text = container.querySelector<HTMLInputElement>('.fa-markers__text input')!
    fireEvent.change(text, { target: { value: ' P-1 ' } })
    fireEvent.blur(text)
    expect(onUpdate.mock.calls.at(-1)![0]).toEqual([{ type: 'pruefpunkt', text: 'P-1' }])
  })
})

describe('PropertiesPanel', () => {
  it('asks for a selection when nothing is selected', () => {
    const { container } = renderInContext(<PropertiesPanel comments={[]} author="" onCommentsChange={vi.fn()} />)
    expect(container.querySelector('.fa-props__empty')!.textContent).toBeTruthy()
    expect(container.querySelector('[role="tablist"]')).toBeNull()
  })
})
