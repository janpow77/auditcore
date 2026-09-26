import { useEffect, useRef } from 'react'
import { createLeafletView, displayName, type LatLon, type MapLayers, type MapView, type TileSource } from '@flowaudit/ui-core'
import { Button } from '../base/Button'
import { useGeo } from './context'

export interface GeoMapCanvasProps {
  layers: MapLayers
  tiles: TileSource | null
  center: LatLon
  zoom: number
  onPick: (point: LatLon) => void
}

function useMapView(container: React.RefObject<HTMLDivElement | null>, props: GeoMapCanvasProps) {
  const view = useRef<MapView | null>(null)
  const latest = useRef(props)
  latest.current = props
  useEffect(() => {
    let unmounted = false
    const element = container.current
    if (!element) return undefined
    const { center, zoom, tiles, layers } = latest.current
    void createLeafletView(element, { center, zoom, tiles, onPick: (point) => latest.current.onPick(point), label: displayName }).then((created) => {
      if (unmounted) {
        created.destroy()
        return
      }
      view.current = created
      created.update(latest.current.layers)
      if (layers.points.length + layers.areas.length > 0) created.fit()
    })
    return () => {
      unmounted = true
      view.current?.destroy()
      view.current = null
    }
  }, [container])
  return view
}

/** Leaflet-Karte (erst beim Anzeigen geladen) mit Punkten, Flächen, Bezugspunkt und Umkreis. */
export function GeoMapCanvas(props: GeoMapCanvasProps) {
  const { t } = useGeo()
  const container = useRef<HTMLDivElement | null>(null)
  const view = useMapView(container, props)
  const { layers, tiles } = props
  const count = layers.points.length + layers.areas.length
  useEffect(() => {
    view.current?.update(layers)
  }, [view, layers])
  useEffect(() => {
    view.current?.fit()
  }, [view, count])
  useEffect(() => {
    view.current?.setTiles(tiles)
  }, [view, tiles])
  return (
    <div className="fa-geo__canvas-wrap">
      <div ref={container} className="fa-geo__canvas" role="application" aria-label={t('mapLabel', { points: layers.points.length, areas: layers.areas.length })} data-testid="geo-map" />
      <div className="fa-geo__map-bar">
        {tiles?.url ? (
          <p className="fa-geo__muted" data-testid="geo-attribution">{t('attribution', { text: tiles.attribution })}</p>
        ) : (
          <p className="fa-geo__muted" data-testid="geo-no-tiles">{t('noTiles')}</p>
        )}
        <Button size="sm" icon="expand" testId="geo-fit" onClick={() => view.current?.fit()}>{t('fit')}</Button>
      </div>
    </div>
  )
}
