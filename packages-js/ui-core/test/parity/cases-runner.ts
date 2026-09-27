/**
 * Paritätsfälle der Runner-Konsole (Vue `RunnerConsole` ↔ React `FlowauditRunnerConsole`).
 * Synthetische, neutrale Daten im Format der JSON-API von `auditcore_runner`.
 */
import { createRunnerMemoryPort, type RunnerAnsicht, type RunnerPort, type RunnerProfil, type RunnerProfilStand, type RunnerStatus, type RunnerWerkzeuge } from '../../src'
import type { ParityCase } from './cases'

export interface RunnerCaseProps {
  port?: RunnerPort | null
  locale?: 'de' | 'en'
  ansicht?: RunnerAnsicht
}

export const runnerProfilBeispiel: RunnerProfil = {
  schema: 'auditcore-runner/profil/3',
  version: 3,
  aenderung: { zeit: '2026-01-02T10:00:00+01:00', quelle: 'lokal', wer: 'ui' },
  sync: 'aus',
  rechner: 'beispiel-rechner',
  image: 'auditcore-runner:local',
  backend: 'jit',
  reserve: { cpus: 4, speicher_gb: 8 },
  netz: { name: 'auditcore-ci', aktiv: true, sperre_pflicht: true },
  soll_quelle: { art: 'lokal', datei: '~/.config/auditcore-runner/soll.json' },
  skalierung: { vorrang_interaktiv: true, leerlauf_minuten: 10, anteil_bei_nutzung: 0.25, thermik: { aktiv: false, url: '' } },
  klassen: {
    cpu: { art: 'cpu', aktiv: true, cpus: 2, speicher_gb: 4, min_instanzen: 0, max_instanzen: 4, leise_max: -1, vram_mb: 0, labels: ['self-hosted', 'cpu'] },
    gpu: { art: 'gpu', aktiv: true, cpus: 2, speicher_gb: 6, min_instanzen: 0, max_instanzen: 1, leise_max: 0, vram_mb: 6000, labels: ['self-hosted', 'gpu'] },
  },
  gpus: [{ index: 0, uuid: 'GPU-0', name: 'Karte 0', vram_mb: 16384, erlaubt: true, klasse: 'gpu' }],
  prioritaeten: [
    { klasse: 'cpu', rang: 1, verdraengbar: false, min: 1 },
    { klasse: 'gpu', rang: 2, verdraengbar: true, min: 0 },
  ],
}

export const runnerStatusBeispiel: RunnerStatus = {
  rechner: 'beispiel-rechner',
  profil_version: 3,
  profil_hash: 'abc123',
  aenderung: { zeit: '2026-01-02T10:00:00+01:00', quelle: 'lokal', wer: 'ui' },
  sync: 'aus',
  ziel: 'besitzer/repo',
  soll_quelle: 'lokal',
  auth_art: 'app',
  hardware: { cpus: 16, speicher_gb: 64, gpus: [{ name: 'Karte 0' }] },
  klassen: {
    cpu: { aktiv: true, max: 4, soll: 2, gruende: ['Leerlauf'], instanzen_aktiv: 2, registriert: 2, belegt: 1 },
    gpu: { aktiv: true, max: 1, soll: 0, gruende: ['Karte belegt'], instanzen_aktiv: 0, registriert: 0, belegt: 0 },
  },
  image_vorhanden: true,
  netz_vorhanden: true,
  netzsperre_aktiv: true,
  unbekannte_runner: [],
  github_rest_kontingent: 4800,
  nur_lesen: false,
}

export const runnerStandBeispiel: RunnerProfilStand = {
  profil: runnerProfilBeispiel,
  profil_hash: 'abc123',
  hardware: runnerStatusBeispiel.hardware,
  probleme: [],
  netzsperre_befehl: 'sudo sh /pfad/zur/netzsperre.sh',
}

export const runnerWerkzeugeBeispiel: RunnerWerkzeuge = {
  werkzeuge: [
    { name: 'ruff', bereich: 'python', installation: 'image', autofix: true, kosten_minuten: 1, im_image: '0.16.0' },
    { name: 'mypy', bereich: 'python', installation: 'image', autofix: false, kosten_minuten: 3, im_image: '' },
  ],
  profile: {
    pr: { mypy: { aktiv: true, zeitlimit_s: 600, prioritaet: 2 }, ruff: { aktiv: true, zeitlimit_s: 120, prioritaet: 1 } },
  },
}

export function runnerBeispielPort(extra: Partial<RunnerStatus> = {}): RunnerPort {
  return createRunnerMemoryPort({ status: { ...runnerStatusBeispiel, ...extra }, profil: runnerStandBeispiel, werkzeuge: runnerWerkzeugeBeispiel })
}

export const runnerCases: ReadonlyArray<ParityCase<RunnerCaseProps>> = [
  {
    name: 'Status mit Klassen',
    props: () => ({ port: runnerBeispielPort() }),
    expect: {
      texts: ['Runner-Konsole', 'beispiel-rechner · Profilversion 3 · nur lokal verwaltet', 'besitzer/repo', 'Leerlauf', 'Anmeldung bei GitHub'],
      roles: [['tab', 'Status'], ['tab', 'Einstellungen'], ['button', 'Aktualisieren']],
      counts: { '[role="tab"][aria-selected="true"]': 1, 'tbody tr': 2 },
    },
  },
  {
    name: 'Warnungen: unbekannte Runner, Image fehlt',
    props: () => ({ port: runnerBeispielPort({ unbekannte_runner: ['fremd-1'], image_vorhanden: false }) }),
    expect: { texts: ['Unbekannte Runner registriert: fremd-1', 'Das Runner-Image fehlt.'], counts: { '.fa-runner__hinweis--danger': 1 } },
  },
  {
    name: 'Einstellungen: Abschnitte und Felder',
    props: () => ({ port: runnerBeispielPort(), ansicht: 'einstellungen' }),
    expect: {
      texts: ['Allgemein', 'Klasse cpu', 'Grafikkarte 0: Karte 0'],
      roles: [['spinbutton', 'Höchstanzahl'], ['checkbox', 'Vorrang interaktiver Nutzung'], ['combobox', 'Soll-Quelle'], ['button', 'Prüfen'], ['button', 'Klasse hinzufügen']],
      counts: { fieldset: 8, 'select[id$=".art"]': 2, 'input[id$="klassen.cpu.vram_mb"]': 0, 'input[id$="klassen.gpu.vram_mb"]': 1 },
    },
  },
  {
    name: 'Werkzeuge eines Prüfprofils',
    props: () => ({ port: runnerBeispielPort(), ansicht: 'werkzeuge' }),
    expect: { texts: ['Prüfprofil pr', 'ruff', '0.16.0', 'nicht installiert'], counts: { 'tbody tr': 2 } },
  },
  {
    name: 'Prioritäten mit Vorschau',
    props: () => ({ port: runnerBeispielPort(), ansicht: 'prioritaeten' }),
    expect: { texts: ['Rang 1', 'Bei Platzmangel weicht zuerst: gpu'], roles: [['button', 'Nach unten: cpu']], counts: { 'ol > li': 2 } },
  },
  {
    name: 'Ohne Klasse der Art gpu keine Kartenauswahl',
    props: () => ({
      port: createRunnerMemoryPort({
        status: runnerStatusBeispiel,
        profil: { ...runnerStandBeispiel, profil: { ...runnerProfilBeispiel, klassen: { cpu: (runnerProfilBeispiel.klassen as Record<string, unknown>).cpu } } },
      }),
      ansicht: 'einstellungen',
    }),
    expect: { texts: ['Klasse cpu'], counts: { 'fieldset legend': 6, 'input[id$="vram_mb"]': 0 } },
  },
  {
    name: 'Nur lesen',
    props: () => ({ port: runnerBeispielPort({ nur_lesen: true }), ansicht: 'einstellungen' }),
    expect: { texts: ['Nur lesen: Änderungen sind nur direkt auf dem Rechner möglich.'], counts: { 'input:not(:disabled)': 0, 'select:not(:disabled)': 0 } },
  },
  {
    name: 'Fehler des Ports, englisch',
    props: () => ({
      port: { ...runnerBeispielPort(), status: async () => { throw new Error('offline') } },
      locale: 'en',
    }),
    expect: { texts: ['Request rejected: offline'], counts: { '[role="alert"]': 1 } },
  },
]
