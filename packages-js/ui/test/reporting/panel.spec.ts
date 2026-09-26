import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import ReportExportPanel from '../../src/reporting/ReportExportPanel.vue'
import { fakeReportingPort, reportingPreview, reportingTables } from '../../../ui-core/test/reporting/fake-port'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('ReportExportPanel', () => {
  it('zeigt Spaltenformate und erste Zeilen der Vorschau', async () => {
    const port = fakeReportingPort()
    const wrapper = mount(ReportExportPanel, { props: { port, tables: reportingTables, filename: 'Vorhabenliste' } })
    await flushPromises()
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(port.calls.preview).toEqual([{ profile: 'flowlib-legacy-v1', tables: reportingTables, filename: 'Vorhabenliste' }])
    expect(wrapper.get('[data-testid="report-columns"]').text()).toContain('#,##0.00 "EUR"')
    expect(wrapper.get('[data-testid="report-sample"]').text()).toContain('=1+1')
    expect(wrapper.emitted('preview-completed')?.[0]).toEqual([reportingPreview])
  })

  it('exportiert, meldet die Datei und Fehler', async () => {
    const wrapper = mount(ReportExportPanel, { props: { port: fakeReportingPort(), tables: reportingTables } })
    await flushPromises()
    await wrapper.get('[data-testid="report-export"]').trigger('click')
    await flushPromises()
    const [file] = wrapper.emitted('export-completed')?.[0] as [{ filename: string }]
    expect(file.filename).toBe('bericht.xlsx')
    expect(wrapper.get('[data-testid="report-status"]').text()).toBe('Exportiert: bericht.xlsx')
    await wrapper.setProps({ port: fakeReportingPort('exportWorkbook') })
    await flushPromises()
    await wrapper.get('[data-testid="report-export"]').trigger('click')
    await flushPromises()
    expect(wrapper.emitted('error')?.[0]).toEqual(['Dienst nicht erreichbar'])
  })

  it('verlangt ein Formatprofil und markiert veraltete Vorschauen', async () => {
    const port = fakeReportingPort()
    const wrapper = mount(ReportExportPanel, { props: { port, tables: reportingTables } })
    await flushPromises()
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    await wrapper.setProps({ tables: [...reportingTables] })
    expect(wrapper.find('[data-testid="report-stale"]').exists()).toBe(true)
    await wrapper.get('[data-testid="report-profile"]').setValue('')
    await wrapper.get('form').trigger('submit')
    expect(wrapper.get('[role="alert"]').text()).toBe('Formatprofil wählen.')
    expect(port.calls.preview).toHaveLength(1)
  })
})
