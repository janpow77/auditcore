import { inject, type ComputedRef, type InjectionKey } from 'vue'
import type { Locale, Translate } from '../i18n'
import type { GeoMessageKey } from './messages'
import type { UseGeoMap } from './useGeoMap'

/** Gemeinsamer Zustand und Übersetzung für die Teilkomponenten der Geo-Karte. */
export interface GeoContext {
  state: UseGeoMap
  t: Translate<GeoMessageKey>
  locale: ComputedRef<Locale>
}

export const GEO_CONTEXT: InjectionKey<GeoContext> = Symbol('flowaudit-geo')

export function useGeoContext(): GeoContext {
  const context = inject(GEO_CONTEXT, null)
  if (!context) throw new Error('Geo-Teilkomponenten nur innerhalb von FaGeoMap verwenden.')
  return context
}
