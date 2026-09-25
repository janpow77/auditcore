let counter = 0

/** Eindeutige, stabile ID je Komponenteninstanz für aria-Verknüpfungen. */
export function useId(prefix = 'fa'): string {
  counter += 1
  return `${prefix}-${counter}`
}
