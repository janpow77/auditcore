/**
 * Eigene, neu gezeichnete Pfade für Ereignis-, Gateway-, Aufgaben- und
 * Aktivitätsmarker. Alle Koordinaten sind lokal zur jeweiligen Form; die
 * Funktionen liefern SVG-Pfaddaten (Attribut `d`).
 *
 * Die Formen folgen den Symbolbeschreibungen der BPMN-2.0-Spezifikation
 * (OMG, Kapitel 10 und 13), sind aber vollständig eigenständig konstruiert.
 */

type Point = [number, number]

function r(value: number): number {
  return Math.round(value * 100) / 100
}

function polygon(points: Point[]): string {
  return points.map(([x, y], index) => `${index === 0 ? 'M' : 'L'} ${r(x)} ${r(y)}`).join(' ') + ' Z'
}

function rotate([x, y]: Point, angle: number): Point {
  const cos = Math.cos(angle)
  const sin = Math.sin(angle)
  return [x * cos - y * sin, x * sin + y * cos]
}

function translatePoints(points: Point[], cx: number, cy: number, scale = 1): Point[] {
  return points.map(([x, y]) => [cx + x * scale, cy + y * scale])
}

/** Pluszeichen als geschlossene Fläche (Armbreite 2·a, Armlänge l). */
export function crossPath(cx: number, cy: number, a: number, l: number, angle = 0): string {
  const points: Point[] = [
    [-a, -l], [a, -l], [a, -a], [l, -a], [l, a], [a, a],
    [a, l], [-a, l], [-a, a], [-l, a], [-l, -a], [-a, -a],
  ]
  return polygon(translatePoints(points.map((p) => rotate(p, angle)), cx, cy))
}

/** Regelmäßiges Vieleck (z. B. Fünfeck für „Mehrfach“). */
export function regularPolygonPath(cx: number, cy: number, radius: number, corners: number): string {
  const points: Point[] = []
  for (let i = 0; i < corners; i++) {
    const angle = -Math.PI / 2 + (i * 2 * Math.PI) / corners
    points.push([cx + radius * Math.cos(angle), cy + radius * Math.sin(angle)])
  }
  return polygon(points)
}

// ---------------------------------------------------------------------------
// Ereignisdefinitionen (zentriert um cx/cy, Grundmaß für Kreis Ø 36)
// ---------------------------------------------------------------------------

export function envelopePaths(cx: number, cy: number, s: number): { body: string; flap: string } {
  const w = 16 * s
  const h = 11 * s
  const x = cx - w / 2
  const y = cy - h / 2
  return {
    body: `M ${r(x)} ${r(y)} H ${r(x + w)} V ${r(y + h)} H ${r(x)} Z`,
    flap: `M ${r(x)} ${r(y)} L ${r(cx)} ${r(y + h * 0.55)} L ${r(x + w)} ${r(y)}`,
  }
}

export function timerTicks(cx: number, cy: number, s: number): string {
  const parts: string[] = []
  for (let i = 0; i < 12; i++) {
    const angle = (i * Math.PI) / 6
    const inner = (i % 3 === 0 ? 7 : 8) * s
    const outer = 9.5 * s
    parts.push(
      `M ${r(cx + inner * Math.sin(angle))} ${r(cy - inner * Math.cos(angle))} ` +
        `L ${r(cx + outer * Math.sin(angle))} ${r(cy - outer * Math.cos(angle))}`,
    )
  }
  return parts.join(' ')
}

export function timerHands(cx: number, cy: number, s: number): string {
  return `M ${r(cx)} ${r(cy)} L ${r(cx)} ${r(cy - 6.5 * s)} M ${r(cx)} ${r(cy)} L ${r(cx + 4.5 * s)} ${r(cy + 1.5 * s)}`
}

export function escalationPath(cx: number, cy: number, s: number): string {
  return polygon(translatePoints([[0, -9], [7, 8], [0, 1.5], [-7, 8]], cx, cy, s))
}

export function conditionalPaths(cx: number, cy: number, s: number): { sheet: string; lines: string } {
  const sheet = polygon(translatePoints([[-6.5, -8.5], [6.5, -8.5], [6.5, 8.5], [-6.5, 8.5]], cx, cy, s))
  const lines = [-5, -1.7, 1.7, 5]
    .map((dy) => `M ${r(cx - 4.5 * s)} ${r(cy + dy * s)} L ${r(cx + 4.5 * s)} ${r(cy + dy * s)}`)
    .join(' ')
  return { sheet, lines }
}

export function linkPath(cx: number, cy: number, s: number): string {
  return polygon(
    translatePoints([[-8.5, -3.5], [1, -3.5], [1, -8], [9, 0], [1, 8], [1, 3.5], [-8.5, 3.5]], cx, cy, s),
  )
}

export function errorPath(cx: number, cy: number, s: number): string {
  return polygon(translatePoints([[-8, 8.5], [-3, -8.5], [2, 1], [8, -8.5], [3, 8.5], [-2, -1]], cx, cy, s))
}

export function cancelPath(cx: number, cy: number, s: number): string {
  return crossPath(cx, cy, 2.2 * s, 9 * s, Math.PI / 4)
}

export function compensationPath(cx: number, cy: number, s: number): string {
  const left = translatePoints([[-0.5, -6.5], [-8.5, 0], [-0.5, 6.5]], cx, cy, s)
  const right = translatePoints([[7.5, -6.5], [-0.5, 0], [7.5, 6.5]], cx, cy, s)
  return polygon(left) + ' ' + polygon(right)
}

export function signalPath(cx: number, cy: number, s: number): string {
  return polygon(translatePoints([[0, -9.5], [8.5, 6], [-8.5, 6]], cx, cy, s))
}

export function multiplePath(cx: number, cy: number, s: number): string {
  return regularPolygonPath(cx, cy + 0.5 * s, 9 * s, 5)
}

export function parallelMultiplePath(cx: number, cy: number, s: number): string {
  return crossPath(cx, cy, 2.8 * s, 9 * s)
}

// ---------------------------------------------------------------------------
// Aufgabentypen (oben links, Symbolfläche ca. 20 × 20 ab ox/oy)
// ---------------------------------------------------------------------------

export function userIcon(ox: number, oy: number): { head: { cx: number; cy: number; r: number }; body: string } {
  return {
    head: { cx: ox + 9, cy: oy + 5, r: 4 },
    body:
      `M ${ox + 1} ${oy + 18} V ${oy + 15} C ${ox + 1} ${oy + 11.5} ${ox + 4} ${oy + 10} ${ox + 9} ${oy + 10} ` +
      `C ${ox + 14} ${oy + 10} ${ox + 17} ${oy + 11.5} ${ox + 17} ${oy + 15} V ${oy + 18} Z`,
  }
}

export function manualIcon(ox: number, oy: number): string {
  const p = (x: number, y: number) => `${r(ox + x)} ${r(oy + y)}`
  return [
    `M ${p(1, 8)} L ${p(6, 8)} L ${p(10, 4)} Q ${p(11.8, 3)} ${p(12.2, 4.8)} L ${p(10.5, 8)}`,
    `L ${p(18, 8)} Q ${p(19.5, 8)} ${p(19.5, 9.3)} Q ${p(19.5, 10.6)} ${p(18, 10.6)} L ${p(13, 10.6)}`,
    `L ${p(18.5, 10.6)} Q ${p(20, 10.6)} ${p(20, 11.9)} Q ${p(20, 13.2)} ${p(18.5, 13.2)} L ${p(13, 13.2)}`,
    `L ${p(17.5, 13.2)} Q ${p(18.8, 13.2)} ${p(18.8, 14.4)} Q ${p(18.8, 15.6)} ${p(17.5, 15.6)} L ${p(12.5, 15.6)}`,
    `L ${p(15.5, 15.6)} Q ${p(16.7, 15.6)} ${p(16.7, 16.7)} Q ${p(16.7, 17.8)} ${p(15.5, 17.8)} L ${p(6, 17.8)}`,
    `Q ${p(4, 17.8)} ${p(3, 16.5)} L ${p(1, 16.5)} Z`,
  ].join(' ')
}

/** Zahnrad mit `teeth` Zähnen als geschlossene Fläche. */
export function gearPath(cx: number, cy: number, outer: number, inner: number, teeth: number): string {
  const points: Point[] = []
  const step = (2 * Math.PI) / teeth
  for (let i = 0; i < teeth; i++) {
    const a = i * step
    points.push([cx + inner * Math.cos(a - step * 0.3), cy + inner * Math.sin(a - step * 0.3)])
    points.push([cx + outer * Math.cos(a - step * 0.18), cy + outer * Math.sin(a - step * 0.18)])
    points.push([cx + outer * Math.cos(a + step * 0.18), cy + outer * Math.sin(a + step * 0.18)])
    points.push([cx + inner * Math.cos(a + step * 0.3), cy + inner * Math.sin(a + step * 0.3)])
  }
  return polygon(points)
}

export function serviceIcon(ox: number, oy: number): { gears: string[]; holes: { cx: number; cy: number; r: number }[] } {
  return {
    gears: [gearPath(ox + 7.5, oy + 7.5, 7, 5, 8), gearPath(ox + 13.5, oy + 13.5, 6, 4.2, 8)],
    holes: [
      { cx: ox + 7.5, cy: oy + 7.5, r: 2.2 },
      { cx: ox + 13.5, cy: oy + 13.5, r: 1.8 },
    ],
  }
}

export function scriptIcon(ox: number, oy: number): { sheet: string; lines: string } {
  const p = (x: number, y: number) => `${r(ox + x)} ${r(oy + y)}`
  return {
    sheet:
      `M ${p(4, 1)} L ${p(17, 1)} C ${p(14, 4)} ${p(14, 7)} ${p(16, 10)} C ${p(18, 13)} ${p(17, 16)} ${p(14, 18)} ` +
      `L ${p(1, 18)} C ${p(4, 15)} ${p(4, 12)} ${p(2, 9)} C ${p(0, 6)} ${p(1, 3)} ${p(4, 1)} Z`,
    lines: [5, 9, 13].map((y) => `M ${p(4.5 + (y === 9 ? 0.5 : 0), y)} L ${p(13, y)}`).join(' '),
  }
}

export function businessRuleIcon(ox: number, oy: number): { table: string; header: string; lines: string } {
  const p = (x: number, y: number) => `${r(ox + x)} ${r(oy + y)}`
  return {
    table: `M ${p(1, 3)} L ${p(19, 3)} L ${p(19, 16)} L ${p(1, 16)} Z`,
    header: `M ${p(1, 3)} L ${p(19, 3)} L ${p(19, 7)} L ${p(1, 7)} Z`,
    lines: `M ${p(1, 11.5)} L ${p(19, 11.5)} M ${p(6.5, 7)} L ${p(6.5, 16)}`,
  }
}

export function messageTaskIcon(ox: number, oy: number): { body: string; flap: string } {
  return envelopePaths(ox + 10, oy + 8, 1.1)
}

// ---------------------------------------------------------------------------
// Aktivitätsmarker (unten mittig, Fläche 14 × 14 um cx/cy)
// ---------------------------------------------------------------------------

export function loopMarker(cx: number, cy: number): string {
  return (
    `M ${r(cx - 4.5)} ${r(cy + 5)} A 6 6 0 1 1 ${r(cx + 4.5)} ${r(cy + 5)} ` +
    `M ${r(cx + 1.2)} ${r(cy + 5.4)} L ${r(cx + 4.8)} ${r(cy + 5.2)} L ${r(cx + 5.3)} ${r(cy + 1.6)}`
  )
}

export function parallelMarker(cx: number, cy: number): string {
  return [-4, 0, 4].map((dx) => `M ${r(cx + dx)} ${r(cy - 6)} L ${r(cx + dx)} ${r(cy + 6)}`).join(' ')
}

export function sequentialMarker(cx: number, cy: number): string {
  return [-4, 0, 4].map((dy) => `M ${r(cx - 6)} ${r(cy + dy)} L ${r(cx + 6)} ${r(cy + dy)}`).join(' ')
}

export function compensationMarker(cx: number, cy: number): string {
  return compensationPath(cx, cy, 0.8)
}

export function adHocMarker(cx: number, cy: number): string {
  return (
    `M ${r(cx - 7)} ${r(cy + 1.5)} C ${r(cx - 5)} ${r(cy - 3)} ${r(cx - 2)} ${r(cy - 3)} ${r(cx)} ${r(cy)} ` +
    `C ${r(cx + 2)} ${r(cy + 3)} ${r(cx + 5)} ${r(cy + 3)} ${r(cx + 7)} ${r(cy - 1.5)}`
  )
}

export function collapsedMarker(cx: number, cy: number): { frame: string; plus: string } {
  return {
    frame: `M ${r(cx - 7)} ${r(cy - 7)} L ${r(cx + 7)} ${r(cy - 7)} L ${r(cx + 7)} ${r(cy + 7)} L ${r(cx - 7)} ${r(cy + 7)} Z`,
    plus: `M ${r(cx)} ${r(cy - 4.5)} L ${r(cx)} ${r(cy + 4.5)} M ${r(cx - 4.5)} ${r(cy)} L ${r(cx + 4.5)} ${r(cy)}`,
  }
}

/** Sammlungsmarker (drei senkrechte Striche) für Datenobjekte und Pools. */
export function collectionMarker(cx: number, bottom: number): string {
  return [-4, 0, 4].map((dx) => `M ${r(cx + dx)} ${r(bottom - 12)} L ${r(cx + dx)} ${r(bottom - 3)}`).join(' ')
}

/** Pfeil für Dateneingang (hohl) bzw. -ausgang (gefüllt), oben links. */
export function dataArrowPath(ox: number, oy: number): string {
  return polygon(translatePoints([[0, 3], [7, 3], [7, 0], [12, 5], [7, 10], [7, 7], [0, 7]], ox, oy))
}
