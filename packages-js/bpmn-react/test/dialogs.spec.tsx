import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { issue, type DiagramInfo, type ExportChoice, type Suggestion } from '@auditcore/bpmn-flowaudit'
import { BaseDialog } from '../src/base/BaseDialog'
import { DiagramInfoDialog } from '../src/dialogs/DiagramInfoDialog'
import { EnrichmentDialog } from '../src/dialogs/EnrichmentDialog'
import { ExportDialog } from '../src/dialogs/ExportDialog'
import { XmlDialog } from '../src/dialogs/XmlDialog'
import { IssueList } from '../src/views/IssueList'
import { KeyFilterBar } from '../src/views/KeyFilterBar'
import { renderInContext } from './context'

afterEach(cleanup)

const INFO: DiagramInfo = { title: 'Bewilligung', status: 'entwurf', version: '1.0', funds: ['efre'] }
const button = (container: HTMLElement, text: string) => Array.from(container.querySelectorAll('button')).find((item) => item.textContent?.includes(text))!
const noop = () => undefined

describe('BaseDialog', () => {
  it('closes with Escape and via the close button', () => {
    const onOpenChange = vi.fn()
    render(<BaseDialog open title="Titel" onOpenChange={onOpenChange}><input /></BaseDialog>)
    const dialog = screen.getByRole('dialog')
    expect(dialog.getAttribute('aria-labelledby')).toBeTruthy()
    fireEvent.keyDown(dialog, { key: 'Escape' })
    fireEvent.click(dialog.querySelector('.fa-icon-btn')!)
    expect(onOpenChange).toHaveBeenLastCalledWith(false)
    expect(onOpenChange).toHaveBeenCalledTimes(2)
  })
})

describe('DiagramInfoDialog', () => {
  it('edits a draft and applies it (funds as toggle chips)', () => {
    const onApply = vi.fn()
    const { container } = renderInContext(<DiagramInfoDialog open info={INFO} profiles={[{ id: 'p', version: '1', title: 'Profil' }]} fallbackTitle="Datei" onOpenChange={noop} onApply={onApply} />)
    expect(container.querySelector('.fa-info-preview')!.textContent).toContain('Bewilligung')
    const title = container.querySelector<HTMLInputElement>('.fa-info-section input')!
    fireEvent.change(title, { target: { value: 'Bewilligung und Auszahlung' } })
    fireEvent.blur(title)
    fireEvent.click(container.querySelector('.fa-chip[aria-pressed="true"]')!)
    fireEvent.click(button(container, 'Übernehmen'))
    expect(onApply.mock.calls[0]![0]).toMatchObject({ title: 'Bewilligung und Auszahlung', funds: [] })
    expect(INFO.title).toBe('Bewilligung')
  })

  it('offers approval and a new version and shows the recorded hash', () => {
    const onApprove = vi.fn()
    const onNewVersion = vi.fn()
    const approvals = [{ version: '1.0', sha256: 'a'.repeat(64) }]
    const { container } = renderInContext(<DiagramInfoDialog open info={INFO} profiles={[]} approvals={approvals} fallbackTitle="Datei" onOpenChange={noop} onApprove={onApprove} onNewVersion={onNewVersion} />)
    expect(container.textContent).toContain('a'.repeat(64))
    fireEvent.click(button(container, 'Stand freigeben'))
    fireEvent.click(button(container, 'Neue Version'))
    expect(onApprove).toHaveBeenCalledTimes(1)
    expect(onNewVersion).toHaveBeenCalledTimes(1)
  })

  it('is read-only except for the status section', () => {
    const { container } = renderInContext(<DiagramInfoDialog open info={INFO} profiles={[]} fallbackTitle="Datei" onOpenChange={noop} />, { readonly: true })
    expect(button(container, 'Übernehmen').disabled).toBe(true)
  })
})

describe('ExportDialog', () => {
  const data = { colors: [{ fill: '#fff', stroke: '#000', label: 'Standard', meaning: 'Standard', count: 1 }], markers: [], legalBases: [] }

  it('preselects attachments from the data and emits the choice', () => {
    const onExport = vi.fn<(choice: ExportChoice) => void>()
    const { container } = render(<ExportDialog open defaultTitle="Bewilligung" data={data} onOpenChange={noop} onExport={onExport} />)
    fireEvent.click(button(container, 'PDF'))
    expect(onExport.mock.calls[0]![0]).toMatchObject({ format: 'pdf', title: 'Bewilligung', showLegend: true, showMarkerLegend: false, neutral: false })
  })

  it('suggests the neutral export for confidential diagrams', () => {
    const onExport = vi.fn<(choice: ExportChoice) => void>()
    const { container } = render(<ExportDialog open defaultTitle="X" data={data} confidentiality="vs_nfd" onOpenChange={noop} onExport={onExport} />)
    fireEvent.click(button(container, 'SVG'))
    expect(onExport.mock.calls[0]![0].neutral).toBe(true)
  })
})

describe('EnrichmentDialog', () => {
  const suggestions: Suggestion[] = [
    { id: 's1', elementId: 'T1', kind: 'legalBasis', value: { act: 'Verordnung (EU) 2021/1060', article: '74' }, excerpt: 'Art. 74 CPR', origin: 'documentation' },
    { id: 's2', elementId: 'T1', kind: 'rolePrefix', value: 'ZGS', excerpt: 'ZGS: Antrag prüfen', origin: 'name' },
  ]

  it('accepts all suggestions by default and lets the user reject single ones', () => {
    const onApply = vi.fn()
    const { container } = render(<EnrichmentDialog open suggestions={suggestions} names={{ T1: 'Antrag prüfen' }} onOpenChange={noop} onApply={onApply} />)
    expect(container.textContent).toContain('Antrag prüfen')
    fireEvent.click(container.querySelector('.fa-enrich__item input')!)
    fireEvent.click(container.querySelector('.fa-btn--primary')!)
    const [accepted, removePrefixes] = onApply.mock.calls[0]! as [Suggestion[], boolean]
    expect(accepted.map((s) => s.id)).toEqual(['s2'])
    expect(removePrefixes).toBe(true)
  })
})

describe('XmlDialog', () => {
  it('applies edited XML unless read-only', () => {
    const onApply = vi.fn()
    const { container } = render(<XmlDialog open xml="<a/>" onOpenChange={noop} onApply={onApply} />)
    fireEvent.change(container.querySelector('textarea')!, { target: { value: '<b/>' } })
    fireEvent.click(container.querySelector('.fa-btn--primary')!)
    expect(onApply).toHaveBeenCalledWith('<b/>')
    cleanup()
    const readonly = render(<XmlDialog open xml="<a/>" readonly onOpenChange={noop} onApply={noop} />)
    expect(readonly.container.querySelector('textarea')!.hasAttribute('readonly')).toBe(true)
  })

  it('renders an own editor instead of the text area', () => {
    const { container } = render(<XmlDialog open xml="<a/>" onOpenChange={noop} onApply={noop} renderEditor={(xml) => <pre className="own">{xml}</pre>} />)
    expect(container.querySelector('.own')!.textContent).toBe('<a/>')
    expect(container.querySelector('textarea')).toBeNull()
  })
})

describe('views', () => {
  const issues = [issue('BPMN-S010', 'Process_1', { name: 'Antrag' }), issue('BPMN-F001', 'Task_1', { name: 'Prüfen' })]

  it('IssueList filters by severity and jumps to elements', () => {
    const onJump = vi.fn()
    const { container } = render(<IssueList issues={issues} onJump={onJump} />)
    expect(container.querySelectorAll('.fa-issue')).toHaveLength(2)
    fireEvent.click(container.querySelectorAll('.fa-chip')[1]!)
    expect(container.querySelectorAll('.fa-issue')).toHaveLength(1)
    fireEvent.click(container.querySelector('.fa-issue .fa-btn')!)
    expect(onJump).toHaveBeenCalledWith('Process_1')
  })

  it('KeyFilterBar reports kind, value and clear', () => {
    const onKindChange = vi.fn()
    const onValueChange = vi.fn()
    const onClear = vi.fn()
    const { container } = render(<KeyFilterBar keys={{ ka: { '2': ['T1'] } }} kind="ka" value="" hits={0} onKindChange={onKindChange} onValueChange={onValueChange} onClear={onClear} />)
    fireEvent.change(container.querySelector('select')!, { target: { value: 'bk' } })
    fireEvent.change(container.querySelector('input')!, { target: { value: '2' } })
    fireEvent.click(within(container).getByRole('button'))
    expect(onKindChange).toHaveBeenCalledWith('bk')
    expect(onValueChange).toHaveBeenCalledWith('2')
    expect(onClear).toHaveBeenCalledTimes(1)
  })
})
