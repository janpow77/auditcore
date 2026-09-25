import { requestJson, requestUpload, type RestOptions } from '../rest'
import type { GeoPort } from './types'

export interface GeoRestOptions extends RestOptions {
  /**
   * Adresssuche über `POST /geocode` anbieten. Standard `false`: ohne
   * ausdrückliche Freigabe sendet die Oberfläche keine Adressen, auch wenn
   * der Server einen Geocoder angeschlossen hat.
   */
  geocoding?: boolean
}

function query(table?: string): string {
  return table ? `?tabelle=${encodeURIComponent(table)}` : ''
}

/** Port auf den REST-Vertrag von `auditcore_geo.web` (Starlette oder FastAPI). */
export function createGeoRestPort(options: GeoRestOptions): GeoPort {
  const port: GeoPort = {
    catalogue: () => requestJson(options, '/profile'),
    radius: (request) => requestJson(options, '/umkreis', request),
    locate: (request) => requestJson(options, '/lage', request),
    utm: (request) => requestJson(options, '/utm', request),
    simplify: (request) => requestJson(options, '/vereinfachung', request),
    loadGeoPackage: (file, table) =>
      requestUpload(options, `/gpkg${query(table)}`, file, 'application/geopackage+sqlite3'),
    loadSource: (name, table) => requestJson(options, `/gpkg/quellen/${encodeURIComponent(name)}${query(table)}`),
  }
  if (options.geocoding) port.geocode = (text) => requestJson(options, '/geocode', { anfrage: text })
  return port
}
