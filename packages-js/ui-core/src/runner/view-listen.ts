// Ansichtsmodelle der Bereiche „Werkzeuge“ und „Prioritäten“.

import type { Translate } from '../i18n'
import type { RunnerData } from './controller'
import { runnerWerkzeugFeldId } from './eingabe'
import type { RunnerMessageKey } from './messages'
import { runnerPrioritaeten, runnerWeichtZuerst, type RunnerPrioritaet } from './profil'

type T = Translate<RunnerMessageKey>

// ---------------------------------------------------------------- Werkzeuge

export interface RunnerWerkzeugZeile {
  id: string
  werkzeug: string
  bereich: string
  imImage: string
  aktiv: boolean
  zeitlimit: string
  prioritaet: string
}

export interface RunnerWerkzeugGruppe {
  profil: string
  titel: string
  zeilen: RunnerWerkzeugZeile[]
}

export function runnerWerkzeugGruppen(state: RunnerData, t: T): RunnerWerkzeugGruppe[] {
  const katalog = new Map((state.werkzeuge?.werkzeuge ?? []).map((w) => [w.name, w]))
  const profile = state.werkzeugEntwurf ?? {}
  return Object.keys(profile)
    .sort()
    .map((profil) => ({
      profil,
      titel: t('werkzeugProfil', { name: profil }),
      zeilen: Object.entries(profile[profil] ?? {})
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([werkzeug, einstellung]) => ({
          id: `${profil}-${werkzeug}`,
          werkzeug,
          bereich: katalog.get(werkzeug)?.bereich ?? '',
          imImage: katalog.get(werkzeug)?.im_image || t('nichtInstalliert'),
          aktiv: einstellung.aktiv,
          zeitlimit: state.eingaben[runnerWerkzeugFeldId(profil, werkzeug, 'zeitlimit_s')] ?? String(einstellung.zeitlimit_s),
          prioritaet: state.eingaben[runnerWerkzeugFeldId(profil, werkzeug, 'prioritaet')] ?? String(einstellung.prioritaet),
        })),
    }))
}

export function runnerWerkzeugeGeaendert(state: RunnerData): boolean {
  return JSON.stringify(state.werkzeugEntwurf) !== JSON.stringify(state.werkzeuge?.profile ?? null)
}

// ---------------------------------------------------------------- Prioritäten

export interface RunnerPrioritaetZeile extends RunnerPrioritaet {
  index: number
  rangText: string
  hoch: string
  runter: string
  ersteZeile: boolean
  letzteZeile: boolean
}

export function runnerPrioritaetZeilen(state: RunnerData, t: T): RunnerPrioritaetZeile[] {
  const liste = runnerPrioritaeten(state.entwurf)
  return liste.map((eintrag, index) => ({
    ...eintrag,
    index,
    rangText: t('rang', { rang: eintrag.rang }),
    hoch: t('hoch', { name: eintrag.klasse }),
    runter: t('runter', { name: eintrag.klasse }),
    ersteZeile: index === 0,
    letzteZeile: index === liste.length - 1,
  }))
}

export function runnerWeichtZuerstText(state: RunnerData, t: T): string {
  const liste = runnerPrioritaeten(state.entwurf)
  if (!liste.length) return ''
  const eintrag = runnerWeichtZuerst(liste)
  return eintrag ? t('weichtZuerst', { name: eintrag.klasse }) : t('keinerVerdraengbar')
}
