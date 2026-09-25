import { formatNumber, type Locale } from '../i18n'
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
