import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { fakeReportingPort, reportingPreview, reportingTables } from '../../ui-core/test/reporting/fake-port'
import { FlowauditReportExport } from '../src/reporting/FlowauditReportExport'

const flush = () => act(() => new Promise<void>((resolve) => setTimeout(resolve, 0)))

afterEach(() => cleanup())

describe('FlowauditReportExport (nativ)', () => {
  it('zeigt Spaltenformate und erste Zeilen der Vorschau', async () => {
    const port = fakeReportingPort()
    const onPreviewCompleted = vi.fn()
    render(<FlowauditReportExport port={port} tables={reportingTables} filename="Vorhabenliste" onPreviewCompleted={onPreviewCompleted} />)
    await flush()
    fireEvent.submit(screen.getByTestId('report-preview').closest('form') as HTMLFormElement)
    await flush()
    expect(port.calls.preview).toEqual([{ profile: 'flowlib-legacy-v1', tables: reportingTables, filename: 'Vorhabenliste' }])
    const formats = screen.getByRole('table', { name: 'Spaltenformate' })
    expect(formats.textContent).toContain('#,##0.00 "EUR"')
    expect(formats.textContent).toContain('ausdrücklich')
    expect(screen.getByRole('table', { name: 'Erste Zeilen' }).textContent).toContain('=1+1')
    expect(screen.getByTestId('report-workbook').textContent).toMatch(/^Probelauf: Vorhabenliste\.xlsx, /)
    expect(onPreviewCompleted).toHaveBeenCalledWith(reportingPreview)
  })

  it('exportiert und meldet Datei sowie Fehler', async () => {
    const onExportCompleted = vi.fn()
    const onError = vi.fn()
    const { rerender } = render(<FlowauditReportExport port={fakeReportingPort()} tables={reportingTables} onExportCompleted={onExportCompleted} />)
    await flush()
    fireEvent.click(screen.getByTestId('report-export'))
    await flush()
    expect(onExportCompleted.mock.calls[0]?.[0].filename).toBe('bericht.xlsx')
    expect(screen.getByTestId('report-status').textContent).toBe('Exportiert: bericht.xlsx')
    rerender(<FlowauditReportExport port={fakeReportingPort('exportWorkbook')} tables={reportingTables} onError={onError} />)
    await flush()
    fireEvent.click(screen.getByTestId('report-export'))
    await flush()
    expect(onError).toHaveBeenCalledWith('Dienst nicht erreichbar')
    expect(screen.getByRole('alert').textContent).toBe('Anfrage abgelehnt: Dienst nicht erreichbar')
  })

  it('markiert die Vorschau als veraltet, wenn sich die Tabellen ändern', async () => {
    const port = fakeReportingPort()
    const { rerender } = render(<FlowauditReportExport port={port} tables={reportingTables} />)
    await flush()
    fireEvent.submit(screen.getByTestId('report-preview').closest('form') as HTMLFormElement)
    await flush()
    expect(screen.queryByTestId('report-stale')).toBeNull()
    rerender(<FlowauditReportExport port={port} tables={[...reportingTables]} />)
    await flush()
    expect(screen.getByTestId('report-stale')).toBeTruthy()
  })
})
