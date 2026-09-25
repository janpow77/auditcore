#!/usr/bin/env node
// Statische API-Erfassung eines npm-Pakets unter packages-js/ (TypeScript-Compiler-API,
// nichts wird ausgeführt). Ausgabe als JSON auf stdout; scripts/docs/api_overview.py
// rendert daraus den README-Abschnitt „API-Überblick“.
//
// Aufruf: node scripts/docs/js_api.mjs packages-js/<paket>
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs'
import { dirname, join, relative, resolve } from 'node:path'
import process from 'node:process'
import ts from 'typescript'

const packageDir = resolve(process.argv[2] ?? '.')
// Codepunkt-Ordnung statt localeCompare: gleiche Ausgabe unter jeder Node-/ICU-Version.
const byText = (a, b) => (a < b ? -1 : a > b ? 1 : 0)
const manifest = JSON.parse(readFileSync(join(packageDir, 'package.json'), 'utf8'))

/** Einstiegspunkte aus package.json#exports: './dist/x.js' → 'src/x.ts'. */
function entryPoints() {
  const exportsField = manifest.exports ?? { '.': { import: manifest.module ?? manifest.main } }
  const entries = []
  for (const [key, value] of Object.entries(exportsField)) {
    const target = typeof value === 'string' ? value : value?.import
    if (typeof target !== 'string' || !target.endsWith('.js')) continue
    const source = target.replace(/^\.\/dist\//, 'src/').replace(/\.js$/, '')
    for (const extension of ['.ts', '.tsx']) {
      const file = join(packageDir, source + extension)
      if (existsSync(file)) entries.push({ key, file })
    }
  }
  return entries
}

function firstParagraph(text) {
  const paragraph = text.trim().split(/\n\s*\n/)[0] ?? ''
  const line = paragraph.split('\n').map((part) => part.trim()).join(' ')
  if (line.length <= 180) return line
  const cut = line.slice(0, 180)
  const end = cut.lastIndexOf('. ')
  return end > 40 ? cut.slice(0, end + 1) : `${cut.trimEnd()} …`
}

function docOf(symbol, checker) {
  return firstParagraph(ts.displayPartsToString(symbol.getDocumentationComment(checker)))
}

function vueSource(symbol) {
  for (const declaration of symbol.declarations ?? []) {
    const exportDeclaration = declaration.parent?.parent
    const specifier = exportDeclaration?.moduleSpecifier
    if (specifier && ts.isStringLiteral(specifier) && specifier.text.endsWith('.vue')) {
      return resolve(dirname(declaration.getSourceFile().fileName), specifier.text)
    }
  }
  return undefined
}

function reExportSource(symbol) {
  const specifier = symbol.declarations?.[0]?.parent?.parent?.moduleSpecifier
  return specifier && ts.isStringLiteral(specifier) ? specifier.text : ''
}

function isFunctionLike(declaration) {
  const initializer = declaration && ts.isVariableDeclaration(declaration) ? declaration.initializer : undefined
  return Boolean(initializer && (ts.isArrowFunction(initializer) || ts.isFunctionExpression(initializer)))
}

function kindOf(symbol) {
  const flags = symbol.flags
  if (flags & ts.SymbolFlags.Class) return 'Klasse'
  if (flags & ts.SymbolFlags.Function) return 'Funktion'
  if (flags & ts.SymbolFlags.Interface) return 'Schnittstelle'
  if (flags & ts.SymbolFlags.TypeAlias) return 'Typ'
  if (flags & ts.SymbolFlags.Enum) return 'Aufzählung'
  if (flags & ts.SymbolFlags.Variable) {
    return isFunctionLike(symbol.valueDeclaration) ? 'Funktion' : 'Konstante'
  }
  return 'Re-Export'
}

function moduleOf(symbol) {
  const file = symbol.declarations?.[0]?.getSourceFile().fileName
  if (!file || file.includes('node_modules')) return ''
  return relative(join(packageDir, 'src'), file).replace(/\.(ts|tsx)$/, '')
}

function describeExport(exported, checker, components) {
  const vue = vueSource(exported)
  if (vue) {
    components.set(exported.name, vue)
    return { name: exported.name, kind: 'Vue-Komponente', summary: '', module: relative(join(packageDir, 'src'), vue) }
  }
  let target = exported
  if (exported.flags & ts.SymbolFlags.Alias) {
    const aliased = checker.getAliasedSymbol(exported)
    if (aliased?.declarations?.length) target = aliased
  }
  const kind = target.declarations?.length ? kindOf(target) : 'Re-Export'
  if (kind === 'Re-Export') return { name: exported.name, kind, summary: '', module: reExportSource(exported) }
  return { name: exported.name, kind, summary: docOf(target, checker), module: moduleOf(target) }
}

function collectEntries() {
  const entries = entryPoints()
  const program = ts.createProgram(entries.map((entry) => entry.file), {
    target: ts.ScriptTarget.ES2022,
    module: ts.ModuleKind.ESNext,
    moduleResolution: ts.ModuleResolutionKind.Bundler,
    jsx: ts.JsxEmit.Preserve,
    allowJs: false,
    noEmit: true,
    skipLibCheck: true,
  })
  const checker = program.getTypeChecker()
  const components = new Map()
  const result = []
  for (const entry of entries) {
    const source = program.getSourceFile(entry.file)
    const moduleSymbol = source && checker.getSymbolAtLocation(source)
    if (!moduleSymbol) continue
    const exported = checker.getExportsOfModule(moduleSymbol)
      .map((symbol) => ({ entry: entry.key, ...describeExport(symbol, checker, components) }))
      .sort((a, b) => byText(a.name, b.name))
    result.push(...exported)
  }
  return { result, components }
}

// ---------- Vue-SFC: Props und Events aus defineProps/defineEmits ----------

function jsDocText(node) {
  const docs = ts.getJSDocCommentsAndTags(node).filter(ts.isJSDoc)
  return firstParagraph(docs.map((doc) => (typeof doc.comment === 'string' ? doc.comment : ts.getTextOfJSDocComment(doc.comment) ?? '')).join('\n'))
}

function typeMembers(typeNode, source) {
  if (!typeNode) return []
  if (ts.isTypeLiteralNode(typeNode)) return typeNode.members
  if (ts.isTypeReferenceNode(typeNode)) {
    const name = typeNode.typeName.getText(source)
    for (const statement of source.statements) {
      if (ts.isInterfaceDeclaration(statement) && statement.name.text === name) return statement.members
      if (ts.isTypeAliasDeclaration(statement) && statement.name.text === name) return typeMembers(statement.type, source)
    }
  }
  return []
}

function defaultsOf(call, source) {
  const defaults = new Map()
  const object = call?.arguments?.[1]
  if (!object || !ts.isObjectLiteralExpression(object)) return defaults
  for (const property of object.properties) {
    if (ts.isPropertyAssignment(property)) defaults.set(property.name.getText(source), property.initializer.getText(source))
  }
  return defaults
}

function findCalls(source) {
  const calls = {}
  const visit = (node) => {
    if (ts.isCallExpression(node) && ts.isIdentifier(node.expression)) {
      const name = node.expression.text
      if (name === 'defineProps' || name === 'defineEmits' || name === 'withDefaults') calls[name] ??= node
    }
    ts.forEachChild(node, visit)
  }
  visit(source)
  return calls
}

function propsOf(calls, source) {
  const defaults = defaultsOf(calls.withDefaults, source)
  return typeMembers(calls.defineProps?.typeArguments?.[0], source)
    .filter(ts.isPropertySignature)
    .map((member) => {
      const name = member.name.getText(source)
      return {
        name,
        type: member.type ? member.type.getText(source).replace(/\s+/g, ' ') : '',
        required: !member.questionToken,
        default: defaults.get(name) ?? '',
        doc: jsDocText(member),
      }
    })
}

function eventsOf(calls, source) {
  const events = []
  for (const member of typeMembers(calls.defineEmits?.typeArguments?.[0], source)) {
    if (ts.isPropertySignature(member)) {
      events.push({ name: member.name.getText(source).replace(/['"]/g, ''), payload: member.type?.getText(source).replace(/\s+/g, ' ') ?? '', doc: jsDocText(member) })
    } else if (ts.isCallSignatureDeclaration(member)) {
      const [first, ...rest] = member.parameters
      const literal = first?.type && ts.isLiteralTypeNode(first.type) ? first.type.literal : undefined
      if (literal && ts.isStringLiteral(literal)) {
        events.push({ name: literal.text, payload: `[${rest.map((p) => p.getText(source)).join(', ')}]`, doc: jsDocText(member) })
      }
    }
  }
  return events
}

function componentApi(name, file) {
  const text = readFileSync(file, 'utf8')
  const script = /<script\s+setup[^>]*>([\s\S]*?)<\/script>/.exec(text)?.[1] ?? ''
  const source = ts.createSourceFile(file, script, ts.ScriptTarget.ES2022, true, ts.ScriptKind.TS)
  const calls = findCalls(source)
  const leading = /^\s*<!--([\s\S]*?)-->/.exec(text)?.[1] ?? ''
  return { name, summary: firstParagraph(leading), props: propsOf(calls, source), events: eventsOf(calls, source) }
}

// ---------- Web Components (ElementDefinition-Objekte) ----------

function sourceFiles(directory) {
  return readdirSync(directory).flatMap((name) => {
    const path = join(directory, name)
    if (statSync(path).isDirectory()) return sourceFiles(path)
    return /\.(ts|tsx)$/.test(name) && !name.endsWith('.spec.ts') ? [path] : []
  })
}

function webComponents() {
  const found = []
  const pattern = /tag:\s*'(flowaudit-[a-z0-9-]+)'[^}]*?component:\s*([A-Za-z0-9_]+)/g
  for (const file of sourceFiles(join(packageDir, 'src'))) {
    for (const match of readFileSync(file, 'utf8').matchAll(pattern)) {
      found.push({ tag: match[1], component: match[2], module: relative(join(packageDir, 'src'), file) })
    }
  }
  return found.sort((a, b) => byText(a.tag, b.tag))
}

const { result, components } = collectEntries()
const componentList = [...components.entries()]
  .sort(([a], [b]) => byText(a, b))
  .map(([name, file]) => componentApi(name, file))
process.stdout.write(JSON.stringify({ name: manifest.name, entries: result, components: componentList, elements: webComponents() }, null, 2))
