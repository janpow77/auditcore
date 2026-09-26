/** Typen des REST-Vertrags `docs/ui/geo-rest.md` (auditcore_geo.web). */

export interface LatLon {
  lat: number
  lon: number
}

/** GeoJSON-Fläche in Achsenfolge Länge, Breite (RFC 7946). */
export type AreaGeometry =
  | { type: 'Polygon'; coordinates: number[][][] }
  | { type: 'MultiPolygon'; coordinates: number[][][][] }

/** Punkt auf der Karte (z. B. Vorhabenstandort); `id` ist die Kennung in Ergebnissen. */
export interface GeoPoint extends LatLon {
  id: string
  label?: string | null
}

/** Fläche auf der Karte (z. B. Schutzgebiet); `notes` sind Hinweise zur Geometrie. */
export interface GeoArea {
  id: string
  label?: string | null
  geometry: AreaGeometry
  notes?: readonly string[]
}

/** Kachelquelle der Anwendung; ohne Quelle zeigt die Karte keinen Hintergrund. */
export interface TileSource {
  /** URL-Vorlage mit `{z}`, `{x}`, `{y}` (optional `{s}`). */
  url: string
  /** Pflichtnennung der Kachel- und Kartendaten, wird immer angezeigt. */
  attribution: string
  maxZoom?: number
  subdomains?: string
}

export interface EarthModel {
  id: string
  radius_m: number
  beschreibung: string
  empfohlen: boolean
}

export interface GeoCatalogue {
  bibliothek: string
  erdmodelle: readonly EarthModel[]
  empfohlenes_erdmodell: string
  rand_gilt_als_innen_empfohlen: boolean
  ellipsoide: readonly string[]
  vereinfachung_einheiten: readonly ('meter' | 'grad')[]
  grenzen: {
    max_body_bytes: number
    max_punkte: number
    max_stuetzpunkte: number
    max_gpkg_bytes: number
    max_gpkg_flaechen: number
  }
  geocoder: { aktiv: boolean; namensnennung: string | null }
  gpkg_quellen: readonly string[]
}

export interface RadiusRequest {
  zentrum: LatLon
  punkte: readonly (LatLon & { id: string })[]
  radius_m: number
  erdmodell: string
}

export interface RadiusHit {
  index: number
  id: string
  abstand_m: number
}

export interface RadiusResult {
  erdmodell: string
  radius_m: number
  geprueft: number
  treffer: readonly RadiusHit[]
}

export type Position = 'innen' | 'aussen' | 'rand'

export interface LocateRequest {
  punkt: LatLon
  flaeche: AreaGeometry
  erdmodell: string
  rand_gilt_als_innen: boolean
  rand_toleranz_m?: number
}

export interface DegenerateRing {
  polygon: number
  ring: number
  art: 'punkt' | 'linie'
  rolle: 'aussen' | 'loch'
  hinweis: string
}

export interface LocateResult {
  lage: Position
  lage_mit_toleranz: Position
  rand_toleranz_m: number
  rand_gilt_als_innen: boolean
  enthaelt: boolean
  abstand_m: number
  erdmodell: string
  entarteter_ring: DegenerateRing | null
  hinweise: readonly string[]
}

export interface UtmRequest {
  punkt: LatLon
  ellipsoid: string
  zone?: number
}

export interface UtmResult {
  zone: number
  nordhalbkugel: boolean
  ellipsoid: string
  epsg: number | null
  mittelmeridian: number
  ost: number
  nord: number
}

/** `POST /utm/geographisch`: Punkt aus Rechts-/Hochwert, Zone und Halbkugel. */
export interface UtmPointRequest {
  ost: number
  nord: number
  zone: number
  nordhalbkugel: boolean
  ellipsoid: string
}

export interface UtmPointResult {
  punkt: LatLon
  zone: number
}

export type SimplifyUnit = 'meter' | 'grad'

export interface SimplifyRequest {
  flaeche: AreaGeometry
  toleranz: number
  einheit: SimplifyUnit
  stellen?: number
}

export interface SimplifyResult {
  geometrie: AreaGeometry | null
  stuetzpunkte_vorher: number
  stuetzpunkte_nachher: number
  entfallene_ringe: readonly { polygon: number; ring: number }[]
  einheit: SimplifyUnit
  toleranz: number
  utm_zone: number | null
}

export interface GeoPackageArea {
  id: string
  bezeichnung: string | null
  geometrie: AreaGeometry
  hinweise: readonly string[]
}

export interface GeoPackageResult {
  quelle?: string
  tabellen: readonly string[]
  tabelle: string
  srs_id: number
  umgerechnet: boolean
  flaechen: readonly GeoPackageArea[]
  fehler: readonly { id: string; meldung: string }[]
  abgeschnitten: boolean
}

export interface GeocodeHit extends LatLon {
  rang: number
  anzeigename: string | null
}

export interface GeocodeResult {
  treffer: readonly GeocodeHit[]
  namensnennung: string
}

/**
 * Schnittstelle der Komponente zur Fachlogik; Standardumsetzung:
 * `createGeoRestPort`. Optionale Methoden fehlen, wenn die Anwendung die
 * Funktion nicht anbietet – die Oberfläche blendet sie dann aus.
 * `geocode` (Adresssuche) gibt es nur auf ausdrücklichen Wunsch.
 */
export interface GeoPort {
  catalogue(): Promise<GeoCatalogue>
  radius(request: RadiusRequest): Promise<RadiusResult>
  locate(request: LocateRequest): Promise<LocateResult>
  utm(request: UtmRequest): Promise<UtmResult>
  /** Rückrechnung aus UTM; ohne sie blendet die Oberfläche die UTM-Eingabe aus. */
  fromUtm?(request: UtmPointRequest): Promise<UtmPointResult>
  simplify(request: SimplifyRequest): Promise<SimplifyResult>
  loadGeoPackage?(file: Blob, table?: string): Promise<GeoPackageResult>
  loadSource?(name: string, table?: string): Promise<GeoPackageResult>
  geocode?(query: string): Promise<GeocodeResult>
}
