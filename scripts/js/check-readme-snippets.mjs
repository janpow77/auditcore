#!/usr/bin/env node
// Prüft die Schnellstart-Codeblöcke der npm-Paket-READMEs (docs/bibliotheken/readme-vorlage.md):
//  - jeder ```ts- bzw. ```tsx-Block im Abschnitt „## Schnellstart“ wird mit strengem
//    TypeScript gegen die gebauten Typen der Pakete geprüft (vorher `npm run build`);
//  - Blöcke mit `run` in der Info-Zeile (```ts run) werden zusätzlich in Node ausgeführt;
//  - `no-check` in der Info-Zeile nimmt einen Block aus.
// Pakete aus docs/bibliotheken/readme-offen.json werden übersprungen.
import { execFileSync } from 'node:child_process'
import { mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync, existsSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import ts from 'typescript'

const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..')
// Unterhalb von node_modules: Paketauflösung wie bei einem Consumer, von git ignoriert.
const workDir = join(root, 'node_modules', '.cache', 'readme-snippets')
const pending = new Set(JSON.parse(readFileSync(join(root, 'docs/bibliotheken/readme-offen.json'), 'utf8')).pakete)

function quickStart(text) {
  const match = /^## Schnellstart[ \t]*\n([\s\S]*?)(?=^## |(?![\s\S]))/m.exec(text)
  return match ? match[1] : ''
}

function blocks(text) {
  const found = []
  for (const match of quickStart(text).matchAll(/^```([^\n]*)\n([\s\S]*?)^```\s*$/gm)) {
    const words = match[1].trim().split(/\s+/)
    if (!['ts', 'tsx'].includes(words[0]) || words.includes('no-check')) continue
    found.push({ language: words[0], run: words.includes('run'), code: match[2] })
  }
  return found
}

const compilerOptions = {
  strict: true,
  noUncheckedIndexedAccess: true,
  target: ts.ScriptTarget.ES2022,
  module: ts.ModuleKind.ESNext,
  moduleResolution: ts.ModuleResolutionKind.Bundler,
  jsx: ts.JsxEmit.ReactJSX,
  lib: ['lib.es2022.d.ts', 'lib.dom.d.ts', 'lib.dom.iterable.d.ts'],
  types: [],
  skipLibCheck: true,
  noEmit: true,
  isolatedModules: true,
  moduleDetection: ts.ModuleDetectionKind.Force,
}

function typecheck(files) {
  const program = ts.createProgram(files, compilerOptions)
  const diagnostics = ts.getPreEmitDiagnostics(program)
  const host = { getCanonicalFileName: (f) => f, getCurrentDirectory: () => root, getNewLine: () => '\n' }
  return diagnostics.length ? ts.formatDiagnostics(diagnostics, host) : ''
}

function execute(file, code) {
  const output = ts.transpileModule(code, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } })
  const target = file.replace(/\.tsx?$/, '.mjs')
  writeFileSync(target, output.outputText)
  execFileSync(process.execPath, [target], { stdio: 'inherit', cwd: root })
}

rmSync(workDir, { recursive: true, force: true })
mkdirSync(workDir, { recursive: true })
const files = []
const runnable = []
for (const name of readdirSync(join(root, 'packages-js')).sort()) {
  const readme = join(root, 'packages-js', name, 'README.md')
  if (pending.has(name) || !existsSync(readme)) continue
  blocks(readFileSync(readme, 'utf8')).forEach((block, index) => {
    const file = join(workDir, `${name}-${index + 1}.${block.language}`)
    writeFileSync(file, block.code)
    files.push(file)
    if (block.run) runnable.push({ file, code: block.code })
  })
}

const report = typecheck(files)
if (report) {
  console.error(`README-Schnellstart: Typfehler\n${report}`)
  process.exit(1)
}
for (const { file, code } of runnable) execute(file, code)
console.log(`README-Schnellstart: ${files.length} Blöcke typgeprüft, ${runnable.length} ausgeführt.`)
