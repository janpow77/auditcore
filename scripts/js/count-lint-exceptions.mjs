#!/usr/bin/env node
/**
 * Zählt ESLint-Ausnahmen (`eslint-disable…`) in packages-js und gibt sie aus.
 * Dateiweite Ausnahmen (Block-Kommentar am Dateianfang) sind unzulässig.
 */

import { readdirSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join, relative } from 'node:path'

const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..')
const base = join(root, 'packages-js')

function files(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    if (['node_modules', 'dist', 'coverage'].includes(entry.name)) return []
    const path = join(dir, entry.name)
    if (entry.isDirectory()) return files(path)
    return /\.(ts|tsx|mts|vue|js|mjs)$/.test(entry.name) ? [path] : []
  })
}

let count = 0
let fileWide = 0
for (const file of files(base)) {
  readFileSync(file, 'utf8')
    .split('\n')
    .forEach((line, index) => {
      if (!line.includes('eslint-disable')) return
      count++
      const isFileWide = /\/\*\s*eslint-disable(?!-)/.test(line)
      if (isFileWide) fileWide++
      console.log(`${relative(root, file)}:${index + 1}: ${line.trim()}${isFileWide ? '  ← dateiweit (unzulässig)' : ''}`)
    })
}
console.log(`ESLint-Ausnahmen gesamt: ${count} (davon dateiweit: ${fileWide})`)
if (fileWide > 0) process.exit(1)
