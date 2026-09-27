#!/usr/bin/env node
/**
 * Web-Component-Bündel der Runner-Konsole (`@auditcore/ui`, Gruppe `runner`)
 * für das Python-Paket `auditcore_runner` bauen und als Paketdatei ablegen –
 * damit `pip install auditcore_runner` ohne Node auskommt.
 *
 *   npm run runner:bundle            bauen und nach packages/auditcore_runner/…/data/web/ kopieren
 *   npm run runner:bundle -- --pruefen   neu bauen und mit der eingecheckten Datei vergleichen (CI)
 *
 * Der Bau ist deterministisch; `--pruefen` scheitert, wenn Oberfläche, Kern
 * oder Stile geändert wurden, ohne das Bündel neu abzulegen.
 */
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { copyFileSync, existsSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import process from 'node:process'
import { fileURLToPath } from 'node:url'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..')
const BUILT = join(ROOT, 'packages-js', 'ui', 'runner-bundle', 'dist', 'runner-elements.js')
const TARGET = join(ROOT, 'packages', 'auditcore_runner', 'src', 'auditcore_runner', 'data', 'web', 'runner-elements.js')

const sha256 = (path) => createHash('sha256').update(readFileSync(path)).digest('hex')

function build() {
  execFileSync('npm', ['run', 'build:runner', '-w', '@auditcore/ui'], { cwd: ROOT, stdio: ['ignore', 'ignore', 'inherit'] })
  if (!existsSync(BUILT)) throw new Error(`Bündel fehlt nach dem Bau: ${BUILT}`)
}

function main(argv) {
  build()
  if (argv.includes('--pruefen')) {
    if (!existsSync(TARGET)) {
      console.error(`Bündel fehlt im Paket: ${TARGET} – npm run runner:bundle ausführen.`)
      return 1
    }
    if (sha256(BUILT) !== sha256(TARGET)) {
      console.error('Runner-Bündel im Paket ist veraltet – npm run runner:bundle ausführen und die Datei committen.')
      return 1
    }
    console.log(`Runner-Bündel aktuell (sha256 ${sha256(TARGET).slice(0, 12)}).`)
    return 0
  }
  copyFileSync(BUILT, TARGET)
  console.log(`Runner-Bündel abgelegt: ${TARGET} (sha256 ${sha256(TARGET).slice(0, 12)})`)
  return 0
}

try {
  process.exit(main(process.argv.slice(2)))
} catch (error) {
  console.error(`runner:bundle: ${error instanceof Error ? error.message : String(error)}`)
  process.exit(1)
}
