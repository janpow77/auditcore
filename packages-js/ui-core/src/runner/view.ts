// Ansichtsmodelle der Runner-Konsole: alles, was Vue und React darstellen,
// wird hier aus dem Zustand abgeleitet (gleiche Zeilen, gleiche Texte).

import type { Translate } from '../i18n'
import type { RunnerData } from './controller'
import { RUNNER_ANSICHTEN } from './controller'
import type { RunnerMessageKey } from './messages'
import { runnerWerkzeugFeldId, type RunnerFeldArt } from './eingabe'
import { runnerGeaendert, runnerPrioritaeten, runnerWeichtZuerst, runnerWert, type RunnerPfad, type RunnerPrioritaet } from './profil'
import type { RunnerAnsicht, RunnerDateiAenderung, RunnerProblem, RunnerProfil, RunnerStatus } from './types'

type T = Translate<RunnerMessageKey>

const TAB_KEYS: Readonly<Record<RunnerAnsicht, RunnerMessageKey>> = {
  status: 'tabStatus',
  einstellungen: 'tabEinstellungen',
  werkzeuge: 'tabWerkzeuge',
  prioritaeten: 'tabPrioritaeten',
}

export interface RunnerTab {
  id: RunnerAnsicht
  label: string
  selected: boolean
}

export function runnerTabs(state: RunnerData, t: T): RunnerTab[] {
  return RUNNER_ANSICHTEN.map((id) => ({ id, label: t(TAB_KEYS[id]), selected: state.ansicht === id }))
}

/** Nächster Reiter für Pfeiltasten (zyklisch). */
export function runnerNachbarTab(aktuell: RunnerAnsicht, richtung: -1 | 1): RunnerAnsicht {
  const index = RUNNER_ANSICHTEN.indexOf(aktuell)
  const next = (index + richtung + RUNNER_ANSICHTEN.length) % RUNNER_ANSICHTEN.length
  return RUNNER_ANSICHTEN[next] as RunnerAnsicht
}

export function runnerNurLesen(state: RunnerData): boolean {
  return Boolean(state.status?.nur_lesen || state.stand?.nur_lesen)
}

export function runnerIstGeaendert(state: RunnerData): boolean {
  return runnerGeaendert(state.entwurf, state.stand?.profil ?? null)
}

export function runnerMeta(state: RunnerData, t: T): string {
  const status = state.status
  if (!status) return ''
  const sync = !status.sync || status.sync === 'aus' ? t('syncAus') : t('syncZentral', { sync: status.sync })
  return `${t('meta', { rechner: status.rechner, version: status.profil_version })} · ${sync}`
}

export interface RunnerHinweis {
  ton: 'danger' | 'warning' | 'info'
  text: string
}

export function runnerHinweise(state: RunnerData, t: T): RunnerHinweis[] {
  const status = state.status
  const hinweise: RunnerHinweis[] = []
  if (runnerNurLesen(state)) hinweise.push({ ton: 'info', text: t('nurLesen') })
  if (!status) return hinweise
  if (status.unbekannte_runner?.length) hinweise.push({ ton: 'danger', text: t('hinweisUnbekannt', { namen: status.unbekannte_runner.join(', ') }) })
  if (!status.image_vorhanden) hinweise.push({ ton: 'warning', text: t('hinweisImage') })
  if (status.netzsperre_aktiv === false) hinweise.push({ ton: 'warning', text: t('hinweisNetzsperre') })
  return hinweise
}

export interface RunnerEintrag {
  label: string
  wert: string
}

function jaNein(wert: boolean | null | undefined, ja: string, nein: string, t: T): string {
  if (wert === null || wert === undefined) return t('unbekannt')
  return wert ? ja : nein
}

export function runnerUeberblick(status: RunnerStatus | null, t: T): RunnerEintrag[] {
  if (!status) return []
  const aenderung = status.aenderung?.zeit ? t('aenderungWert', { zeit: status.aenderung.zeit, quelle: status.aenderung.quelle }) : t('aenderungKeine')
  const eintraege: RunnerEintrag[] = [
    { label: t('ziel'), wert: status.ziel || t('unbekannt') },
    { label: t('sollQuelle'), wert: status.soll_quelle },
    { label: t('profilVersion'), wert: String(status.profil_version) },
    { label: t('aenderung'), wert: aenderung },
    { label: t('image'), wert: jaNein(status.image_vorhanden, t('vorhanden'), t('fehlt'), t) },
    { label: t('netzsperre'), wert: jaNein(status.netzsperre_aktiv, t('aktiv'), t('inaktiv'), t) },
    { label: t('kontingent'), wert: status.github_rest_kontingent === null ? t('unbekannt') : String(status.github_rest_kontingent) },
  ]
  if (status.runner_version) {
    eintraege.push({
      label: t('runnerVersion'),
      wert: status.runner_frist ? t('runnerVersionFrist', { version: status.runner_version, frist: status.runner_frist }) : status.runner_version,
    })
  }
  return eintraege
}

export interface RunnerKlassenZeile {
  name: string
  aktiv: boolean
  soll: string
  max: string
  instanzen: string
  registriert: string
  belegt: string
  warteschlange: string
  gruende: string
}

const zahl = (wert: number | null | undefined): string => (wert === null || wert === undefined ? '–' : String(wert))

export function runnerKlassenZeilen(status: RunnerStatus | null): RunnerKlassenZeile[] {
  if (!status) return []
  return Object.entries(status.klassen)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([name, klasse]) => ({
      name,
      aktiv: klasse.aktiv,
      soll: zahl(klasse.soll),
      max: zahl(klasse.max),
      instanzen: zahl(klasse.instanzen_aktiv),
      registriert: zahl(klasse.registriert),
      belegt: zahl(klasse.belegt),
      warteschlange: zahl(klasse.warteschlange),
      gruende: klasse.gruende.join('; '),
    }))
}

export function runnerHatWarteschlange(status: RunnerStatus | null): boolean {
  return Boolean(status && Object.values(status.klassen).some((klasse) => typeof klasse.warteschlange === 'number'))
}

function kurz(wert: unknown): string {
  if (wert === null || wert === undefined) return '–'
  if (Array.isArray(wert)) {
    const namen = wert.map((eintrag) => (typeof eintrag === 'object' && eintrag !== null ? String((eintrag as Record<string, unknown>).name ?? '') : String(eintrag))).filter(Boolean)
    return namen.length ? namen.join(', ') : String(wert.length)
  }
  if (typeof wert === 'object') return JSON.stringify(wert)
  return String(wert)
}

/** Hardware-Angaben des Rechners als Liste (Schlüssel wie vom Backend geliefert). */
export function runnerHardware(hardware: Readonly<Record<string, unknown>> | null | undefined): RunnerEintrag[] {
  if (!hardware) return []
  return Object.entries(hardware)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([label, wert]) => ({ label, wert: kurz(wert) }))
}

// ---------------------------------------------------------------- Einstellungen


export interface RunnerOption {
  wert: string
  label: string
}

export interface RunnerFeld {
  /** Pfad in Punktschreibweise; zugleich Zuordnung der Fehlermeldungen des Backends. */
  id: string
  pfad: RunnerPfad
  label: string
  art: RunnerFeldArt
  /** Anzeigewert für Eingabe- und Auswahlfelder. */
  wert: string
  /** Zustand eines Schalters. */
  an: boolean
  optionen: readonly RunnerOption[]
  schritt: string
  fehler: string
}

export interface RunnerAbschnitt {
  id: string
  titel: string
  felder: RunnerFeld[]
}

interface FeldDef {
  pfad: RunnerPfad
  key: RunnerMessageKey
  art: RunnerFeldArt
  schritt?: string
  optionen?: (t: T) => readonly RunnerOption[]
}

const SOLL_QUELLEN = [['statisch', 'oStatisch'], ['lokal', 'oLokal'], ['datei', 'oDatei']] as const
const sollQuellen = (t: T): RunnerOption[] => SOLL_QUELLEN.map(([wert, key]) => ({ wert, label: t(key) }))

const ALLGEMEIN: readonly FeldDef[] = [
  { pfad: ['soll_quelle', 'art'], key: 'fSollQuelle', art: 'auswahl', optionen: sollQuellen },
  { pfad: ['soll_quelle', 'datei'], key: 'fSollDatei', art: 'text' },
  { pfad: ['backend'], key: 'fBackend', art: 'text' },
  { pfad: ['image'], key: 'fImage', art: 'text' },
  { pfad: ['reserve', 'cpus'], key: 'fReserveCpus', art: 'zahl' },
  { pfad: ['reserve', 'speicher_gb'], key: 'fReserveSpeicher', art: 'zahl' },
]

const REGELUNG: readonly FeldDef[] = [
  { pfad: ['skalierung', 'vorrang_interaktiv'], key: 'fVorrang', art: 'schalter' },
  { pfad: ['skalierung', 'leerlauf_minuten'], key: 'fLeerlauf', art: 'zahl' },
  { pfad: ['skalierung', 'anteil_bei_nutzung'], key: 'fAnteil', art: 'zahl', schritt: '0.05' },
  { pfad: ['skalierung', 'swap_sperre_gb'], key: 'fSwap', art: 'zahl', schritt: '0.5' },
  { pfad: ['skalierung', 'ram_frei_min_gb'], key: 'fRam', art: 'zahl', schritt: '0.5' },
  { pfad: ['skalierung', 'last_je_kern_max'], key: 'fLast', art: 'zahl', schritt: '0.05' },
  { pfad: ['skalierung', 'temperatur_max_c'], key: 'fTemperatur', art: 'zahl' },
  { pfad: ['skalierung', 'volllast_von'], key: 'fVon', art: 'zahl' },
  { pfad: ['skalierung', 'volllast_bis'], key: 'fBis', art: 'zahl' },
  { pfad: ['skalierung', 'haltezeit_s'], key: 'fHaltezeit', art: 'zahl' },
]

const THERMIK: readonly FeldDef[] = [
  { pfad: ['skalierung', 'thermik', 'aktiv'], key: 'fThermikAktiv', art: 'schalter' },
  { pfad: ['skalierung', 'thermik', 'url'], key: 'fThermikUrl', art: 'text' },
]

const NETZ: readonly FeldDef[] = [
  { pfad: ['netz', 'aktiv'], key: 'fNetzAktiv', art: 'schalter' },
  { pfad: ['netz', 'sperre_pflicht'], key: 'fSperre', art: 'schalter' },
]

const KLASSE: readonly (Omit<FeldDef, 'pfad'> & { feld: string })[] = [
  { feld: 'aktiv', key: 'kAktiv', art: 'schalter' },
  { feld: 'min_instanzen', key: 'kMin', art: 'zahl' },
  { feld: 'max_instanzen', key: 'kMax', art: 'zahl' },
  { feld: 'leise_max', key: 'kLeise', art: 'zahl' },
  { feld: 'cpus', key: 'kCpus', art: 'zahl' },
  { feld: 'speicher_gb', key: 'kSpeicher', art: 'zahl' },
  { feld: 'vram_mb', key: 'kVram', art: 'zahl' },
  { feld: 'labels', key: 'kLabels', art: 'liste' },
]

function anzeige(wert: unknown, art: RunnerFeldArt): string {
  if (art === 'liste') return Array.isArray(wert) ? wert.map(String).join(', ') : ''
  if (wert === null || wert === undefined) return ''
  return String(wert)
}

interface Kontext {
  t: T
  fehler: ReadonlyMap<string, string>
  eingaben: Readonly<Record<string, string>>
}

function feld(profil: RunnerProfil, def: FeldDef, { t, fehler, eingaben }: Kontext): RunnerFeld | null {
  const wert = runnerWert(profil, def.pfad)
  if (wert === undefined) return null
  const id = def.pfad.join('.')
  return {
    id,
    pfad: def.pfad,
    label: t(def.key),
    art: def.art,
    wert: eingaben[id] ?? anzeige(wert, def.art),
    an: wert === true,
    optionen: def.optionen?.(t) ?? [],
    schritt: def.schritt ?? '1',
    fehler: fehler.get(id) ?? '',
  }
}

function abschnitt(id: string, titel: string, profil: RunnerProfil, defs: readonly FeldDef[], kontext: Kontext): RunnerAbschnitt | null {
  const felder = defs.map((def) => feld(profil, def, kontext)).filter((entry): entry is RunnerFeld => entry !== null)
  return felder.length ? { id, titel, felder } : null
}

/** Meldungen des Backends: aus der letzten Prüfung, sonst aus dem geladenen Stand. */
export function runnerProbleme(state: RunnerData): readonly RunnerProblem[] {
  return state.pruefung?.probleme ?? state.stand?.probleme ?? []
}

/** Formularabschnitte aus dem Entwurf; nur Felder, die das Profil tatsächlich enthält. */
export function runnerAbschnitte(state: RunnerData, t: T): RunnerAbschnitt[] {
  const profil = state.entwurf
  if (!profil) return []
  const kontext: Kontext = { t, fehler: new Map(runnerProbleme(state).map((problem) => [problem.feld, problem.meldung])), eingaben: state.eingaben }
  const klassen = runnerWert(profil, ['klassen'])
  const klassenNamen = klassen && typeof klassen === 'object' ? Object.keys(klassen).sort() : []
  const result: (RunnerAbschnitt | null)[] = [
    abschnitt('allgemein', t('abschnittAllgemein'), profil, ALLGEMEIN, kontext),
    abschnitt('regelung', t('abschnittRegelung'), profil, REGELUNG, kontext),
    abschnitt('thermik', t('abschnittThermik'), profil, THERMIK, kontext),
    abschnitt('netz', t('abschnittNetz'), profil, NETZ, kontext),
    ...klassenNamen.map((name) =>
      abschnitt(`klasse-${name}`, t('abschnittKlasse', { name }), profil, KLASSE.map(({ feld: schluessel, ...rest }) => ({ ...rest, pfad: ['klassen', name, schluessel] })), kontext),
    ),
  ]
  const gpus = runnerWert(profil, ['gpus'])
  if (Array.isArray(gpus)) {
    gpus.forEach((karte, index) => {
      const name = typeof karte === 'object' && karte !== null ? String((karte as Record<string, unknown>).name ?? index) : String(index)
      const optionen = (): RunnerOption[] => klassenNamen.map((klasse) => ({ wert: klasse, label: klasse }))
      result.push(
        abschnitt(`karte-${index}`, t('abschnittKarte', { index, name }), profil, [
          { pfad: ['gpus', index, 'erlaubt'], key: 'gErlaubt', art: 'schalter' },
          { pfad: ['gpus', index, 'klasse'], key: 'gKlasse', art: 'auswahl', optionen },
        ], kontext),
      )
    })
  }
  return result.filter((entry): entry is RunnerAbschnitt => entry !== null)
}

export interface RunnerVorschau {
  gueltig: boolean
  aenderungen: readonly RunnerDateiAenderung[]
  schritte: readonly string[]
  rootBefehl: string
}

export function runnerVorschau(state: RunnerData): RunnerVorschau | null {
  const pruefung = state.pruefung
  if (!pruefung) return null
  return { gueltig: pruefung.gueltig, aenderungen: pruefung.aenderungen, schritte: pruefung.schritte, rootBefehl: pruefung.netzsperre_befehl ?? '' }
}

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
