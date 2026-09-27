import { describe, expect, it } from 'vitest'
import ReportTemplates from '../../../ui/src/reporttemplates/ReportTemplates.vue'
import { reporttemplatesCases } from '../../../ui-core/test/parity/cases-reporttemplates'
import { fakeTemplatesPort } from '../../../ui-core/test/reporttemplates/fake-port'
import { FlowauditReportTemplates } from '../../src/reporttemplates/FlowauditReportTemplates'
import { both, byTestId } from './interact'
import { expectParity, renderBoth } from './setup'

describe('Parität Berichtsvorlagen Vue ↔ React', () => {
  for (const entry of reporttemplatesCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(ReportTemplates, { ...entry.props() }, <FlowauditReportTemplates {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

describe('Parität Berichtsvorlagen nach Interaktion', () => {
  it('Vorschau, Vorlage wechseln, ungültige Daten, Format ohne Extra, Bericht', async () => {
    const vuePort = fakeTemplatesPort({ pdf: false })
    const reactPort = fakeTemplatesPort({ pdf: false })
    const rendered = await renderBoth(ReportTemplates, { port: vuePort, filename: 'Bericht' }, <FlowauditReportTemplates port={reactPort} filename="Bericht" />)
    await both(rendered, byTestId('template-preview-button'), { kind: 'submit' })
    expect(rendered.react.querySelector('iframe')?.getAttribute('sandbox')).toBe('')
    expect(rendered.react.querySelector('[data-testid="template-preview"]')?.textContent).toContain('Verwendete Textbausteine: rechtsgrundlage')
    await both(rendered, byTestId('template-format'), { kind: 'change', value: 'pdf' })
    expect(rendered.react.querySelector('[role="alert"]')?.textContent).toBe('Format „PDF“ auf dem Server nicht verfügbar.')
    await both(rendered, byTestId('template-format'), { kind: 'change', value: 'html' })
    await both(rendered, byTestId('template-render'), { kind: 'click' })
    expect(rendered.react.querySelector('[data-testid="template-status"]')?.textContent).toBe('Erzeugt: Bericht.html')
    await both(rendered, byTestId('template-select'), { kind: 'change', value: 'vermerk' })
    expect(rendered.react.querySelector('[data-testid="template-preview"]')).toBeNull()
    expect(reactPort.calls).toEqual(vuePort.calls)
  })

  it('ungültige Daten zeigen alle Pfade', async () => {
    const data = { aktenzeichen: 'AZ-1' }
    const rendered = await renderBoth(ReportTemplates, { port: fakeTemplatesPort(), data }, <FlowauditReportTemplates port={fakeTemplatesPort()} data={data} />)
    await both(rendered, byTestId('template-preview-button'), { kind: 'submit' })
    expect(rendered.react.querySelectorAll('.fa-reporttemplates__issues li')).toHaveLength(5)
    expect(rendered.react.querySelector('iframe')).toBeNull()
  })
})
