// Extracts functions from TS/JS/Vue sources with the TypeScript compiler API.
// Input (stdin, JSON): {"root": "/abs/repo", "files": ["rel/path.ts", ...]}
// Output (file AUDITCORE_HELPERS_OUTPUT, JSON): {"functions": [...], "constants": {file: [{name, text}]}, "errors": [...]}
// The toolchain directory (node_modules with typescript) is passed in
// AUDITCORE_HELPERS_TOOLCHAIN.
import { createRequire } from 'node:module'
import { createHash } from 'node:crypto'
import { readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'

const toolchain = process.env.AUDITCORE_HELPERS_TOOLCHAIN
if (!toolchain) throw new Error('AUDITCORE_HELPERS_TOOLCHAIN is not set')
const ts = createRequire(join(toolchain, 'package.json'))('typescript')

// Identifiers that keep their name during normalisation (browser and framework globals).
const GLOBALS = new Set(['Intl', 'Math', 'Number', 'String', 'Date', 'JSON', 'Object', 'Array', 'Promise', 'URL',
  'Blob', 'document', 'window', 'localStorage', 'sessionStorage', 'setTimeout', 'clearTimeout', 'fetch', 'FormData',
  'console', 'parseFloat', 'parseInt', 'isNaN', 'RegExp', 'encodeURIComponent', 'decodeURIComponent', 'navigator',
  'undefined', 'Error', 'Set', 'Map', 'Boolean', 'Symbol', 'crypto', 'axios', 'ref', 'computed', 'watch', 'useState',
  'useEffect', 'useRef', 'useCallback', 'useMemo', 'onMounted', 'onUnmounted', 'reactive', 'nextTick'])
const MAX_SOURCE = 20000

function scriptKind(file) {
  if (file.endsWith('.tsx')) return ts.ScriptKind.TSX
  if (file.endsWith('.jsx')) return ts.ScriptKind.JSX
  if (/\.[mc]?js$/.test(file)) return ts.ScriptKind.JS
  return ts.ScriptKind.TS
}

// Returns the script blocks of a file; Vue SFCs contribute each <script> block.
export function scriptBlocks(file, text) {
  if (!file.endsWith('.vue')) return [{ code: text, offsetLine: 0, kind: scriptKind(file) }]
  const blocks = []
  const pattern = /<script([^>]*)>([\s\S]*?)<\/script>/g
  let match
  while ((match = pattern.exec(text))) {
    const attrs = match[1]
    const start = match.index + match[0].indexOf('>') + 1
    const offsetLine = text.slice(0, start).split('\n').length - 1
    const kind = /lang=["']tsx["']/.test(attrs) ? ts.ScriptKind.TSX
      : /lang=["']ts["']/.test(attrs) ? ts.ScriptKind.TS : ts.ScriptKind.JS
    blocks.push({ code: match[2], offsetLine, kind })
  }
  return blocks
}

function stripTypes(code) {
  try {
    const options = { target: ts.ScriptTarget.ESNext, jsx: ts.JsxEmit.Preserve, removeComments: true }
    return ts.transpileModule(code, { compilerOptions: options, reportDiagnostics: false }).outputText
  } catch {
    return code
  }
}

// Normalised token stream: types removed, local names alpha-renamed, strings neutralised.
export function normalisedTokens(code) {
  const scanner = ts.createScanner(ts.ScriptTarget.ESNext, true, ts.LanguageVariant.JSX, stripTypes(code))
  const tokens = []
  const names = new Map()
  let previous = null
  for (let kind = scanner.scan(); kind !== ts.SyntaxKind.EndOfFileToken; kind = scanner.scan()) {
    let value = scanner.getTokenText()
    if (kind === ts.SyntaxKind.Identifier && previous !== '.' && previous !== '?.' && !GLOBALS.has(value)) {
      if (!names.has(value)) names.set(value, `$${names.size}`)
      value = names.get(value)
    } else if (kind === ts.SyntaxKind.StringLiteral || kind === ts.SyntaxKind.NoSubstitutionTemplateLiteral) {
      value = 'S'
    }
    tokens.push(value)
    previous = value
  }
  return tokens
}

function isFunctionLike(node) {
  return node && (ts.isArrowFunction(node) || ts.isFunctionExpression(node) || ts.isMethodDeclaration(node))
}

// Returns {name, fn, kind} when the node defines a named function, else null.
function functionOf(node, context) {
  if (ts.isFunctionDeclaration(node) && node.body) {
    return { name: node.name?.text ?? 'default', fn: node, kind: 'declaration' }
  }
  if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && isFunctionLike(node.initializer)) {
    return { name: node.name.text, fn: node.initializer, kind: 'variable' }
  }
  const member = ts.isMethodDeclaration(node) || ts.isPropertyAssignment(node) || ts.isPropertyDeclaration(node)
  if (member && node.name && ts.isIdentifier(node.name)) {
    const fn = ts.isMethodDeclaration(node) ? node : node.initializer
    if (isFunctionLike(fn) && fn.body) {
      return { name: (context ? `${context}.` : '') + node.name.text, fn, kind: 'method' }
    }
  }
  return null
}

function isExported(node) {
  let current = node
  while (current) {
    if (current.modifiers?.some((modifier) => modifier.kind === ts.SyntaxKind.ExportKeyword)) return true
    current = ts.isVariableDeclaration(current) ? current.parent?.parent : null
  }
  return false
}

function literalish(node) {
  if (!node) return false
  if (ts.isRegularExpressionLiteral(node) || ts.isStringLiteral(node) || ts.isNumericLiteral(node)) return true
  if (ts.isNoSubstitutionTemplateLiteral(node)) return true
  if (ts.isArrayLiteralExpression(node)) return node.elements.every(literalish)
  if (ts.isNewExpression(node) && node.expression.getText() === 'RegExp') return (node.arguments ?? []).every(literalish)
  if (ts.isAsExpression(node)) return literalish(node.expression)
  return false
}

// Top-level literal constants and functions a probed helper may reference.
function topLevelDefinitions(sourceFile) {
  const definitions = []
  for (const statement of sourceFile.statements) {
    if (ts.isFunctionDeclaration(statement) && statement.name && statement.body) {
      const text = statement.getText(sourceFile).replace(/^export\s+(default\s+)?/, '')
      definitions.push({ name: statement.name.text, text })
      continue
    }
    if (!ts.isVariableStatement(statement)) continue
    for (const declaration of statement.declarationList.declarations) {
      const init = declaration.initializer
      if (ts.isIdentifier(declaration.name) && (literalish(init) || isFunctionLike(init))) {
        definitions.push({ name: declaration.name.text, text: `const ${declaration.getText(sourceFile)}` })
      }
    }
  }
  return definitions
}

function hash(tokens) {
  return createHash('sha1').update(tokens.join(' ')).digest('hex').slice(0, 16)
}

function record(file, block, sourceFile, node, found) {
  const text = node.getText(sourceFile)
  const start = sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile)).line
  const end = sourceFile.getLineAndCharacterOfPosition(node.getEnd()).line
  const full = ts.isVariableDeclaration(node) ? `const ${text}` : text
  const tokens = normalisedTokens(full)
  return {
    path: file,
    name: found.name,
    kind: found.kind,
    line: start + 1 + block.offsetLine,
    end_line: end + 1 + block.offsetLine,
    exported: isExported(node),
    params: found.fn.parameters.length,
    tokens: tokens.length,
    body_hash: hash(tokens),
    source: full.length > MAX_SOURCE ? full.slice(0, MAX_SOURCE) : full,
  }
}

function scanBlock(file, block, functions) {
  const sourceFile = ts.createSourceFile(file, block.code, ts.ScriptTarget.ESNext, true, block.kind)
  const visit = (node, context, nested) => {
    const found = functionOf(node, context)
    if (found) functions.push({ ...record(file, block, sourceFile, node, found), nested })
    const nextContext = ts.isClassDeclaration(node) && node.name ? node.name.text : context
    ts.forEachChild(node, (child) => visit(child, found ? found.name : nextContext, nested || Boolean(found)))
  }
  visit(sourceFile, null, false)
  return topLevelDefinitions(sourceFile)
}

function main() {
  const request = JSON.parse(readFileSync(0, 'utf8'))
  const functions = []
  const constants = {}
  const errors = []
  for (const file of request.files) {
    try {
      const text = readFileSync(join(request.root, file), 'utf8')
      const collected = []
      for (const block of scriptBlocks(file, text)) collected.push(...scanBlock(file, block, functions))
      if (collected.length) constants[file] = collected
    } catch (error) {
      errors.push({ path: file, error: String(error?.message ?? error) })
    }
  }
  writeFileSync(process.env.AUDITCORE_HELPERS_OUTPUT, JSON.stringify({ functions, constants, errors }))
}

main()
