// Aktionen der Runner-Konsole, nach Bereich getrennt: Profil-Entwurf (Prüfen,
// Anwenden, Konflikt, Prioritäten) und Werkzeug-Einstellungen.

import type { Store } from '../store'
import type { RunnerController, RunnerData } from './controller'
import { runnerEingabe, runnerWerkzeugFeldId } from './eingabe'
import { runnerPrioritaetSetze, runnerSetze, runnerUnterschiede, runnerVerschiebe, runnerVersion } from './profil'
import type { RunnerPort, RunnerProfil, RunnerProfilStand, RunnerPruefung } from './types'

type Run = <T>(kind: string, task: (port: RunnerPort) => Promise<T>) => Promise<T | null>

export interface RunnerKontext {
  store: Store<RunnerData>
  run: Run
  applied: (version: number) => void
}

type ProfilAktionen = Pick<RunnerController, 'setze' | 'eingabe' | 'verwerfen' | 'pruefen' | 'anwenden' | 'gespeichertUebernehmen' | 'entwurfTrotzdemAnwenden' | 'verschiebe' | 'prioritaet'>
type WerkzeugAktionen = Pick<RunnerController, 'werkzeug' | 'werkzeugZahl' | 'werkzeugeSpeichern'>

function uebernimmStand(store: Store<RunnerData>, stand: RunnerProfilStand): void {
  store.set({ stand, entwurf: stand.profil, pruefung: null, konflikt: null, eingaben: {} })
}

/** Entwurf ändern; eine alte Prüfung und Rückmeldung gelten danach nicht mehr. */
function aendere(store: Store<RunnerData>, aenderung: (entwurf: RunnerProfil) => RunnerProfil): void {
  const entwurf = store.get().entwurf
  if (entwurf) store.set({ entwurf: aenderung(entwurf), pruefung: null, meldung: null })
}

async function konfliktLaden({ store, run }: RunnerKontext, entwurf: RunnerProfil, ergebnis: RunnerPruefung): Promise<void> {
  const gespeichert = await run('anwenden', (port) => port.profil())
  if (!gespeichert) return
  store.set({ pruefung: null, konflikt: { gespeichert, meldung: ergebnis.meldung ?? '', unterschiede: runnerUnterschiede(entwurf, gespeichert.profil) } })
}

async function nachAnwenden({ store, run, applied }: RunnerKontext, ergebnis: RunnerPruefung, version: number): Promise<void> {
  const neu = await run('load', (port) => Promise.all([port.status(), port.profil()]))
  if (neu) {
    uebernimmStand(store, neu[1])
    store.set({ status: neu[0] })
  }
  store.set({ pruefung: ergebnis, meldung: { key: 'angewendet', params: { version }, ton: 'success' } })
  applied(version)
}

async function anwendenMit(kontext: RunnerKontext, erwartet: number): Promise<void> {
  const { store, run } = kontext
  const entwurf = store.get().entwurf
  if (!entwurf) return
  store.set({ meldung: null })
  const ergebnis = await run('anwenden', (port) => port.anwenden(entwurf, erwartet))
  if (!ergebnis) return
  if (ergebnis.konflikt) return konfliktLaden(kontext, entwurf, ergebnis)
  if (!ergebnis.angewendet) {
    store.set({ pruefung: ergebnis, meldung: { key: 'nichtAngewendet', params: { meldung: ergebnis.meldung ?? '' }, ton: 'warning' } })
    return
  }
  return nachAnwenden(kontext, ergebnis, ergebnis.version ?? erwartet + 1)
}

export function profilAktionen(kontext: RunnerKontext): ProfilAktionen {
  const { store, run } = kontext
  return {
    setze: (pfad, wert) => aendere(store, (entwurf) => runnerSetze(entwurf, pfad, wert)),
    eingabe(pfad, art, roh) {
      if (typeof roh === 'string') store.set({ eingaben: { ...store.get().eingaben, [pfad.join('.')]: roh } })
      aendere(store, (entwurf) => runnerSetze(entwurf, pfad, runnerEingabe(art, roh)))
    },
    verwerfen() {
      const stand = store.get().stand
      if (stand) uebernimmStand(store, stand)
      store.set({ meldung: null })
    },
    async pruefen() {
      const entwurf = store.get().entwurf
      if (!entwurf) return
      store.set({ meldung: null })
      const pruefung = await run('pruefen', (port) => port.pruefen(entwurf))
      if (pruefung) store.set({ pruefung })
    },
    anwenden: () => anwendenMit(kontext, runnerVersion(store.get().stand?.profil)),
    gespeichertUebernehmen() {
      const konflikt = store.get().konflikt
      if (konflikt) uebernimmStand(store, konflikt.gespeichert)
    },
    async entwurfTrotzdemAnwenden() {
      const konflikt = store.get().konflikt
      if (!konflikt) return
      store.set({ stand: konflikt.gespeichert, konflikt: null })
      await anwendenMit(kontext, runnerVersion(konflikt.gespeichert.profil))
    },
    verschiebe: (index, richtung) => aendere(store, (entwurf) => runnerVerschiebe(entwurf, index, richtung)),
    prioritaet: (index, aenderung) => aendere(store, (entwurf) => runnerPrioritaetSetze(entwurf, index, aenderung)),
  }
}

export function werkzeugAktionen({ store, run }: RunnerKontext): WerkzeugAktionen {
  return {
    werkzeug(profil, werkzeug, aenderung) {
      const alle = store.get().werkzeugEntwurf
      const bisher = alle?.[profil]?.[werkzeug]
      if (!alle || !bisher) return
      store.set({ werkzeugEntwurf: { ...alle, [profil]: { ...alle[profil], [werkzeug]: { ...bisher, ...aenderung } } }, meldung: null })
    },
    werkzeugZahl(profil, werkzeug, feld, roh) {
      const zahl = Number(roh)
      store.set({ eingaben: { ...store.get().eingaben, [runnerWerkzeugFeldId(profil, werkzeug, feld)]: roh } })
      if (roh.trim() !== '' && Number.isInteger(zahl) && zahl >= 0) this.werkzeug(profil, werkzeug, { [feld]: zahl })
    },
    async werkzeugeSpeichern() {
      const profile = store.get().werkzeugEntwurf
      if (!profile) return
      const ok = await run('werkzeuge', async (port) => {
        await port.werkzeugeSpeichern(profile)
        return true
      })
      if (!ok) return
      const werkzeuge = store.get().werkzeuge
      store.set({ werkzeuge: werkzeuge ? { ...werkzeuge, profile } : werkzeuge, meldung: { key: 'gespeichert', ton: 'success' } })
    },
  }
}
