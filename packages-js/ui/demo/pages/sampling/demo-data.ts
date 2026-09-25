import type { PopulationItem } from '@flowaudit/ui'

/** Deterministische Beispielbelegliste (zwei Lose) für die Demo – keine echten Daten. */
export function demoPopulation(count = 240): PopulationItem[] {
  let state = 20260925
  const next = (): number => {
    state = (state * 1103515245 + 12345) % 2147483648
    return state / 2147483648
  }
  return Array.from({ length: count }, (_, index) => {
    const value = Math.round(10 ** (1.5 + next() * 3.2) * 100) / 100
    return { id: `BL-${String(index + 1).padStart(4, '0')}`, value: index % 47 === 0 ? -value / 10 : value, stratum: index % 4 === 0 ? 'Los 2 – Bau' : 'Los 1 – Personal' }
  })
}

/** Beträge mit auffällig vielen Werten, die mit 4 beginnen (für die Hervorhebung). */
export function demoBenfordValues(count = 1500): number[] {
  const items = demoPopulation(count).map((item) => Math.abs(item.value ?? 0))
  return items.map((value, index) => (index % 9 === 0 ? Number(`4${String(Math.round(value)).slice(1)}.${index % 100}`) : value))
}
