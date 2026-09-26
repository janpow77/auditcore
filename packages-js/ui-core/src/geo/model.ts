import { intlFormatNumber as formatNumber } from '@auditcore/common'
import type { Locale } from '../i18n'
import type { GeoMessageKey } from './messages'
import type { AreaGeometry, GeoArea, GeoPackageResult, GeoPoint, LatLon } from './types'

/** Stufen des Toleranzreglers der Vereinfachung (Meter bzw. Grad). */
export const TOLERANCE_STEPS: Readonly<Record<'meter' | 'grad', readonly number[]>> = {
  meter: [0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000],
  grad: [0, 0.00001, 0.00005, 0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1],
}

/**
 * Dezimalgrad aus Texteingabe; Komma und Punkt sind als Dezimaltrenner
 * erlaubt, Tausendertrennzeichen nicht. Ungültiges ergibt `null`.
 */
export function parseDegrees(text: string): number | null {
  const trimmed = text.trim().replace(',', '.')
  if (!/^[+-]?\d{1,3}(\.\d+)?$/.test(trimmed)) return null
  const value = Number(trimmed)
  return Number.isFinite(value) ? value : null
}

export type CoordinateError = 'lat' | 'lon' | null

/** Punkt aus zwei Texteingaben mit Wertebereichsprüfung. */
export function parseLatLon(lat: string, lon: string): { point: LatLon | null; error: CoordinateError } {
  const la = parseDegrees(lat)
  if (la === null || la < -90 || la > 90) return { point: null, error: 'lat' }
  const lo = parseDegrees(lon)
  if (lo === null || lo < -180 || lo > 180) return { point: null, error: 'lon' }
  return { point: { lat: la, lon: lo }, error: null }
}

/** Meter aus Texteingabe (Komma oder Punkt, keine Tausendertrennung); Ungültiges ergibt `null`. */
export function parseMetres(text: string): number | null {
  const trimmed = text.trim().replace(',', '.')
  if (!/^[+-]?\d+(\.\d+)?$/.test(trimmed)) return null
  const value = Number(trimmed)
  return Number.isFinite(value) ? value : null
}

export type UtmInputError = 'zone' | 'east' | 'north' | null

export interface UtmInput {
  zone: number
  ost: number
  nord: number
}

/** UTM-Eingabe mit Wertebereichsprüfung: Zone 1–60, Ostwert 0–1 000 000 m, Nordwert 0–10 000 000 m. */
export function parseUtm(zone: string, east: string, north: string): { value: UtmInput | null; error: UtmInputError } {
  const number = /^\s*\d{1,2}\s*$/.test(zone) ? Number(zone) : NaN
  if (!(number >= 1 && number <= 60)) return { value: null, error: 'zone' }
  const ost = parseMetres(east)
  if (ost === null || ost <= 0 || ost >= 1_000_000) return { value: null, error: 'east' }
  const nord = parseMetres(north)
  if (nord === null || nord < 0 || nord > 10_000_000) return { value: null, error: 'north' }
  return { value: { zone: number, ost, nord }, error: null }
}

/** Text der Fehlermeldung einer UTM-Eingabe. */
export function utmErrorKey(error: Exclude<UtmInputError, null>): GeoMessageKey {
  return `utmerror${error}`
}

/** Entfernung sprachabhängig: unter 1 km in Metern, sonst in Kilometern mit zwei Stellen. */
export function formatDistance(metres: number, locale: Locale): string {
  if (metres < 1000) return `${formatNumber(Math.round(metres), locale)} m`
  return `${formatNumber(metres / 1000, locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} km`
}

/** Grad mit sechs Nachkommastellen (≈ 0,1 m). */
export function formatDegrees(value: number, locale: Locale): string {
  return formatNumber(value, locale, { minimumFractionDigits: 6, maximumFractionDigits: 6 })
}

/** Rechts-/Hochwert in Metern mit zwei Nachkommastellen, ohne Tausendertrennung. */
export function formatMetres(value: number, locale: Locale): string {
  return formatNumber(value, locale, { minimumFractionDigits: 2, maximumFractionDigits: 2, useGrouping: false })
}

/** Anzahl der Stützpunkte einer Fläche (Schlusspunkte mitgezählt). */
export function vertexCount(geometry: AreaGeometry): number {
  const polygons = geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates
  return polygons.reduce((sum, rings) => sum + rings.reduce((inner, ring) => inner + ring.length, 0), 0)
}

/** Flächen aus einer GeoPackage-Antwort; Kennungen erhalten die Herkunft als Präfix. */
export function areasFromGeoPackage(result: GeoPackageResult, origin: string): GeoArea[] {
  return result.flaechen.map((area) => ({
    id: `${origin}:${area.id}`,
    label: area.bezeichnung,
    geometry: area.geometrie,
    notes: area.hinweise,
  }))
}

/** Bezeichnung für Listen: Name, sonst Kennung. */
export function displayName(entry: GeoPoint | GeoArea): string {
  return entry.label?.trim() ? entry.label : entry.id
}
