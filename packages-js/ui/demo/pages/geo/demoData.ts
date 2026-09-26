import type { GeoArea, GeoPoint } from '@auditcore/ui'

/** Deterministischer Zufall (mulberry32), damit Demo und Bildschirmfotos gleich bleiben. */
function random(seed: number): () => number {
  let state = seed
  return () => {
    state = (state + 0x6d2b79f5) | 0
    let t = Math.imul(state ^ (state >>> 15), 1 | state)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/** 24 erfundene Vorhabenstandorte um einen erfundenen Mittelpunkt. */
export function demoPoints(): GeoPoint[] {
  const next = random(20260925)
  return Array.from({ length: 24 }, (_, index) => ({
    id: `V-${String(index + 1).padStart(3, '0')}`,
    label: `Vorhaben ${index + 1} (Demo)`,
    lat: Math.round((50.25 + next() * 0.18) * 1e5) / 1e5,
    lon: Math.round((8.86 + next() * 0.3) * 1e5) / 1e5,
  }))
}

function ellipse(lon: number, lat: number, rx: number, ry: number, n: number): number[][] {
  const ring = Array.from({ length: n }, (_, i) => {
    const angle = (2 * Math.PI * i) / n
    const wobble = 1 + 0.15 * Math.sin(6 * angle) + 0.05 * Math.cos(17 * angle)
    return [Math.round((lon + rx * Math.cos(angle) * wobble) * 1e6) / 1e6, Math.round((lat + ry * Math.sin(angle) * wobble) * 1e6) / 1e6]
  })
  return [...ring, ring[0] ?? [lon, lat]]
}

/** Zwei erfundene Flächen: ein Rechteck mit Loch (Randfälle) und ein fein gezeichnetes Gebiet. */
export function demoAreas(): GeoArea[] {
  return [
    {
      id: 'demo-rechteck',
      label: 'Gewerbegebiet mit Aussparung (Demo)',
      geometry: {
        type: 'Polygon',
        coordinates: [
          [[8.95, 50.3], [9.0, 50.3], [9.0, 50.33], [8.95, 50.33], [8.95, 50.3]],
          [[8.965, 50.31], [8.985, 50.31], [8.985, 50.32], [8.965, 50.32], [8.965, 50.31]],
        ],
      },
    },
    { id: 'demo-auenlandschaft', label: 'Auenlandschaft (Demo, 240 Stützpunkte)', geometry: { type: 'Polygon', coordinates: [ellipse(9.06, 50.39, 0.05, 0.025, 240)] } },
  ]
}
