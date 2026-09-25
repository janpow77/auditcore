// Executes TypeScript/JavaScript helper functions for auditcore-helpers.
// Input (stdin, JSON):
//   {"mode": "contracts", "module": "/abs/file.ts", "export": "name", "calls": [{"id", "args"}]}
//   {"mode": "probe", "functions": [{"id", "name", "kind", "source", "prelude": []}], "calls": [...]}
// Output (file AUDITCORE_HELPERS_OUTPUT, JSON): {"results": {...}} or {"load_error": "..."}.
// Special values are encoded as {"$undefined"}, {"$nan"}, {"$date"}, {"$error"}.
import { createRequire } from 'node:module'
import { readFileSync, existsSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { pathToFileURL } from 'node:url'
import vm from 'node:vm'

const toolchain = process.env.AUDITCORE_HELPERS_TOOLCHAIN
if (!toolchain) throw new Error('AUDITCORE_HELPERS_TOOLCHAIN is not set')
const requireFromToolchain = createRequire(join(toolchain, 'package.json'))
const PROBE_TIMEOUT_MS = 1000
const MAX_MESSAGE = 160

// First line of an error message, shortened and without echoed input values (secrets).
export function describeError(error) {
  const first = String(error?.message ?? error).trim().split('\n')[0] ?? ''
  const text = first.replace(/(input_value|input)\s*=\s*('[^']*'|"[^"]*"|\S+)/g, '$1=***')
  return text.length <= MAX_MESSAGE ? text : `${text.slice(0, MAX_MESSAGE - 1)}…`
}

export function decode(value) {
  if (Array.isArray(value)) return value.map(decode)
  if (value === null || typeof value !== 'object') return value
  if (value.$undefined) return undefined
  if (value.$nan) return Number.NaN
  if (typeof value.$date === 'string') return new Date(value.$date)
  if (typeof value.$error === 'string') return new Error(value.$error)
  return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, decode(item)]))
}

export function encode(value, depth = 0) {
  if (value === undefined) return { $undefined: true }
  if (typeof value === 'number' && Number.isNaN(value)) return { $nan: true }
  if (typeof value === 'bigint') return String(value)
  const tag = Object.prototype.toString.call(value)
  if (tag === '[object Date]') return { $date: Number.isNaN(value.getTime()) ? 'Invalid Date' : value.toISOString() }
  if (tag === '[object Error]') return { $error: String(value.message) }
  if (value === null || typeof value !== 'object') return typeof value === 'function' ? String(value) : value
  if (depth > 6) return String(value)
  if (Array.isArray(value)) return value.map((item) => encode(item, depth + 1))
  return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, encode(item, depth + 1)]))
}

async function callAll(fn, calls) {
  const results = {}
  for (const call of calls) {
    try {
      let value = fn(...decode(call.args))
      if (value && typeof value.then === 'function') value = await value
      results[call.id] = { value: encode(value) }
    } catch (error) {
      results[call.id] = { error: describeError(error) }
    }
  }
  return results
}

function pick(module, name) {
  let current = module
  for (const part of name.split('.')) {
    if (current === null || current === undefined) return undefined
    current = current[part]
  }
  return current
}

async function loadModule(file) {
  const apiPath = requireFromToolchain.resolve('tsx/esm/api').replace(/\.cjs$/, '.mjs')
  const api = await import(pathToFileURL(existsSync(apiPath) ? apiPath : requireFromToolchain.resolve('tsx/esm/api')).href)
  return api.tsImport(pathToFileURL(file).href, import.meta.url)
}

async function runContracts(request) {
  let module
  try {
    module = await loadModule(request.module)
  } catch (error) {
    return { load_error: `Modul nicht ladbar: ${describeError(error)}` }
  }
  const fn = pick(module, request.export)
  if (typeof fn !== 'function') return { load_error: `Export „${request.export}“ ist keine Funktion` }
  return { results: await callAll(fn, request.calls) }
}

// Turns an extracted function text into a standalone script that yields the function.
export function standalone(fn) {
  const source = fn.source.replace(/^export\s+(default\s+)?/, '')
  const body = fn.kind === 'variable' && !/^(const|let|var)\s/.test(source) ? `const ${source}` : source
  return `${fn.prelude.join('\n')}\n${body}\n;globalThis.__probe = ${fn.name};`
}

function probeOne(ts, fn, calls) {
  let compiled
  try {
    const options = { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None, jsx: ts.JsxEmit.Preserve }
    compiled = ts.transpileModule(standalone(fn), { compilerOptions: options }).outputText
    const context = vm.createContext({})
    vm.runInContext(compiled, context, { timeout: PROBE_TIMEOUT_MS })
    const target = context.__probe
    if (typeof target !== 'function') return { isolated: false, reason: 'keine Funktion' }
    const results = {}
    for (const call of calls) {
      try {
        const value = vm.runInContext('__probe(...__args)', Object.assign(context, { __args: decode(call.args) }),
          { timeout: PROBE_TIMEOUT_MS })
        results[call.id] = { value: encode(value) }
      } catch (error) {
        if (error?.name === 'ReferenceError') return { isolated: false, reason: describeError(error) }
        results[call.id] = { error: describeError(error) }
      }
    }
    return { isolated: true, results }
  } catch (error) {
    return { isolated: false, reason: describeError(error) }
  }
}

function runProbe(request) {
  const ts = requireFromToolchain('typescript')
  const results = {}
  for (const fn of request.functions) results[fn.id] = probeOne(ts, fn, request.calls)
  return { results }
}

async function main() {
  const request = JSON.parse(readFileSync(0, 'utf8'))
  const response = request.mode === 'probe' ? runProbe(request) : await runContracts(request)
  // Written to a file so that console output of the loaded app modules cannot corrupt it.
  writeFileSync(process.env.AUDITCORE_HELPERS_OUTPUT, JSON.stringify(response))
}

await main()
