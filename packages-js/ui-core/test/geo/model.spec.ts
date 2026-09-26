import { describe, expect, it } from 'vitest'
import { areasFromGeoPackage, displayName, formatDegrees, formatDistance, formatMetres, parseDegrees, parseLatLon, parseMetres, parseUtm, TOLERANCE_STEPS, utmErrorKey, vertexCount } from '../../src/geo/model'
import type { GeoPackageResult } from '../../src/geo/types'
import gpkg from '../fixtures/geo-gpkg.json'

describe('Geo-Modell', () => {
  it('liest UTM-Eingaben mit Wertebereich und benennt das fehlerhafte Feld', () => {
    expect(parseMetres('476398,98')).toBe(476398.98)
    expect(parseMetres('476.398,98')).toBeNull()
    expect(parseUtm('32', '476398,98', '5549801.4')).toEqual({ value: { zone: 32, ost: 476398.98, nord: 5549801.4 }, error: null })
    expect(parseUtm('61', '476398', '5549801').error).toBe('zone')
    expect(parseUtm('3a', '476398', '5549801').error).toBe('zone')
    expect(parseUtm('32', '1000000', '5549801').error).toBe('east')
    expect(parseUtm('32', '476398', '-1').error).toBe('north')
    expect(utmErrorKey('east')).toBe('utmerroreast')
  })

  it('liest Dezimalgrad mit Komma oder Punkt und weist Tausendertrennung ab', () => {
    expect(parseDegrees('50,1106')).toBe(50.1106)
    expect(parseDegrees(' -8.5 ')).toBe(-8.5)
    expect(parseDegrees('1.234,5')).toBeNull()
    expect(parseDegrees('abc')).toBeNull()
    expect(parseDegrees('')).toBeNull()
  })

  it('prüft den Wertebereich und benennt das fehlerhafte Feld', () => {
    expect(parseLatLon('50,1', '8,6')).toEqual({ point: { lat: 50.1, lon: 8.6 }, error: null })
    expect(parseLatLon('91', '8')).toEqual({ point: null, error: 'lat' })
    expect(parseLatLon('50', '181')).toEqual({ point: null, error: 'lon' })
  })

  it('formatiert Entfernungen, Grad und Meter sprachabhängig', () => {
    expect(formatDistance(850.4, 'de')).toBe('850 m')
    expect(formatDistance(4234.5, 'de')).toBe('4,23 km')
    expect(formatDistance(4234.5, 'en')).toBe('4.23 km')
    expect(formatDegrees(50.1, 'de')).toBe('50,100000')
    expect(formatMetres(5550000.123, 'de')).toBe('5550000,12')
  })

  it('zählt Stützpunkte und übernimmt GeoPackage-Flächen mit Herkunft', () => {
    const result = gpkg as unknown as GeoPackageResult
    const areas = areasFromGeoPackage(result, 'datei')
    expect(areas).toHaveLength(1)
    expect(areas[0]?.id).toBe('datei:1')
    expect(displayName(areas[0] ?? { id: 'x', geometry: { type: 'Polygon', coordinates: [] } })).toBe('Schutzgebiet Nord')
    expect(vertexCount(result.flaechen[0]?.geometrie ?? { type: 'Polygon', coordinates: [] })).toBe(5)
    expect(displayName({ id: 'P-1', label: ' ', lat: 0, lon: 0 })).toBe('P-1')
    expect(TOLERANCE_STEPS.meter[0]).toBe(0)
  })
})
