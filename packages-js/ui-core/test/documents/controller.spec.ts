import { describe, expect, it, vi } from 'vitest'
import { RestError } from '@auditcore/common'
import { createComparisonsController, type ComparisonsPort } from '../../src/documents/controller'
import { comparisonsView } from '../../src/documents/view'
import { created, errors, fakePort, file, imported, summaries, t } from './fake-port'

function setup(port: ComparisonsPort | null = fakePort(), maxBytes = 20 * 1024 * 1024) {
  const hooks = { onCreated: vi.fn(), onImported: vi.fn(), onRemoved: vi.fn(), onError: vi.fn() }
  const controller = createComparisonsController({ port: () => port, t: () => t, maxBytes: () => maxBytes, lang: () => 'de', ...hooks })
  const view = () => comparisonsView(controller.store.get(), t, { lang: 'de', maxBytes })
  return { controller, hooks, view }
}

describe('Zustandsautomat der Vergleichsverwaltung', () => {
  it('lädt Profile und Liste und bietet das Standardprofil als Vorgabe an', async () => {
    const { controller, view } = setup()
    expect(view().emptyText).toBeNull()
    await controller.load()
    expect(view().rows).toHaveLength(summaries.length)
    expect(view().countText).toBe(`${summaries.length} von ${summaries.length} Vergleichen`)
    expect(view().profileOptions.map((option) => option.value)).toEqual(['audit_designer.document_compare', 'audit_designer.document_compare.difflib', ''])
    expect(view().profileOptions[2]?.label).toBe('auditcore.document_compare 2026.09.2 (Vorgabe)')
    controller.setQuery('gibt es nicht')
    expect(view().emptyText).toBe('Kein Vergleich passt zur Suche.')
  })

  it('zeigt Befunde erst nach dem Absenden und lädt nichts hoch, solange sie bestehen', async () => {
    const port = fakePort()
    const { controller, view } = setup(port, 1024)
    expect(view().problems).toEqual([])
    controller.updateForm({ oldFile: file('alt.docx', 4096) })
    expect(await controller.submit()).toBeNull()
    expect(view().problems.map((problem) => problem.text)).toEqual(['alt.docx ist größer als 1 KiB.', 'Die neue Fassung fehlt.'])
    expect(port.create).not.toHaveBeenCalled()
  })

  it('legt einen Vergleich an, setzt das Formular zurück und meldet ihn', async () => {
    const port = fakePort({ list: vi.fn(async () => []) })
    const { controller, hooks, view } = setup(port)
    await controller.load()
    expect(view().emptyText).toBe('Noch keine Vergleiche gespeichert.')
    controller.updateForm({ oldFile: file('alt.docx'), newFile: file('neu.pdf'), title: 'Richtlinie' })
    expect(view().pdfHint).toBe(true)
    expect(view().oldFileText).toBe('Ausgewählt: alt.docx (10 B)')
    expect(await controller.submit()).toBe(created)
    expect(port.create).toHaveBeenCalledWith(expect.any(File), 'alt.docx', expect.any(File), 'neu.pdf', expect.objectContaining({ title: 'Richtlinie', mode: 'auto' }))
    expect(hooks.onCreated).toHaveBeenCalledWith(created)
    expect(controller.store.get().form.oldFile).toBeNull()
    expect(view().rows.map((row) => row.id)).toEqual([created.id])
    expect(controller.store.get().notice).toBe(`„${created.title}“ wurde angelegt.`)
  })

  it('übernimmt die Fehlermeldung des Servers', async () => {
    const detail = errors.unsupported_type.body.detail
    const port = fakePort({ create: vi.fn(async () => Promise.reject(new RestError(detail, 415, 'http_error'))) })
    const { controller, hooks } = setup(port)
    controller.updateForm({ oldFile: file('a.docx'), newFile: file('b.docx') })
    expect(await controller.submit()).toBeNull()
    expect(controller.store.get().error).toEqual({ code: 'http_error', message: detail, status: 415 })
    expect(hooks.onError).toHaveBeenCalledOnce()
    expect(controller.store.get().busy).toBeNull()
  })

  it('meldet Netzfehler verständlich', async () => {
    const { controller } = setup(fakePort({ list: vi.fn(async () => Promise.reject(new TypeError('Failed to fetch'))) }))
    await controller.load()
    expect(controller.store.get().error?.message).toBe('Keine Verbindung zum Server (Failed to fetch).')
  })

  it('importiert ein Ergebnis und weist ungültige Dateien vor dem Senden ab', async () => {
    const port = fakePort()
    const { controller, hooks } = setup(port)
    expect(await controller.importText('kein json')).toBeNull()
    expect(controller.store.get().error?.message).toBe('Die Datei ist kein gültiges JSON.')
    expect(await controller.importText(JSON.stringify({ title: 'Import', result: created.result }))).toBe(imported)
    expect(port.importResult).toHaveBeenCalledWith({ title: 'Import', result: created.result })
    expect(hooks.onImported).toHaveBeenCalledWith(imported)
    expect(controller.store.get().error).toBeNull()
    const { importResult: _unused, ...withoutImport } = fakePort()
    const limited = setup(withoutImport)
    expect(await limited.controller.importText(JSON.stringify(created.result))).toBeNull()
    expect(limited.controller.store.get().error?.message).toBe('Der Port unterstützt keinen Import.')
  })

  it('löscht erst nach Bestätigung und schließt einen geöffneten Vergleich', async () => {
    const port = fakePort()
    const { controller, hooks, view } = setup(port)
    await controller.load()
    const target = summaries[0]!
    controller.open(target.id)
    expect(view().openTitle).toBe(target.title)
    expect(await controller.confirmRemove()).toBe(false)
    controller.askRemove(target.id)
    expect(view().pendingTitle).toBe(target.title)
    controller.cancelRemove()
    expect(view().pendingTitle).toBeNull()
    controller.askRemove(target.id)
    expect(await controller.confirmRemove()).toBe(true)
    expect(port.remove).toHaveBeenCalledWith(target.id)
    expect(hooks.onRemoved).toHaveBeenCalledWith(target.id)
    expect(controller.store.get()).toMatchObject({ openId: null, pendingRemove: null, notice: `„${target.title}“ wurde gelöscht.` })
    expect(view().rows).toHaveLength(summaries.length - 1)
  })

  it('bleibt ohne Port untätig und passt die Dateibeschriftung der Gesetzessynopse an', async () => {
    const { controller, view } = setup(null)
    await controller.load()
    expect(controller.store.get().loaded).toBe(false)
    controller.updateForm({ kind: 'article_law', oldFile: file('a.pdf') })
    expect(view()).toMatchObject({ oldFileLabel: 'Stammgesetz (geltende Fassung)', newFileLabel: 'Artikelgesetz mit Änderungsbefehlen', pdfHint: false })
    controller.toggleSection('unchanged', true)
    expect(controller.store.get().form.sections).toContain('unchanged')
    controller.resetForm()
    expect(controller.store.get().form.kind).toBe('standard')
  })
})
