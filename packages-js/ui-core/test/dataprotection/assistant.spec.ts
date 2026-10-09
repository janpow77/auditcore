import { RestError } from '@auditcore/common'
import { describe, expect, it, vi } from 'vitest'
import {
  assistantView,
  createAssistantController,
  createAssistantRestPort,
  dataprotectionMessages,
  questionOptions,
  stepReachable,
  translator,
} from '../../src'
import { activityId, fakeAssistantPort, fresh, suggested } from './fake-assistant-port'

const t = translator(dataprotectionMessages, 'de')

function controllerFor(port = fakeAssistantPort()) {
  return { port, controller: createAssistantController({ port: () => port, activityId: () => activityId, t: () => t }) }
}

describe('Datenschutz-Assistent (Kern)', () => {
  it('startet geführt bei W01 und kennt den nächsten Schritt', async () => {
    const { controller } = controllerFor()
    await controller.load()
    const view = assistantView(controller.store.get())
    expect(view.mode).toBe('gefuehrt')
    expect(view.step?.id).toBe('W01')
    expect(view.next).toBe('W02')
    expect(stepReachable(view, 1)).toBe(true)
    expect(stepReachable(view, 5)).toBe(false)
    expect(view.steps.map((step) => step.id)).not.toContain('W10') // erst bei DSFA-Pflicht
  })

  it('speichert eine Antwort mit Registerrevision und übernimmt den Serverstand', async () => {
    const { controller, port } = controllerFor()
    await controller.load()
    controller.setDraft('W01-02', { value: 'unklar', justification: '' })
    expect(await controller.answer('W01-02')).toBe(true)
    expect(port.answer).toHaveBeenCalledWith(activityId, 'W01-02', 'unklar', '', fresh.register.revision)
    expect(controller.store.get().drafts).toEqual({})
    const tasks = controller.store.get().overview?.assistent.tasks ?? []
    expect(tasks).toContainEqual({ step: 'W01', question: 'W01-02', kind: 'unklar' })
    expect(tasks).toContainEqual({ step: 'W01', question: 'W01-03', kind: 'unbestaetigt' })
  })

  it('behält die Eingabe und meldet den Fehler an der Frage (GUI-08)', async () => {
    const answer = vi.fn(async () => {
      throw new RestError('W01-06: die Antwort „nein“ ist zu begründen.', 422, 'validation_error')
    })
    const { controller } = controllerFor(fakeAssistantPort(fresh, { answer }))
    await controller.load()
    controller.setDraft('W01-06', { value: 'nein', justification: '' })
    expect(await controller.answer('W01-06')).toBe(false)
    const state = controller.store.get()
    expect(state.fieldErrors['W01-06']).toContain('zu begründen')
    expect(state.drafts['W01-06']).toEqual({ value: 'nein', justification: '' })
  })

  it('wechselt in den freien Modus über den Server', async () => {
    const { controller, port } = controllerFor()
    await controller.load()
    await controller.setMode('frei')
    expect(port.navigate).toHaveBeenCalledWith(activityId, 'frei', 'W01', fresh.register.revision)
    const view = assistantView(controller.store.get())
    expect(view.mode).toBe('frei')
    expect(stepReachable(view, 10)).toBe(true)
  })

  it('bietet „unklar“ an und „nicht anwendbar“ nur, wo vorgesehen', () => {
    const question = suggested.assistent.steps[0]!.questions.find((entry) => entry.id === 'W01-06')!
    expect(questionOptions(t, question).map((option) => option.key)).toEqual(['ja', 'nein', 'unklar'])
  })
})

describe('REST-Port des Assistenten', () => {
  it('bildet Antworten, Navigation und Prüfpunkte auf die Pfade ab', async () => {
    const fetch = vi.fn(async () => new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }))
    const port = createAssistantRestPort({ baseUrl: '/api', fetch })
    await port.workspace('t 1')
    await port.answer('t 1', 'W09:x', 'ja', '', 2)
    await port.navigate('t 1', 'frei', 'W03', 3)
    await port.checklist('t 1', 'CHK-16', { status: 'zur_pruefung' }, 4)
    expect(fetch.mock.calls.map((call) => (call as unknown as [string])[0])).toEqual([
      '/api/activities/t%201/workspace',
      '/api/activities/t%201/answers',
      '/api/activities/t%201/navigate',
      '/api/activities/t%201/checklist/CHK-16',
    ])
  })
})
