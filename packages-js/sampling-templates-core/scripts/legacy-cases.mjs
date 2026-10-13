#!/usr/bin/env node
/**
 * Erzeugt die benannten Falldateien der Altvorlagen X1–X4 (`test/cases/X*.json`): Die Fälle
 * entstehen aus einem Standardfall und gezielten Änderungen; ein erneuter Lauf liefert
 * dieselben Dateien. Alle Werte sind erfunden. Die Zufallsbelegungen (`X*.zufall.json`)
 * erzeugt `scripts/random-cases.mjs`, die erwarteten Werte danach `scripts/golden_recalc.py`.
 *
 *     node scripts/legacy-cases.mjs
 */
import { writeFileSync } from 'node:fs'
import process from 'node:process'
import { URL, fileURLToPath } from 'node:url'

const TARGET = fileURLToPath(new URL('../test/cases/', import.meta.url))
const LEVELS = [0.6, 0.7, 0.8, 0.9, 0.95]

/** Fall aus einem Grundfall: `changes` überschreibt, `null` leert die Zelle. */
function variant(sheet, name, base, changes = {}) {
  const inputs = { ...base, ...changes }
  for (const [cell, value] of Object.entries(inputs)) if (value === null) delete inputs[cell]
  return { name, blatt: sheet, eingaben: inputs }
}

/** Je Eingabe ein Fall „alles ausgefüllt außer …“. */
function allBut(sheet, base, cells) {
  return cells.map((cell) => variant(sheet, `Alles ausgefüllt außer ${cell}`, base, { [cell]: null }))
}

function levels(sheet, base, cell, standard) {
  return LEVELS.filter((level) => level !== standard).map((level) => variant(sheet, `Konfidenzniveau ${Math.round(level * 100)} %`, base, { [cell]: level }))
}

function write(name, cases) {
  writeFileSync(`${TARGET}${name}.json`, `${JSON.stringify(cases, null, 1)}\n`)
  process.stdout.write(`${name}: ${cases.length} Fälle\n`)
}

// ---------------------------------------------------------------- X1: konservativer MUS-Ansatz

const X1 = 'X1_KonsMUS_2017'
const x1 = { C1: 48500000, C2: 'Vorhaben', C3: 420, C4: 0.9, C7: 0.005, C13: 18400, C14: 0.62, C16: 95000 }

function x1Cases() {
  return [
    variant(X1, 'Standardfall, Konfidenzniveau 90 %', x1),
    ...levels(X1, x1, 'C4', 0.9),
    variant(X1, 'Leeres Formular', {}),
    ...allBut(X1, x1, ['C1', 'C4', 'C7', 'C13', 'C14', 'C16']),
    variant(X1, 'Ohne Stichprobeneinheit und Umfang der Grundgesamtheit (C2, C3 werden nicht gelesen)', x1, { C2: null, C3: null }),
    variant(X1, 'Nur Planung ausgefüllt, Prüfergebnisse leer', x1, { C13: null, C14: null, C16: null }),
    variant(X1, 'Nur Buchwert ausgefüllt', { C1: 48500000 }),
    variant(X1, 'TE = AE × EF (95 %, erwartete Fehlerquote 1,25 %): Nenner null', x1, { C4: 0.95, C7: 0.0125 }),
    variant(X1, 'Knapp unter TE = AE × EF (95 %, 1,24 %)', x1, { C4: 0.95, C7: 0.0124 }),
    variant(X1, 'Knapp über TE = AE × EF (95 %, 1,26 %): negativer Nenner, Umfang 30', x1, { C4: 0.95, C7: 0.0126 }),
    variant(X1, 'Erwartete Fehlerquote über der Wesentlichkeitsschwelle (3 %)', x1, { C7: 0.03 }),
    variant(X1, 'Rechnerischer Umfang genau 150 (95 %, erwartete Fehlerquote 0)', x1, { C1: 1000000, C4: 0.95, C7: 0, C13: 0, C14: 0.2, C16: 0 }),
    variant(X1, 'Erwartete Fehlerquote 0 eingetragen', x1, { C7: 0 }),
    variant(X1, 'Keine Fehler in der Stichprobe (Nullen eingetragen)', x1, { C13: 0, C14: 0, C16: 0 }),
    variant(X1, 'Buchwert 0: Division durch null', x1, { C1: 0 }),
    variant(X1, 'Kleine Grundgesamtheit, Konfidenzniveau 60 %', x1, { C1: 612345.67, C3: 35, C4: 0.6, C7: 0.002, C13: 0, C14: 0.031, C16: 1250.5 }),
  ]
}

// ---------------------------------------------------------------- X2: Differenzenschätzung

const X2 = 'X2_DiffSch_2017'
const x2 = { C1: 48500000, C2: 'Vorhaben', C3: 420, C4: 9500, C5: 0.9, C7: 0.005, C12: 9200000, C13: 38000, C15: 2900 }

function x2Cases() {
  return [
    variant(X2, 'Standardfall, Konfidenzniveau 90 %', x2),
    ...levels(X2, x2, 'C5', 0.9),
    variant(X2, 'Leeres Formular', {}),
    ...allBut(X2, x2, ['C1', 'C3', 'C4', 'C5', 'C7', 'C13', 'C15']),
    variant(X2, 'Ohne Stichprobeneinheit und Ausgaben der Stichprobe (C2, C12 werden nicht gelesen)', x2, { C2: null, C12: null }),
    variant(X2, 'Nur Planung ausgefüllt, Prüfergebnisse leer', x2, { C12: null, C13: null, C15: null }),
    variant(X2, 'Nur Buchwert ausgefüllt', { C1: 48500000 }),
    variant(X2, 'TE = AE (erwartete Fehlerquote 2 %): Nenner null', x2, { C7: 0.02 }),
    variant(X2, 'Knapp unter TE = AE (1,99 %)', x2, { C7: 0.0199 }),
    variant(X2, 'Knapp über TE = AE (2,01 %): negativer Nenner wird quadriert', x2, { C7: 0.0201 }),
    variant(X2, 'Rechnerischer Umfang unter 30: Mindestumfang 30', x2, { C4: 2500 }),
    variant(X2, 'Rechnerischer Umfang genau 100 (95 %)', x2, { C1: 1960000, C3: 100, C4: 1000, C5: 0.95, C7: 0.01, C12: 400000, C13: 2500, C15: 310 }),
    variant(X2, 'Rechnerischer Umfang genau 30', x2, { C1: 1000000, C3: 100, C4: 547.722557505166, C5: 0.95, C7: 0.0004, C12: 300000, C13: 900, C15: 120 }),
    variant(X2, 'Rechnerischer Umfang knapp über 30: 31', x2, { C1: 1000000, C3: 100, C4: 548, C5: 0.95, C7: 0.0004, C12: 300000, C13: 900, C15: 120 }),
    variant(X2, 'Erwartete Fehlerquote 0 eingetragen', x2, { C7: 0 }),
    variant(X2, 'Keine Fehler in der Stichprobe (Nullen eingetragen)', x2, { C13: 0, C15: 0 }),
    variant(X2, 'Buchwert 0: Division durch null', x2, { C1: 0 }),
    variant(X2, 'Umfang der Grundgesamtheit 0', x2, { C3: 0 }),
    variant(X2, 'Fehler zugunsten des Haushalts überwiegen (negativer Stichprobenfehler)', x2, { C13: -12500 }),
  ]
}

// ---------------------------------------------------------------- X3: Differenzenschätzung, geschichtet

const X3 = 'X3_DiffSch_S_2017'
const COLUMNS = ['E', 'F', 'G', 'H', 'I', 'J', 'K']
/** Eingabezeilen je Schicht: Buchwert, Umfang, σ der Planung, Ausgaben, Fehler und s der Stichprobe. */
const STRATUM_ROWS = [6, 7, 8, 18, 19, 21]
const STRATA = [
  [24000000, 210, 9000, 4100000, 15000, 2800],
  [16500000, 150, 11000, 2900000, 12000, 3300],
  [8000000, 60, 7500, 1700000, 4000, 2100],
  [5200000, 44, 12500, 900000, 2600, 3900],
  [3900000, 31, 10200, 610000, 0, 0],
  [2700000, 25, 8800, 480000, 1900, 2500],
  [1500000, 12, 14000, 390000, 3100, 5200],
]

/** Schichten in den genannten Spalten, belegt mit den Beispielschichten in ihrer Reihenfolge. */
function strata(columns) {
  const inputs = {}
  columns.forEach((column, index) => STRATUM_ROWS.forEach((row, position) => (inputs[`${column}${row}`] = STRATA[index][position])))
  return inputs
}

const x3 = { D2: 'Vorhaben', D9: 0.9, D11: 0.005, ...strata(['E', 'F', 'G']) }
const x3Seven = { D2: 'Vorhaben', D9: 0.9, D11: 0.005, ...strata(COLUMNS) }
const emptyRow = (row, columns = COLUMNS) => Object.fromEntries(columns.map((column) => [`${column}${row}`, null]))

function x3Cases() {
  return [
    variant(X3, 'Standardfall, drei Schichten, Konfidenzniveau 90 %', x3),
    ...levels(X3, x3, 'D9', 0.9),
    variant(X3, 'Leeres Formular', {}),
    variant(X3, 'Eine Schicht (Spalte E)', { D2: 'Vorhaben', D9: 0.9, D11: 0.005, ...strata(['E']) }),
    variant(X3, 'Nur Schicht k (Spalte K)', { D2: 'Vorhaben', D9: 0.9, D11: 0.005, ...strata(['K']) }),
    variant(X3, 'Sieben Schichten (alle Spalten der Vorlage)', x3Seven),
    variant(X3, 'Leere Schicht zwischen belegten (E, G, K)', { D2: 'Vorhaben', D9: 0.9, D11: 0.005, ...strata(['E', 'G', 'K']) }),
    ...allBut(X3, x3, ['D9', 'D11']),
    variant(X3, 'Ohne Stichprobeneinheit (D2 wird nicht gelesen)', x3, { D2: null }),
    variant(X3, 'Sieben Schichten, Buchwerte der Schichten leer (Zeile 6)', x3Seven, emptyRow(6)),
    variant(X3, 'Sieben Schichten, σ der Planung leer (Zeile 8)', x3Seven, emptyRow(8)),
    variant(X3, 'Sieben Schichten, Ausgaben der Stichprobe leer (Zeile 18 wird nicht gelesen)', x3Seven, emptyRow(18)),
    variant(X3, 'Sieben Schichten, Fehler der Stichprobe leer (Zeile 19)', x3Seven, emptyRow(19)),
    variant(X3, 'Sieben Schichten, s der Stichprobe leer (Zeile 21)', x3Seven, emptyRow(21)),
    variant(X3, 'Sieben Schichten, nur Planung ausgefüllt', x3Seven, { ...emptyRow(18), ...emptyRow(19), ...emptyRow(21) }),
    variant(X3, 'Fehlende Angabe in nur einer Schicht: Buchwert F6', x3, { F6: null }),
    variant(X3, 'Fehlende Angabe in nur einer Schicht: σ der Planung F8', x3, { F8: null }),
    variant(X3, 'Fehlende Angabe in nur einer Schicht: Fehler F19', x3, { F19: null }),
    variant(X3, 'Fehlende Angabe in nur einer Schicht: s der Stichprobe F21', x3, { F21: null }),
    variant(X3, 'Schicht nur mit Buchwert, ohne Umfang (H6)', x3, { H6: 2000000 }),
    variant(X3, 'Schicht nur mit Umfang (H7)', x3, { H7: 40 }),
    variant(X3, 'Schichtumfänge heben beim Aufrunden die Summe über den Gesamtumfang', x3Seven, { D11: 0.012 }),
    variant(X3, 'TE = AE (erwartete Fehlerquote 2 %): Nenner null', x3, { D11: 0.02 }),
    variant(X3, 'Knapp unter TE = AE (1,99 %)', x3, { D11: 0.0199 }),
    variant(X3, 'Knapp über TE = AE (2,01 %): negativer Nenner wird quadriert', x3, { D11: 0.0201 }),
    variant(X3, 'Rechnerischer Umfang unter 30: Mindestumfang 30', x3, { E8: 2000, F8: 2500, G8: 1500 }),
    variant(X3, 'Rechnerischer Umfang genau 100 (95 %, eine Schicht)', { D9: 0.95, D11: 0.01, E6: 1960000, E7: 100, E8: 1000, E18: 400000, E19: 2500, E21: 310 }),
    variant(X3, 'Erwartete Fehlerquote 0 eingetragen', x3, { D11: 0 }),
    variant(X3, 'Keine Fehler in der Stichprobe (Nullen eingetragen)', x3, { E19: 0, F19: 0, G19: 0, E21: 0, F21: 0, G21: 0 }),
    variant(X3, 'Schicht mit Umfang 0', x3, { G7: 0 }),
    variant(X3, 'Nur Konfidenzniveau und erwartete Fehlerquote ausgefüllt', { D9: 0.9, D11: 0.005 }),
  ]
}

// ---------------------------------------------------------------- X4: Differenzenschätzung, zwei Zeiträume

const X4 = 'X4_DiffSch_2Z_2017'
const x4 = {
  C2: 'Vorhaben',
  C3: 26000000,
  C4: 22500000,
  C5: 230,
  C6: 190,
  C7: 9000,
  C8: 9500,
  C10: 0.9,
  C12: 0.005,
  C20: 4800000,
  C21: 21000,
  C22: 2700,
  C23: 9800,
  C25: 23100000,
  C26: 205,
  C27: 0.006,
  C33: 2600000,
  C34: 14000,
  C35: 3100,
}
const SECOND_PERIOD = { C23: null, C25: null, C26: null, C27: null, C33: null, C34: null, C35: null }

function x4Cases() {
  return [
    variant(X4, 'Standardfall, Konfidenzniveau 90 %', x4),
    ...levels(X4, x4, 'C10', 0.9),
    variant(X4, 'Leeres Formular', {}),
    variant(X4, 'Nur der erste Zeitraum ausgefüllt', x4, SECOND_PERIOD),
    variant(X4, 'Nur Planung des ersten Zeitraums ausgefüllt', x4, { ...SECOND_PERIOD, C20: null, C21: null, C22: null }),
    ...allBut(X4, x4, ['C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C10', 'C12', 'C21', 'C22', 'C23', 'C25', 'C26', 'C27', 'C34', 'C35']),
    variant(X4, 'Ohne Stichprobeneinheit und Buchwerte der Stichproben (C2, C20, C33 werden nicht gelesen)', x4, { C2: null, C20: null, C33: null }),
    variant(X4, 'Negativer Nenner bei der Neuberechnung (hohe Streuung im ersten Zeitraum)', x4, { C22: 21000 }),
    variant(X4, 'Negativer Nenner mit negativer Varianzsumme: Genauigkeit nicht bestimmbar', x4, { C22: 21000, C35: 60000 }),
    variant(X4, 'Nenner der Neuberechnung knapp über null', x4, { C22: 19650 }),
    variant(X4, 'TE = AE im ersten Zeitraum (erwartete Fehlerquote 2 %): Nenner null', x4, { C12: 0.02 }),
    variant(X4, 'TE = AE im zweiten Zeitraum (erwartete Fehlerquote 2 %)', x4, { C27: 0.02 }),
    variant(X4, 'Erwartete Fehlerquote über der Wesentlichkeitsschwelle im ersten Zeitraum (2,5 %)', x4, { C12: 0.025 }),
    variant(X4, 'Erster Zeitraum ohne Fehler', x4, { C21: 0, C22: 0 }),
    variant(X4, 'Zweiter Zeitraum ohne Fehler', x4, { C34: 0, C35: 0 }),
    variant(X4, 'Erwartete Fehlerquoten 0 eingetragen', x4, { C12: 0, C27: 0 }),
    variant(X4, 'Rechnerischer Umfang genau 100 (95 %, gleiche Zeiträume)', x4, { C3: 980000, C4: 980000, C5: 50, C6: 50, C7: 1000, C8: 1000, C10: 0.95, C12: 0.01, C22: 0, C23: 1000, C25: 980000, C26: 50, C27: 0.01 }),
    variant(X4, 'Zweiter Zeitraum ohne Einheiten (C26 = 0)', x4, { C26: 0 }),
    variant(X4, 'Umfänge der Grundgesamtheit 0', x4, { C5: 0, C6: 0 }),
    variant(X4, 'Sehr kleine Stichprobe (kein Mindestumfang in der Vorlage)', x4, { C7: 900, C8: 950, C22: 300, C23: 980, C35: 310 }),
  ]
}

write(X1, x1Cases())
write(X2, x2Cases())
write(X3, x3Cases())
write(X4, x4Cases())
