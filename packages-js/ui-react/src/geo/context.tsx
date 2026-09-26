import { createContext, useContext } from 'react'
import type { GeoController, GeoData, GeoMessageKey, GeoPoint, GeoSelection, Locale, Translate } from '@flowaudit/ui-core'

/** Gemeinsamer Zustand und Übersetzung der Teilkomponenten (Gegenstück zu `GEO_CONTEXT` in Vue). */
export interface GeoContextValue {
  controller: GeoController
  state: GeoData
  selection: GeoSelection
  points: readonly GeoPoint[]
  t: Translate<GeoMessageKey>
  locale: Locale
}

export const GeoContext = createContext<GeoContextValue | null>(null)

export function useGeo(): GeoContextValue {
  const context = useContext(GeoContext)
  if (!context) throw new Error('Geo-Teilkomponenten nur innerhalb von FlowauditGeoMap verwenden.')
  return context
}

/** Zahl aus einem Zahlenfeld (wie `v-model.number`); ungültige Eingaben ändern nichts. */
export function numberInput(value: string, apply: (next: number) => void): void {
  const parsed = Number.parseFloat(value)
  if (!Number.isNaN(parsed)) apply(parsed)
}
