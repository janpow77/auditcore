#!/usr/bin/env node
/**
 * Erzeugt den Fallsatz der Zufallsbelegungen eines Blatts für den Golden-Abgleich: vollständig
 * ausgefüllte Belegungen aus einem festen Startwert, im Fallformat von `scripts/golden_recalc.py`
 * (Liste aus `{ "name": …, "blatt": "<Blatt>", "eingaben": { "C7": … } }`). Derselbe Startwert
 * liefert dieselbe Datei Byte für Byte. Alle Werte sind erfunden.
 *
 * Aufruf (im Paketverzeichnis `packages-js/sampling-templates-core`):
 *
 *     node scripts/random-cases.mjs <Blatt> [--anzahl <n>] [--start <Startwert>] [--ziel <Datei>]
 *     node scripts/random-cases.mjs --liste
 *
 * Ohne `--ziel` entsteht `test/cases/<Blatt>.zufall.json`; ohne `--anzahl` und `--start` gelten
 * die Vorgaben des Blatts, mit denen die vorhandenen Fallsätze entstanden sind:
 *
 *     Blatt                Startwert    Anzahl  Generator
 *     03_MUS_1Z            2026101303   100     Mulberry32
 *     04_MUS_1Z_S          2026101304   100     Mulberry32
 *     05_MUS_2Z            2026101305   100     MT19937 wie Python
 *     06_MUS_2Z_S          2026101306   100     MT19937 wie Python
 *     07_MUS_3Z            2026101307   100     MT19937 wie Python
 *     08_SRS_1Z … 12_SRS_3Z  20231067   100     Mulberry32, Startwert mit dem Blattnamen gemischt
 *     13_NS_GW … 16_NS_PPS_S 20261013   120     MT19937 wie Python, Startwert + Blattnummer
 *     X1_KonsMUS_2017      20170630     100     Mulberry32
 *     X2_DiffSch_2017      20170631     100     Mulberry32
 *     X3_DiffSch_S_2017    20170632     100     Mulberry32
 *     X4_DiffSch_2Z_2017   20170633     100     Mulberry32
 *
 * Der gemeinsame Kern liegt in `scripts/random-cases/` (`core.mjs`: Generator, Ziehungen für
 * Beträge, Anteile und Auswahlwerte, Schichtspalten, Ausgabe; `python-random.mjs`: Generator,
 * Rundung und Zahlenschreibweise wie Python für die Blätter 05–07 und 13–16), die Belegung je
 * Blatt bzw. Blattgruppe in `scripts/random-cases/sheets/`. Ein neues Blatt bekommt dort eine
 * Beschreibung `{ start, count, cases }` und einen Eintrag in `sheets/index.mjs`.
 *
 * Danach die erwarteten Werte mit der Vorlage neu berechnen (Wurzel des Repositorys bzw. Pfade
 * entsprechend anpassen); Golden-Dateien entstehen nur so:
 *
 *     python3 scripts/golden_recalc.py test/cases/<Blatt>.zufall.json test/golden/<Blatt>.zufall.golden.json
 */
import { writeFileSync } from 'node:fs'
import process from 'node:process'
import { URL, fileURLToPath } from 'node:url'
import { parseArgs } from 'node:util'
import { serialize } from './random-cases/core.mjs'
import { sheets } from './random-cases/sheets/index.mjs'

const USAGE = 'Aufruf: node scripts/random-cases.mjs <Blatt> [--anzahl <n>] [--start <Startwert>] [--ziel <Datei>] | --liste\n'

function fail(message) {
  process.stderr.write(`${message}\n${USAGE}`)
  process.exit(1)
}

/** Nichtnegative ganze Zahl aus einer Option oder die Vorgabe des Blatts. */
function wholeNumber(text, fallback, option) {
  if (text === undefined) return fallback
  const value = Number(text)
  if (!Number.isSafeInteger(value) || value < 0) fail(`--${option} erwartet eine nichtnegative ganze Zahl, erhalten: ${text}`)
  return value
}

function list() {
  const lines = Object.entries(sheets).map(([sheet, description]) => `${sheet.padEnd(20)} Startwert ${String(description.start).padEnd(11)} Anzahl ${description.count}`)
  process.stdout.write(`${lines.join('\n')}\n`)
}

function readArguments() {
  try {
    return parseArgs({
      allowPositionals: true,
      options: { anzahl: { type: 'string' }, start: { type: 'string' }, ziel: { type: 'string' }, liste: { type: 'boolean' } },
    })
  } catch (error) {
    return fail(error.message)
  }
}

function main() {
  const { values, positionals } = readArguments()
  if (values.liste) return list()
  const [sheet] = positionals
  if (positionals.length !== 1) fail('Genau ein Blatt angeben.')
  const description = sheets[sheet]
  if (!description) fail(`Für Blatt „${sheet}“ gibt es keine Beschreibung. Vorhanden: ${Object.keys(sheets).join(', ')}`)
  const start = wholeNumber(values.start, description.start, 'start')
  const count = wholeNumber(values.anzahl, description.count, 'anzahl')
  const target = values.ziel ?? fileURLToPath(new URL(`../test/cases/${sheet}.zufall.json`, import.meta.url))
  const cases = description.cases({ start, count })
  writeFileSync(target, serialize(cases))
  process.stdout.write(`${target}: ${cases.length} Fälle (Blatt ${sheet}, Startwert ${start})\n`)
}

main()
