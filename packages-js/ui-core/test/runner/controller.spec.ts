import { describe, expect, it, vi } from 'vitest'
import {
  createRunnerController,
  createRunnerMemoryPort,
  createRunnerRestPort,
  runnerAbschnitte,
  runnerEingabe,
  runnerFeldId,
  runnerKlassenZeilen,
  runnerPrioritaetZeilen,
  runnerUnterschiede,
  runnerWeichtZuerstText,
  runnerWerkzeugGruppen,
  translator,
  runnerMessages,
  type RunnerPort,
} from '../../src'
import { runnerBeispielPort, runnerProfilBeispiel, runnerStandBeispiel, runnerStatusBeispiel, runnerWerkzeugeBeispiel } from '../parity/cases-runner'

const t = translator(runnerMessages, 'de')

async function geladen(port: RunnerPort = runnerBeispielPort()) {
  const controller = createRunnerController({ port: () => port })
  await controller.load()
  return controller
}

describe('Runner-Konsole: Laden und Status', () => {
  it('lädt Status, Profil und Werkzeuge; Entwurf = gespeicherter Stand', async () => {
    const controller = await geladen()
    const state = controller.store.get()
    expect(state.status?.rechner).toBe('beispiel-rechner')
    expect(state.entwurf).toEqual(runnerProfilBeispiel)
    expect(runnerKlassenZeilen(state.status).map((z) => [z.name, z.soll, z.belegt])).toEqual([['cpu', '2', '1'], ['gpu', '0', '0']])
  })

  it('ohne Port geschieht nichts; mit `api` wird der REST-Port genutzt', async () => {
    const leer = createRunnerController({ port: () => null })
    await leer.load()
    expect(leer.store.get().status).toBeNull()
    const fetch = vi.fn(async (url: string) => {
      const body = url.endsWith('/status') ? runnerStatusBeispiel : url.endsWith('/profil') ? runnerStandBeispiel : runnerWerkzeugeBeispiel
      return new Response(JSON.stringify(body), { status: 200 })
    })
    vi.stubGlobal('fetch', fetch)
    const controller = createRunnerController({ port: () => null, api: () => '/api' })
    await controller.load()
    expect(fetch.mock.calls.map(([url]) => url)).toEqual(['/api/status', '/api/profil', '/api/werkzeuge'])
    expect(controller.store.get().status?.ziel).toBe('besitzer/repo')
    vi.unstubAllGlobals()
  })
})

describe('Runner-Konsole: Einstellungen', () => {
  it('Felder nur für vorhandene Profilwerte; Fehler des Backends am Feld', async () => {
    const port = createRunnerMemoryPort({
      status: runnerStatusBeispiel,
      profil: runnerStandBeispiel,
      pruefen: () => ({ gueltig: false, probleme: [{ feld: 'klassen.cpu.max_instanzen', meldung: 'zu groß' }], aktive_version: 3, aenderungen: [], schritte: [], netzsperre_befehl: null }),
    })
    const controller = await geladen(port)
    controller.setze(['klassen', 'cpu', 'max_instanzen'], 99)
    await controller.pruefen()
    const abschnitte = runnerAbschnitte(controller.store.get(), t)
    expect(abschnitte.map((a) => a.id)).toEqual(['allgemein', 'regelung', 'thermik', 'netz', 'klasse-cpu', 'klasse-gpu', 'karte-0'])
    const max = abschnitte.find((a) => a.id === 'klasse-cpu')?.felder.find((f) => f.id === 'klassen.cpu.max_instanzen')
    expect(max).toMatchObject({ wert: '99', fehler: 'zu groß' })
    expect(abschnitte.find((a) => a.id === 'karte-0')?.felder[1]?.optionen.map((o) => o.wert)).toEqual(['cpu', 'gpu'])
  })

  it('Rohtext bleibt beim Tippen erhalten, der Entwurf bekommt den umgesetzten Wert', async () => {
    const controller = await geladen()
    controller.eingabe(['klassen', 'cpu', 'labels'], 'liste', 'a, ')
    expect(runnerAbschnitte(controller.store.get(), t).find((a) => a.id === 'klasse-cpu')?.felder.find((f) => f.id === 'klassen.cpu.labels')?.wert).toBe('a, ')
    expect(controller.store.get().entwurf?.klassen).toMatchObject({ cpu: { labels: ['a'] } })
    controller.werkzeugZahl('pr', 'ruff', 'zeitlimit_s', '')
    expect(runnerWerkzeugGruppen(controller.store.get(), t)[0]?.zeilen[1]?.zeitlimit).toBe('')
    expect(controller.store.get().werkzeugEntwurf?.pr?.ruff?.zeitlimit_s).toBe(120)
  })

  it('Fehlerpfade des Backends mit Listenindex landen am Feld', async () => {
    const port = createRunnerMemoryPort({
      status: runnerStatusBeispiel,
      profil: runnerStandBeispiel,
      pruefen: () => ({ gueltig: false, probleme: [{ feld: 'gpus[0].erlaubt', meldung: 'Karte fehlt' }], aktive_version: 3, aenderungen: [], schritte: [], netzsperre_befehl: null }),
    })
    const controller = await geladen(port)
    await controller.pruefen()
    const karte = runnerAbschnitte(controller.store.get(), t).find((a) => a.id === 'karte-0')
    expect(karte?.felder.find((f) => f.id === 'gpus.0.erlaubt')?.fehler).toBe('Karte fehlt')
    expect(runnerFeldId('klassen.cpu.labels[2]')).toBe('klassen.cpu.labels.2')
  })

  it('Eingaben: Zahl, Liste, Schalter', () => {
    expect(runnerEingabe('zahl', '0,5')).toBe(0.5)
    expect(runnerEingabe('zahl', 'x')).toBe('x')
    expect(runnerEingabe('liste', 'a, b,,c')).toEqual(['a', 'b', 'c'])
    expect(runnerEingabe('schalter', true)).toBe(true)
  })

  it('Anwenden erhöht die Version und meldet Erfolg; Verwerfen stellt den Stand her', async () => {
    const applied = vi.fn()
    const port = runnerBeispielPort()
    const controller = createRunnerController({ port: () => port, callbacks: () => ({ applied }) })
    await controller.load()
    controller.setze(['reserve', 'cpus'], 6)
    controller.verwerfen()
    expect(controller.store.get().entwurf).toEqual(runnerProfilBeispiel)
    controller.setze(['reserve', 'cpus'], 6)
    await controller.anwenden()
    expect(applied).toHaveBeenCalledWith(4)
    expect(controller.store.get().meldung).toMatchObject({ key: 'angewendet', params: { version: 4 } })
    expect(controller.store.get().stand?.profil.version).toBe(4)
  })

  it('Konflikt: beide Stände mit Unterschieden, dann Entwurf trotzdem anwenden', async () => {
    const port = runnerBeispielPort()
    const controller = await geladen(port)
    await port.anwenden({ ...runnerProfilBeispiel, image: 'anderes:tag' }, 3)
    controller.setze(['reserve', 'cpus'], 6)
    await controller.anwenden()
    const konflikt = controller.store.get().konflikt
    expect(konflikt?.unterschiede.map((u) => u.pfad)).toEqual(['image', 'reserve.cpus'])
    await controller.entwurfTrotzdemAnwenden()
    expect(controller.store.get().konflikt).toBeNull()
    expect(controller.store.get().stand?.profil.version).toBe(5)
  })

  it('Unterschiede ignorieren Version und Änderungsvermerk', () => {
    expect(runnerUnterschiede({ ...runnerProfilBeispiel, version: 9, aenderung: {} }, runnerProfilBeispiel)).toEqual([])
  })
})

describe('Runner-Konsole: Prioritäten und Werkzeuge', () => {
  it('verschiebt Einträge mit fortlaufenden Rängen und nennt, wer zuerst weicht', async () => {
    const controller = await geladen()
    controller.verschiebe(0, 1)
    const zeilen = runnerPrioritaetZeilen(controller.store.get(), t)
    expect(zeilen.map((z) => [z.klasse, z.rang])).toEqual([['gpu', 1], ['cpu', 2]])
    controller.prioritaet(0, { verdraengbar: false })
    expect(runnerWeichtZuerstText(controller.store.get(), t)).toBe('Kein Eintrag ist verdrängbar.')
  })

  it('ändert und speichert Werkzeug-Einstellungen', async () => {
    const controller = await geladen()
    controller.werkzeug('pr', 'mypy', { aktiv: false, zeitlimit_s: 300 })
    const gruppe = runnerWerkzeugGruppen(controller.store.get(), t)[0]
    expect(gruppe?.zeilen.map((z) => [z.werkzeug, z.aktiv, z.zeitlimit, z.imImage])).toEqual([['mypy', false, '300', 'nicht installiert'], ['ruff', true, '120', '0.16.0']])
    await controller.werkzeugeSpeichern()
    expect(controller.store.get().meldung?.key).toBe('gespeichert')
  })
})

describe('REST-Port der Runner-API', () => {
  it('sendet die Schreib-Kopfzeile und macht aus 409 einen Konflikt mit der Meldung des Servers', async () => {
    const fetch = vi.fn(async (_url: string, init?: RequestInit) => {
      expect(new Headers(init?.headers).get('X-Auditcore-Runner')).toBe('1')
      return new Response(JSON.stringify({ fehler: 'Profil wurde inzwischen geändert' }), { status: 409 })
    })
    const port = createRunnerRestPort({ baseUrl: '/api', fetch })
    const ergebnis = await port.anwenden(runnerProfilBeispiel, 3)
    expect(ergebnis).toMatchObject({ konflikt: true, angewendet: false, meldung: 'Profil wurde inzwischen geändert' })
    expect(JSON.parse(String(fetch.mock.calls[0]?.[1]?.body))).toEqual({ profil: runnerProfilBeispiel, erwartete_version: 3 })
  })

  it('übersetzt `fehler` des Servers in eine lesbare Fehlermeldung', async () => {
    const fetch = vi.fn(async () => new Response(JSON.stringify({ fehler: 'kein gültiges JSON' }), { status: 400 }))
    const port = createRunnerRestPort({ baseUrl: '/api', fetch })
    await expect(port.pruefen(runnerProfilBeispiel)).rejects.toThrow('kein gültiges JSON')
  })

  it('speichert Werkzeuge mit Schema', async () => {
    const fetch = vi.fn(async (_url: string, _init?: RequestInit) => new Response(JSON.stringify({ gespeichert: true }), { status: 200 }))
    await createRunnerRestPort({ baseUrl: '/api/', fetch }).werkzeugeSpeichern(runnerWerkzeugeBeispiel.profile)
    expect(fetch.mock.calls[0]?.[0]).toBe('/api/werkzeuge')
    expect(JSON.parse(String(fetch.mock.calls[0]?.[1]?.body))).toMatchObject({ schema: 'auditcore-runner/werkzeuge/1' })
  })
})
