/**
 * Statische Erfassung der öffentlichen Komponenten eines Vue- und eines
 * React-Pakets mit der TypeScript-Compiler-API (nichts wird ausgeführt).
 */
import { existsSync, readFileSync, statSync } from 'node:fs'
import { dirname, join, relative, resolve } from 'node:path'
import ts from 'typescript'

const COMPILER_OPTIONS = {
  target: ts.ScriptTarget.ES2022,
  module: ts.ModuleKind.ESNext,
  moduleResolution: ts.ModuleResolutionKind.Bundler,
  jsx: ts.JsxEmit.Preserve,
  noEmit: true,
  skipLibCheck: true,
  noResolve: false,
}

export const posix = (path) => path.split('\\').join('/')

export function readJson(file) {
  return JSON.parse(readFileSync(file, 'utf8'))
}

/** Einstiegspunkte aus `package.json#exports` (`./dist/x.d.ts` → `src/x.ts`). */
export function entryFiles(packageDir) {
  const manifest = readJson(join(packageDir, 'package.json'))
  const exportsField = manifest.exports ?? { '.': { types: manifest.types } }
  const files = new Set()
  for (const value of Object.values(exportsField)) {
    const target = typeof value === 'string' ? value : value?.types ?? value?.import
    if (typeof target !== 'string') continue
    const source = target.replace(/^\.\/dist[^/]*\//, 'src/').replace(/(\.d)?\.(ts|js)$/, '')
    for (const extension of ['.ts', '.tsx']) {
      if (existsSync(join(packageDir, source + extension))) files.add(join(packageDir, source + extension))
    }
  }
  return [...files]
}

function exportedSymbols(files) {
  const program = ts.createProgram(files, COMPILER_OPTIONS)
  const checker = program.getTypeChecker()
  const symbols = []
  for (const file of files) {
    const source = program.getSourceFile(file)
    const moduleSymbol = source && checker.getSymbolAtLocation(source)
    if (moduleSymbol) symbols.push(...checker.getExportsOfModule(moduleSymbol))
  }
  return { checker, symbols }
}

/** Pfad der `.vue`-Datei, aus der ein Export (`export { default as X } from './X.vue'`) stammt. */
function vueSource(symbol) {
  for (const declaration of symbol.declarations ?? []) {
    const specifier = declaration.parent?.parent?.moduleSpecifier
    if (specifier && ts.isStringLiteral(specifier) && specifier.text.endsWith('.vue')) {
      return resolve(dirname(declaration.getSourceFile().fileName), specifier.text)
    }
  }
  return undefined
}

function target(symbol, checker) {
  if (!(symbol.flags & ts.SymbolFlags.Alias)) return symbol
  const aliased = checker.getAliasedSymbol(symbol)
  return aliased?.declarations?.length ? aliased : symbol
}

/** `export const XElement = defineCustomElement(...)` → Web Component `X`. */
function customElementName(symbol) {
  const declaration = symbol.valueDeclaration
  if (!declaration || !ts.isVariableDeclaration(declaration)) return undefined
  const init = declaration.initializer
  const isDefine = init && ts.isCallExpression(init) && ts.isIdentifier(init.expression) && init.expression.text === 'defineCustomElement'
  return isDefine && symbol.name.endsWith('Element') ? symbol.name.slice(0, -'Element'.length) : undefined
}

/**
 * Öffentliche Vue-Komponenten: `.vue`-Exporte aller Einstiegspunkte und
 * per `defineCustomElement` erzeugte Web Components.
 * @returns {{ name: string, file: string, customElement: boolean }[]}
 */
export function vueComponents(packageDir) {
  const { checker, symbols } = exportedSymbols(entryFiles(packageDir))
  const found = new Map()
  for (const symbol of symbols) {
    const file = vueSource(symbol)
    if (file) {
      found.set(symbol.name, { name: symbol.name, file, customElement: false })
      continue
    }
    const resolved = target(symbol, checker)
    const element = customElementName(resolved)
    const declared = resolved.valueDeclaration?.getSourceFile().fileName
    if (element && declared) found.set(element, { name: element, file: declared, customElement: true })
  }
  return [...found.values()].sort((a, b) => (a.name < b.name ? -1 : 1))
}

const isComponentName = (name) => /^[A-Z][A-Za-z0-9]*$/.test(name) && !name.endsWith('Provider')

/**
 * Öffentliche React-Komponenten: Werte-Exporte mit großem Anfangsbuchstaben,
 * deklariert in einer `.tsx`-Datei des Pakets (Kontext-Provider ausgenommen:
 * Vue nutzt dafür `provide`/Plugins).
 * @returns {{ name: string, file: string }[]}
 */
export function reactComponents(packageDir) {
  const { checker, symbols } = exportedSymbols(entryFiles(packageDir))
  const src = join(packageDir, 'src')
  const found = []
  for (const symbol of symbols) {
    const resolved = target(symbol, checker)
    const isValue = resolved.flags & (ts.SymbolFlags.Function | ts.SymbolFlags.Variable)
    const file = resolved.valueDeclaration?.getSourceFile().fileName ?? ''
    if (!isValue || !file.endsWith('.tsx') || !file.startsWith(src) || !isComponentName(symbol.name)) continue
    found.push({ name: symbol.name, file })
  }
  return found.sort((a, b) => (a.name < b.name ? -1 : 1))
}

function parse(file) {
  return ts.createSourceFile(file, readFileSync(file, 'utf8'), ts.ScriptTarget.ES2022, true)
}

/** Import-Bezeichner → aufgelöster Pfad (nur relative Imports). */
function importMap(source) {
  const map = new Map()
  for (const statement of source.statements) {
    if (!ts.isImportDeclaration(statement) || !ts.isStringLiteral(statement.moduleSpecifier)) continue
    const path = resolveModule(source.fileName, statement.moduleSpecifier.text)
    const clause = statement.importClause
    if (!path || !clause) continue
    if (clause.name) map.set(clause.name.text, path)
    const bindings = clause.namedBindings
    if (bindings && ts.isNamedImports(bindings)) for (const element of bindings.elements) map.set(element.name.text, path)
  }
  return map
}

/** Relativen Modulpfad wie der Bundler auflösen (Endung ergänzen, `index.ts`). */
export function resolveModule(fromFile, specifier) {
  if (!specifier.startsWith('.')) return undefined
  const base = resolve(dirname(fromFile), specifier)
  const candidates = [base, `${base}.ts`, `${base}.tsx`, join(base, 'index.ts'), join(base, 'index.tsx')]
  return candidates.find((candidate) => existsSync(candidate) && statSync(candidate).isFile()) ?? base
}

function objectProperty(object, name) {
  const property = object.properties.find((entry) => ts.isPropertyAssignment(entry) && entry.name.getText() === name)
  return property && ts.isPropertyAssignment(property) ? property.initializer : undefined
}

function elementDefinition(file, name) {
  const source = parse(file)
  const imports = importMap(source)
  let found
  const visit = (node) => {
    if (ts.isVariableDeclaration(node) && node.name.getText() === name && node.initializer && ts.isObjectLiteralExpression(node.initializer)) {
      const tag = objectProperty(node.initializer, 'tag')
      const component = objectProperty(node.initializer, 'component')
      if (tag && ts.isStringLiteral(tag) && component && ts.isIdentifier(component)) {
        found = { tag: tag.text, file: imports.get(component.text) }
      }
    }
    ts.forEachChild(node, visit)
  }
  visit(source)
  return found
}

/**
 * Web Components aus der Liste `ELEMENTS` (`registry.ts`): Tag und `.vue`-Datei.
 * @returns {{ tag: string, file: string | undefined, entry: string }[]}
 */
export function registeredElements(registryFile) {
  if (!registryFile || !existsSync(registryFile)) return []
  const source = parse(registryFile)
  const imports = importMap(source)
  const result = []
  const visit = (node) => {
    if (ts.isVariableDeclaration(node) && node.name.getText() === 'ELEMENTS' && node.initializer && ts.isArrayLiteralExpression(node.initializer)) {
      for (const element of node.initializer.elements) {
        if (!ts.isIdentifier(element)) continue
        const definitionFile = imports.get(element.text)
        const definition = definitionFile && existsSync(definitionFile) ? elementDefinition(definitionFile, element.text) : undefined
        result.push({ entry: element.text, tag: definition?.tag ?? '', file: definition?.file })
      }
    }
    ts.forEachChild(node, visit)
  }
  visit(source)
  return result
}

/** Alle statischen und dynamischen Modul-Spezifizierer einer Datei. */
export function importsOf(file) {
  const text = readFileSync(file, 'utf8')
  const script = file.endsWith('.vue') ? [...text.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map((m) => m[1]).join('\n') : text
  return ts.preProcessFile(script, true, true).importedFiles.map((entry) => entry.fileName)
}

export function relativeTo(root, file) {
  return posix(relative(root, file))
}
