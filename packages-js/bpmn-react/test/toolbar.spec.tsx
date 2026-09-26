import { describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach } from 'vitest'
import { hasIcon } from '@auditcore/bpmn-flowaudit'
import { CORE_ENTRY_ICONS, EDIT_ACTIONS, FILE_ACTIONS, readPaletteEntries, TABS, VIEW_ACTIONS } from '@auditcore/bpmn-flowaudit/ui'
import { EditorToolbar, type EditorToolbarProps } from '../src/toolbar/EditorToolbar'
import { ToolPalette } from '../src/palette/ToolPalette'
import { FaIcon } from '../src/base/FaIcon'
import { ColorSwatches } from '../src/base/ColorSwatches'
import { StatusBar } from '../src/canvas/CanvasParts'

afterEach(cleanup)

const toolbarProps = (extra: Partial<EditorToolbarProps> = {}): EditorToolbarProps => ({ name: 'Muster', dirty: true, saving: false, readonly: false, canUndo: true, canRedo: false, direction: 'waagerecht', pageView: 'aus', active: {}, onAction: vi.fn(), ...extra })

describe('icons', () => {
  it('exist for every toolbar action, palette entry and tab', () => {
    const names = [...FILE_ACTIONS, ...EDIT_ACTIONS, ...VIEW_ACTIONS].map((entry) => entry.icon).concat(Object.values(CORE_ENTRY_ICONS), TABS.map((tab) => tab.icon))
    expect(names.filter((name) => !hasIcon(name))).toEqual([])
  })

  it('renders decorative icons hidden and labelled icons as images', () => {
    const { container } = render(<><FaIcon name="save" /><FaIcon name="save" label="Speichern" /></>)
    const [plain, labelled] = Array.from(container.querySelectorAll('svg'))
    expect(plain!.getAttribute('aria-hidden')).toBe('true')
    expect(labelled!.getAttribute('role')).toBe('img')
    expect(labelled!.getAttribute('aria-label')).toBe('Speichern')
    expect(plain!.querySelector('[stroke-width], path, rect, circle')).not.toBeNull()
  })
})

describe('EditorToolbar', () => {
  it('reports actions, renames on leaving the field and disables undo/redo by state', () => {
    const onAction = vi.fn()
    const onNameChange = vi.fn()
    const { container } = render(<EditorToolbar {...toolbarProps({ onAction, onNameChange })} />)
    expect(container.textContent).toContain('ungespeichert')
    fireEvent.click(container.querySelector('.fa-btn--primary')!)
    expect(onAction).toHaveBeenCalledWith('save')
    const name = container.querySelector<HTMLInputElement>('.fa-toolbar__name')!
    fireEvent.change(name, { target: { value: 'Neu' } })
    expect(onNameChange).not.toHaveBeenCalled()
    fireEvent.blur(name)
    expect(onNameChange).toHaveBeenCalledWith('Neu')
    expect(screen.getByLabelText('Wiederholen').hasAttribute('disabled')).toBe(true)
  })

  it('blocks writing actions when read-only and hides configured actions', () => {
    const { container } = render(<EditorToolbar {...toolbarProps({ readonly: true, hidden: ['export'] })} />)
    expect(container.querySelector('.fa-btn--primary')!.hasAttribute('disabled')).toBe(true)
    expect(container.querySelector('[aria-label="Exportieren"]')).toBeNull()
  })

  it('opens the check menu, runs an entry and closes it with Escape', () => {
    const onAction = vi.fn()
    render(<EditorToolbar {...toolbarProps({ onAction })} />)
    fireEvent.click(screen.getByRole('button', { name: 'Prüfen' }))
    fireEvent.click(screen.getAllByRole('menuitem')[0]!)
    expect(onAction).toHaveBeenCalledWith('validate')
    expect(screen.queryByRole('menu')).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Prüfen' }))
    fireEvent.keyDown(screen.getByRole('menu'), { key: 'Escape' })
    expect(screen.queryByRole('menu')).toBeNull()
  })

  it('reports direction, page view and imported files', () => {
    const onDirection = vi.fn()
    const onPageView = vi.fn()
    const onImportFile = vi.fn()
    const { container } = render(<EditorToolbar {...toolbarProps({ onDirection, onPageView, onImportFile })} />)
    fireEvent.click(screen.getByLabelText(/^Senkrecht/))
    fireEvent.change(container.querySelector('select')!, { target: { value: 'a4-quer' } })
    const file = new File(['<x/>'], 'prozess.bpmn')
    fireEvent.change(container.querySelector('input[type="file"]')!, { target: { files: [file] } })
    expect(onDirection).toHaveBeenCalledWith('senkrecht')
    expect(onPageView).toHaveBeenCalledWith('a4-quer')
    expect(onImportFile).toHaveBeenCalledWith(file)
  })
})

describe('palette', () => {
  it('triggers entries by click and hides empty sections', () => {
    const onTrigger = vi.fn()
    const { container } = render(<ToolPalette items={readPaletteEntries({ 'create.task': { group: 'activity', title: 'Aufgabe' } })} onTrigger={onTrigger} />)
    fireEvent.click(container.querySelector('button')!)
    expect(onTrigger.mock.calls[0]![0]).toBe('create.task')
    expect(container.querySelectorAll('section[style*="none"]')).toHaveLength(2)
  })
})

describe('ColorSwatches', () => {
  it('reports the chosen colour or null for reset', () => {
    const onChoose = vi.fn()
    const color = { id: 'w', fill: '#fff', stroke: '#000', label: 'Weiß', meaning: 'neutral' }
    const { container } = render(<ColorSwatches colors={[color]} onChoose={onChoose} />)
    const buttons = container.querySelectorAll('button')
    fireEvent.click(buttons[0]!)
    fireEvent.click(buttons[buttons.length - 1]!)
    expect(onChoose.mock.calls.map((call) => call[0])).toEqual([color, null])
  })
})

describe('StatusBar', () => {
  it('shows zoom, counts and profile', () => {
    const onIssues = vi.fn()
    const { container } = render(<StatusBar scale={1.25} count={{ fehler: 1, warnung: 2, hinweis: 0 }} profile="p@1" onIssues={onIssues} />)
    expect(container.textContent).toContain('125')
    expect(container.textContent).toContain('p@1')
    fireEvent.click(container.querySelector('button')!)
    expect(onIssues).toHaveBeenCalledTimes(1)
  })
})
