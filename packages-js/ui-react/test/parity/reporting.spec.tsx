import { describe, expect, it } from 'vitest'
import ReportExportPanel from '../../../ui/src/reporting/ReportExportPanel.vue'
import { reportingCases } from '../../../ui-core/test/parity/cases-reporting'
import { fakeReportingPort, reportingTables } from '../../../ui-core/test/reporting/fake-port'
import { FlowauditReportExport } from '../../src/reporting/FlowauditReportExport'
import { byTestId, both } from './interact'
import { expectParity, renderBoth } from './setup'

describe('Parität Tabellenexport Vue ↔ React', () => {
  for (const entry of reportingCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(ReportExportPanel, { ...entry.props() }, <FlowauditReportExport {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

describe('Parität Tabellenexport nach Interaktion', () => {
  it('Vorschau, Profil wechseln (veraltet), Dateiname, Export, Profil abwählen', async () => {
    const vuePort = fakeReportingPort()
    const reactPort = fakeReportingPort()
    const props = { tables: reportingTables, filename: 'Vorhabenliste' }
    const rendered = await renderBoth(ReportExportPanel, { ...props, port: vuePort }, <FlowauditReportExport {...props} port={reactPort} />)
    await both(rendered, byTestId('report-preview'), { kind: 'submit' })
    expect(rendered.react.querySelectorAll('[data-testid="report-columns"] tbody tr')).toHaveLength(5)
    await both(rendered, byTestId('report-profile'), { kind: 'change', value: 'plain-v1' })
    expect(rendered.react.querySelector('[data-testid="report-stale"]')).not.toBeNull()
    await both(rendered, byTestId('report-filename'), { kind: 'input', value: 'Liste 2026' })
    await both(rendered, byTestId('report-export'), { kind: 'click' })
    expect(rendered.react.querySelector('[data-testid="report-status"]')?.textContent).toBe('Exportiert: Liste 2026.xlsx')
    expect(reactPort.calls).toEqual(vuePort.calls)
    await both(rendered, byTestId('report-profile'), { kind: 'change', value: '' })
    await both(rendered, byTestId('report-preview'), { kind: 'submit' })
    expect(rendered.react.querySelector('.fa-report__error')?.textContent).toBe('Formatprofil wählen.')
  })
})
