import { RestError, requestJson, type RestOptions } from '../rest'
import type { GeoPackageResult, GeoPort } from './types'

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

async function uploadError(response: Response): Promise<RestError> {
  const data = (await response.json().catch(() => ({}))) as { error?: { code?: string; message?: string } }
  return new RestError(data.error?.message ?? `HTTP ${response.status}`, response.status, data.error?.code ?? 'http_error')
}

/** `POST /gpkg`: die Datei ist der Anfragekörper (kein JSON, kein Multipart). */
async function upload(options: RestOptions, file: Blob, table?: string): Promise<GeoPackageResult> {
  const fetchImpl = options.fetch ?? ((input, init) => globalThis.fetch(input, init))
  const response = await fetchImpl(`${options.baseUrl.replace(/\/$/, '')}/gpkg${query(table)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/geopackage+sqlite3', Accept: 'application/json', ...options.headers },
    body: file,
  })
  if (!response.ok) throw await uploadError(response)
  return (await response.json()) as GeoPackageResult
}

/** Port auf den REST-Vertrag von `auditcore_geo.web` (Starlette oder FastAPI). */
export function createGeoRestPort(options: GeoRestOptions): GeoPort {
  const port: GeoPort = {
    catalogue: () => requestJson(options, '/profile'),
    radius: (request) => requestJson(options, '/umkreis', request),
    locate: (request) => requestJson(options, '/lage', request),
    utm: (request) => requestJson(options, '/utm', request),
    simplify: (request) => requestJson(options, '/vereinfachung', request),
    loadGeoPackage: (file, table) => upload(options, file, table),
    loadSource: (name, table) => requestJson(options, `/gpkg/quellen/${encodeURIComponent(name)}${query(table)}`),
  }
  if (options.geocoding) port.geocode = (text) => requestJson(options, '/geocode', { anfrage: text })
  return port
}
