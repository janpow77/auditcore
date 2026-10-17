/**
 * Migrationsgerüst der Arbeitsstandsdatei. Jede Funktion hebt eine Datei von
 * ihrer Fassung auf die nächste; ältere Dateien laufen der Reihe nach durch,
 * neuere Fassungen werden abgelehnt. Mit Fassung 1 gibt es noch keinen Schritt.
 *
 * Neue Fassung einführen: `WORKSPACE_FORMAT_VERSION` erhöhen, hier unter der
 * alten Fassungsnummer eine Funktion ergänzen, Schema und Tests anpassen.
 */
import { OpenFailure } from './validate'

/** Hebt eine Datei von der Fassung des Schlüssels auf die nächste Fassung. */
export type Migration = (file: Record<string, unknown>) => Record<string, unknown>

export type Migrations = Readonly<Record<number, Migration>>

export const MIGRATIONS: Migrations = {}

/** Datei schrittweise von `from` auf `to` anheben. */
export function migrate(file: Record<string, unknown>, from: number, to: number, migrations: Migrations = MIGRATIONS): Record<string, unknown> {
  let current = file
  for (let version = from; version < to; version += 1) {
    const step = migrations[version]
    if (!step) throw new OpenFailure('invalid-structure', `Migration von Fassung ${version} fehlt`)
    current = { ...step(current), formatVersion: version + 1 }
  }
  return current
}
