import { useEffect, useMemo, useRef, useState } from 'react'
import {
  createGeoController,
  geoMessages,
  selectGeo,
  type GeoArea,
  type GeoPackageResult,
  type GeoPoint,
  type GeoPort,
  type LatLon,
  type Locale,
  type LocateResult,
  type RadiusResult,
  type TileSource,
} from '@flowaudit/ui-core'
import { useTranslation } from '../i18n'
import { useStoreState } from '../store'
import { GeoContext, useGeo as useGeoContextValue, type GeoContextValue } from './context'
import { GeoLocate } from './GeoLocate'
import { GeoMapCanvas } from './GeoMapCanvas'
import { GeoPackageLoader } from './GeoPackageLoader'
import { GeoRadius } from './GeoRadius'
import { GeoReference } from './GeoReference'
import { GeoSimplify } from './GeoSimplify'

export interface FlowauditGeoMapProps {
  /** Fachlogik, z. B. `createGeoRestPort({ baseUrl: '/api/geo' })` (docs/ui/geo-rest.md). */
  port?: GeoPort | null
  /** Punkte (Dezimalgrad, WGS 84/ETRS89). */
  points?: readonly GeoPoint[]
  /** Flächen als GeoJSON-Polygon/-MultiPolygon. */
  areas?: readonly GeoArea[]
  /** Kachelquelle der Anwendung; ohne Angabe kein Hintergrund und kein fremder Server. */
  tiles?: TileSource | null
  /** Anfangsausschnitt; ohne Punkte und Flächen gilt er dauerhaft. */
  center?: LatLon
  zoom?: number
  locale?: Locale
  onRadiusCompleted?: (result: RadiusResult) => void
  onLocationChecked?: (result: LocateResult) => void
  onAreasLoaded?: (areas: readonly GeoArea[], result: GeoPackageResult) => void
  onReferenceChange?: (point: LatLon | null) => void
  onError?: (message: string) => void
}

const NO_POINTS: readonly GeoPoint[] = []
const NO_AREAS: readonly GeoArea[] = []
const GERMANY: LatLon = { lat: 51.163, lon: 10.448 }

function useGeoMap(props: FlowauditGeoMapProps) {
  const { port = null, points = NO_POINTS, areas = NO_AREAS } = props
  const inputs = useMemo(() => ({ port, points, areas }), [port, points, areas])
  const latest = useRef({ inputs, props })
  latest.current = { inputs, props }
  const [controller] = useState(() =>
    createGeoController({
      inputs: () => latest.current.inputs,
      radius: (result) => latest.current.props.onRadiusCompleted?.(result),
      located: (result) => latest.current.props.onLocationChecked?.(result),
      areasLoaded: (areas, result) => latest.current.props.onAreasLoaded?.(areas, result),
      reference: (point) => latest.current.props.onReferenceChange?.(point),
      failed: (message) => latest.current.props.onError?.(message),
    }),
  )
  const state = useStoreState(controller.store)
  useEffect(() => {
    void controller.load()
  }, [controller, props.port])
  const selection = useMemo(() => selectGeo(state, inputs), [state, inputs])
  return { controller, state, selection, inputs }
}

/**
 * Geo-Karte als native React-Komponente (Vertrag wie `<flowaudit-geo-map>`):
 * Karte, Bezugspunkt mit UTM, Umkreis, Punkt in Fläche, Vereinfachung,
 * GeoPackage. Jede Berechnung läuft über den Port (auditcore_geo.web).
 */
function Messages({ hasPort }: { hasPort: boolean }) {
  const { state, t } = useGeoContextValue()
  return (
    <>
      {hasPort ? null : <p className="fa-geo__notice" role="status">{t('noPort')}</p>}
      {state.busy === 'load' ? <p className="fa-geo__muted" role="status">{t('loading')}</p> : null}
      {state.failure ? <p className="fa-geo__failure" role="alert">{t('failed', { message: state.failure })}</p> : null}
      {state.hint ? <p className="fa-geo__error" role="alert" data-testid="geo-hint">{t(state.hint)}</p> : null}
    </>
  )
}

function Panel({ port }: { port: GeoPort | null | undefined }) {
  const { state } = useGeoContextValue()
  const upload = Boolean(port?.loadGeoPackage)
  const sources = Boolean(port?.loadSource)
  return (
    <div className="fa-geo__panel">
      <GeoReference />
      {state.catalogue ? (
        <>
          <GeoRadius />
          <GeoLocate />
          <GeoSimplify />
          {upload || sources ? <GeoPackageLoader upload={upload} sources={sources} /> : null}
        </>
      ) : null}
    </div>
  )
}

/**
 * Geo-Karte als native React-Komponente (Vertrag wie `<flowaudit-geo-map>`):
 * Karte, Bezugspunkt mit UTM, Umkreis, Punkt in Fläche, Vereinfachung,
 * GeoPackage. Jede Berechnung läuft über den Port (auditcore_geo.web).
 */
export function FlowauditGeoMap(props: FlowauditGeoMapProps) {
  const { t, locale } = useTranslation(geoMessages, props.locale)
  const { controller, state, selection, inputs } = useGeoMap(props)
  const context: GeoContextValue = { controller, state, selection, points: inputs.points, t, locale }
  return (
    <GeoContext.Provider value={context}>
      <div className="fa-geo" lang={locale}>
        <Messages hasPort={!!props.port} />
        <div className="fa-geo__layout">
          <GeoMapCanvas layers={selection.layers} tiles={props.tiles ?? null} center={props.center ?? GERMANY} zoom={props.zoom ?? 6} onPick={(point) => void controller.setReference(point)} />
          <Panel port={props.port} />
        </div>
      </div>
    </GeoContext.Provider>
  )
}
