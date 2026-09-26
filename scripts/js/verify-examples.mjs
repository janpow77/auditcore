#!/usr/bin/env node
// Installiert und baut die Beispielprojekte unter examples/ wie eine fremde Anwendung:
// frisches Verzeichnis, leere npm-Konfiguration und leerer Cache, @auditcore-Pakete
// ausschließlich aus npm-pack-Tarballs (docs/deployment/frontend-installation.md).
//
//   node scripts/js/verify-examples.mjs                      # Tarballs aus dem Workspace (vorher npm run build)
//   node scripts/js/verify-examples.mjs --base-url <URL>     # Tarballs eines Releases (liest <URL>/npm-packages.json)
//   Optionen: --only vue-minimal,react-minimal  --report <datei.json>  --keep
//
// Geprüft je Beispiel: die aufgeführten @auditcore-Pakete bilden die vollständige
// interne Abhängigkeitshülle, npm löst sie nur aus den Tarballs auf (die Registry ist
// für den Scope gesperrt), package-lock.json trägt genau die erwartete Integrität,
// es gibt keine doppelten @auditcore-Kopien und `npm run build` läuft.
import { execFileSync } from 'node:child_process'
import { cpSync, existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..')
const SCOPE = '@auditcore/'
const BLOCKED_REGISTRY = 'https://npm-registry.invalid/'

function parseArgs(argv) {
  const options = { baseUrl: null, only: null, report: null, keep: false }
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index]
    if (flag === '--keep') options.keep = true
    else if (flag === '--base-url') options.baseUrl = argv[++index].replace(/\/$/, '')
    else if (flag === '--only') options.only = new Set(argv[++index].split(','))
    else if (flag === '--report') options.report = resolve(argv[++index])
    else throw new Error(`Unbekannte Option: ${flag}`)
  }
  return options
}

function internalRequirements(manifest) {
  const optional = new Set(Object.entries(manifest.peerDependenciesMeta ?? {}).filter(([, meta]) => meta?.optional).map(([name]) => name))
  const peers = Object.entries(manifest.peerDependencies ?? {}).filter(([name]) => !optional.has(name))
  return [...Object.keys(manifest.dependencies ?? {}), ...peers.map(([name]) => name)].filter((name) => name.startsWith(SCOPE))
}

/** Tarballs aus dem Workspace packen (Bau muss vorher gelaufen sein). */
function packWorkspace(workDir) {
  const destination = join(workDir, 'tarballs')
  mkdirSync(destination)
  const report = JSON.parse(execFileSync('npm', ['pack', '--workspaces', '--json', '--pack-destination', destination], { cwd: root, stdio: ['ignore', 'pipe', 'inherit'] }))
  const packages = {}
  for (const directory of readdirSync(join(root, 'packages-js'))) {
    const manifestPath = join(root, 'packages-js', directory, 'package.json')
    if (!existsSync(manifestPath)) continue
    const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'))
    const file = `${manifest.name.slice(1).replace('/', '-')}-${manifest.version}.tgz`
    packages[manifest.name] = { version: manifest.version, spec: `file:${join(destination, file)}`, requires: internalRequirements(manifest), integrity: null }
  }
  // Integrität wie npm sie berechnet (Ausgabe von npm pack --json).
  for (const entry of report) packages[entry.name].integrity = entry.integrity
  return { mode: 'workspace', source: 'npm pack --workspaces', packages }
}

/** Release-Manifest npm-packages.json lesen (scripts/prepare_library_release.py). */
async function releasePackages(baseUrl) {
  const response = await fetch(`${baseUrl}/npm-packages.json`)
  if (!response.ok) throw new Error(`${baseUrl}/npm-packages.json: HTTP ${response.status}`)
  const manifest = await response.json()
  const packages = {}
  for (const item of manifest.packages) {
    packages[item.name] = { version: item.version, spec: `${baseUrl}/${item.file}`, requires: Object.keys(item.internal_requirements), integrity: item.integrity }
  }
  return { mode: 'release', source: baseUrl, release_version: manifest.release_version, source_commit: manifest.source_commit, packages }
}

function closure(names, packages) {
  const seen = new Set()
  const pending = [...names]
  while (pending.length) {
    const name = pending.pop()
    if (seen.has(name)) continue
    if (!packages[name]) throw new Error(`${name} ist kein Paket des Releases`)
    seen.add(name)
    pending.push(...packages[name].requires)
  }
  return seen
}

function prepareExample(name, workDir, packages) {
  const target = join(workDir, 'apps', name)
  cpSync(join(root, 'examples', name), target, { recursive: true, filter: (path) => !/(^|\/)(node_modules|dist)(\/|$)/.test(path.slice(root.length)) })
  const manifest = JSON.parse(readFileSync(join(target, 'package.json'), 'utf8'))
  const listed = Object.keys(manifest.dependencies ?? {}).filter((dependency) => dependency.startsWith(SCOPE))
  const missing = [...closure(listed, packages)].filter((dependency) => !listed.includes(dependency))
  if (missing.length) throw new Error(`${name}: interne Abhängigkeiten fehlen in package.json: ${missing.join(', ')}`)
  for (const dependency of listed) manifest.dependencies[dependency] = packages[dependency].spec
  writeFileSync(join(target, 'package.json'), `${JSON.stringify(manifest, null, 2)}\n`)
  // Wie in der Anleitung empfohlen: Registry für den Scope sperren (kein Nachladen gleichnamiger Fremdpakete).
  writeFileSync(join(target, '.npmrc'), `@auditcore:registry=${BLOCKED_REGISTRY}\n`)
  return { target, listed }
}

/** `resolved` aus package-lock.json in derselben Form wie die Angabe in package.json. */
function resolvedSpec(target, resolved) {
  return resolved?.startsWith('file:') ? `file:${resolve(target, resolved.slice(5))}` : resolved
}

function checkLock(target, listed, packages) {
  const lock = JSON.parse(readFileSync(join(target, 'package-lock.json'), 'utf8'))
  const found = []
  for (const [path, node] of Object.entries(lock.packages)) {
    const match = /(?:^|\/)node_modules\/(@auditcore\/[^/]+)$/.exec(path)
    if (!match) continue
    const expected = packages[match[1]]
    if (path !== `node_modules/${match[1]}`) throw new Error(`Doppelte Kopie ${path}`)
    if (!expected || node.version !== expected.version) throw new Error(`${match[1]}: unerwartete Version ${node.version}`)
    if (expected.integrity && node.integrity !== expected.integrity) throw new Error(`${match[1]}: Integrität ${node.integrity} statt ${expected.integrity}`)
    if (resolvedSpec(target, node.resolved) !== expected.spec) {
      throw new Error(`${match[1]}: aufgelöst aus ${node.resolved} statt ${expected.spec}`)
    }
    found.push({ name: match[1], version: node.version, integrity: node.integrity, resolved: node.resolved })
  }
  if (found.length !== listed.length) throw new Error(`Lock enthält ${found.length} statt ${listed.length} @auditcore-Pakete`)
  return found
}

function verifyExample(name, workDir, packages) {
  const { target, listed } = prepareExample(name, workDir, packages)
  const env = { ...process.env, npm_config_userconfig: join(workDir, 'empty-npmrc'), npm_config_cache: join(workDir, 'npm-cache'), npm_config_audit: 'false', npm_config_fund: 'false', npm_config_update_notifier: 'false' }
  const started = Date.now()
  execFileSync('npm', ['install'], { cwd: target, env, stdio: 'inherit' })
  const installed = checkLock(target, listed, packages)
  execFileSync('npm', ['run', 'build'], { cwd: target, env, stdio: 'inherit' })
  return { example: name, status: 'PASS', auditcore_packages: installed, install_and_build_seconds: Math.round((Date.now() - started) / 1000) }
}

async function main() {
  const options = parseArgs(process.argv.slice(2))
  const workDir = mkdtempSync(join(tmpdir(), 'auditcore-examples-'))
  writeFileSync(join(workDir, 'empty-npmrc'), '')
  try {
    const release = options.baseUrl ? await releasePackages(options.baseUrl) : packWorkspace(workDir)
    const examples = readdirSync(join(root, 'examples')).filter((name) => existsSync(join(root, 'examples', name, 'package.json')) && (!options.only || options.only.has(name)))
    const results = examples.map((name) => verifyExample(name, workDir, release.packages))
    const report = {
      scope: 'NPM_TARBALL_INSTALLATION',
      status: 'PASS',
      mode: release.mode,
      source: release.source,
      release_version: release.release_version ?? null,
      source_commit: release.source_commit ?? null,
      node: process.version,
      npm: execFileSync('npm', ['--version']).toString().trim(),
      method: 'frisches Verzeichnis, leere npm-Konfiguration und leerer Cache, @auditcore-Registry gesperrt, npm install, Abgleich package-lock.json, npm run build',
      examples: results,
      registry_publication: 'NOT_EXECUTED',
      checked_at: new Date().toISOString(),
    }
    if (options.report) writeFileSync(options.report, `${JSON.stringify(report, null, 2)}\n`)
    console.log(`Beispiele: ${results.map((result) => `${result.example} ${result.status}`).join(', ')}`)
  } finally {
    if (options.keep) console.log(`Arbeitsverzeichnis: ${workDir}`)
    else rmSync(workDir, { recursive: true, force: true })
  }
}

await main()
