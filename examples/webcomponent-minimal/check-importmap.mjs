#!/usr/bin/env node
// Prüft ohne Browser, dass die Import-Map in index.html jeden Modulimport auflöst:
// ausgehend vom Inline-Modul werden alle statischen und dynamischen Importe der
// erreichbaren Dateien verfolgt (Zerlegung mit es-module-lexer, wie in Vite).
import { existsSync, readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { init, parse } from 'es-module-lexer'

const page = resolve(process.argv[2] ?? 'index.html')
const html = readFileSync(page, 'utf8')
const map = JSON.parse(/<script type="importmap">([\s\S]*?)<\/script>/.exec(html)[1]).imports
const inline = [...html.matchAll(/<script type="module">([\s\S]*?)<\/script>/g)].map((match) => match[1])

function target(specifier, base) {
  if (specifier in map) return resolve(dirname(page), map[specifier])
  if (specifier.startsWith('./') || specifier.startsWith('../')) return resolve(dirname(base), specifier)
  throw new Error(`Nicht in der Import-Map: ${specifier} (aus ${base})`)
}

function specifiers(code) {
  // n ist bei dynamischen Importen mit berechnetem Ziel undefined; solche gibt es hier nicht.
  return parse(code)[0].map((entry) => entry.n).filter((name) => name !== undefined)
}

await init
const seen = new Set()
const pending = inline.flatMap((code) => specifiers(code).map((name) => target(name, page)))
while (pending.length) {
  const file = pending.pop()
  if (seen.has(file)) continue
  if (!existsSync(file)) throw new Error(`Datei fehlt: ${file}`)
  seen.add(file)
  for (const name of specifiers(readFileSync(file, 'utf8'))) pending.push(target(name, file))
}
console.log(`Import-Map vollständig: ${seen.size} Module erreichbar`)
