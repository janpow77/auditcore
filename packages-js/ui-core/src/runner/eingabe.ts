// Umsetzung von Formulareingaben in Profilwerte (gemeinsam für Controller und Ansicht).

export type RunnerFeldArt = 'zahl' | 'schalter' | 'auswahl' | 'text' | 'liste'

/** Eingabe eines Feldes in den Profilwert umsetzen (Zahl, Liste, Schalter, Text). */
export function runnerEingabe(feldArt: RunnerFeldArt, roh: string | boolean): unknown {
  if (feldArt === 'schalter') return Boolean(roh)
  const text = String(roh)
  if (feldArt === 'zahl') {
    const zahlWert = Number(text.replace(',', '.'))
    return text.trim() !== '' && Number.isFinite(zahlWert) ? zahlWert : text
  }
  if (feldArt === 'liste') return text.split(',').map((teil) => teil.trim()).filter(Boolean)
  return text
}

/** Schlüssel des Rohtexts einer Werkzeug-Zahleneingabe. */
export function runnerWerkzeugFeldId(profil: string, werkzeug: string, feld: string): string {
  return `werkzeug:${profil}:${werkzeug}:${feld}`
}
