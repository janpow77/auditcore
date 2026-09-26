/**
 * Prüfungen des Vollständigkeits-Gates (Vue ↔ React, gemeinsamer Kern,
 * gemeinsame Paritätsfälle). Jede Lücke wird eine Verletzung mit stabiler
 * Kennung `<prüfung>:<familie>:<gegenstand>`, auf die sich eine befristete
 * Ausnahme beziehen kann.
 */
import { existsSync, readdirSync, readFileSync } from 'node:fs'
import { join, relative, sep } from 'node:path'
import { importsOf, reactComponents, readJson, registeredElements, relativeTo, resolveModule, vueComponents } from './discover.mjs'
import { VUE_MODULES } from './families.mjs'

const SKIPPED = new Set(['node_modules', 'dist', 'coverage', 'e2e-results'])
const CONTROLLER = /\bcreateStore\s*[(<]|export\s+function\s+create\w*Controller\b/

function walk(dir, accept) {
  if (!existsSync(dir)) return []
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    if (SKIPPED.has(entry.name)) return []
    const path = join(dir, entry.name)
    if (entry.isDirectory()) return walk(path, accept)
    return accept(entry.name) ? [path] : []
  })
}

const pascal = (kebab) => kebab.split('-').map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join('')

/** Erwarteter Name der React-Komponente zu einem Web-Component-Tag (`flowaudit-risk-flags` → `FlowauditRiskFlags`). */
export const reactNameForTag = (tag) => `Flowaudit${pascal(tag.replace(/^flowaudit-/, ''))}`

const within = (dir, file) => file === dir || file.startsWith(dir + sep)

/**
 * Vue-Komponenten einer Familie mit Gruppe, Tag und den zulässigen Namen der
 * React-Fassung (Name selbst, ohne `Fa`-Präfix, `Flowaudit<Tag>`).
 */
export function vueSide(root, family) {
  const vueDir = join(root, family.vue)
  const components = vueComponents(vueDir)
  const elements = registeredElements(family.registry ? join(root, family.registry) : null)
  const byFile = new Map(elements.filter((element) => element.file).map((element) => [element.file, element.tag]))
  const list = components.map((component) => ({ ...component, tag: byFile.get(component.file) ?? null }))
  for (const element of elements) {
    if (!list.some((component) => component.file === element.file)) {
      list.push({ name: element.entry, file: element.file ?? join(vueDir, 'src', family.registry ?? ''), customElement: false, tag: element.tag })
    }
  }
  return list.map((component) => {
    const expected = component.tag ? reactNameForTag(component.tag) : component.name.replace(/^Fa(?=[A-Z])/, '')
    const accepted = new Set([component.name, component.name.replace(/^Fa(?=[A-Z])/, ''), expected])
    const group = family.groupOf(relativeTo(join(vueDir, 'src'), component.file))
    return { ...component, group, expected, accepted }
  })
}

function violation(check, family, subject, message) {
  return { id: `${check}:${family.id}:${subject}`, check, family: family.id, subject, message }
}

/** (a) jede Vue-Komponente hat eine native React-Fassung; (d) umgekehrt. */
export function checkCounterparts(root, family, vue, react) {
  const reactNames = new Set(react.map((component) => component.name))
  const out = []
  for (const component of vue) {
    if ([...component.accepted].some((name) => reactNames.has(name))) continue
    const where = relativeTo(root, component.file)
    out.push(violation('react-missing', family, component.name, `Vue-Komponente ${component.name} (${where}) hat keine native React-Fassung in ${family.react} (erwartet: ${component.expected}).`))
  }
  for (const component of react) {
    if (vue.some((entry) => entry.accepted.has(component.name))) continue
    const where = relativeTo(root, component.file)
    out.push(violation('vue-missing', family, component.name, `React-Komponente ${component.name} (${where}) hat kein öffentliches Vue-Gegenstück in ${family.vue}.`))
  }
  return out
}

const hasController = (files) => files.some((file) => CONTROLLER.test(readFileSync(file, 'utf8')))
const tsFiles = (dir) => walk(dir, (name) => name.endsWith('.ts') && !name.endsWith('.d.ts'))

/** (b) Kernmodul mit Controller (und Stil) je Gruppe. */
export function checkCore(root, family, groups) {
  const coreSrc = join(root, family.core, family.coreSrc)
  if (family.coreLayout === 'shared') {
    return hasController(tsFiles(coreSrc)) ? [] : [violation('core-controller', family, '*', `${relativeTo(root, coreSrc)} enthält keinen Controller (createStore).`)]
  }
  const out = []
  const coreIndex = join(coreSrc, 'index.ts')
  const coreExports = existsSync(coreIndex) ? importsOf(coreIndex) : []
  for (const group of groups) {
    const dir = join(coreSrc, group)
    const sibling = join(root, 'packages-js', `${group}-core`, 'src')
    if (!existsSync(join(dir, 'index.ts'))) {
      out.push(violation('core-missing', family, group, `Kernmodul ${relativeTo(root, dir)}/index.ts fehlt.`))
    } else if (!coreExports.includes(`./${group}`)) {
      out.push(violation('core-export', family, group, `${relativeTo(root, coreIndex)} exportiert ./${group} nicht.`))
    }
    if (!hasController([...tsFiles(dir), ...tsFiles(sibling)])) {
      out.push(violation('core-controller', family, group, `Kein Controller (createStore / create…Controller) in ${relativeTo(root, dir)} oder packages-js/${group}-core.`))
    }
    out.push(...checkStyle(root, family, group))
  }
  return out
}

function checkStyle(root, family, group) {
  if (!family.styles) return []
  const dir = join(root, family.styles)
  const index = join(dir, 'index.css')
  const imported = existsSync(index) && readFileSync(index, 'utf8').includes(`'./${group}.css'`)
  if (existsSync(join(dir, `${group}.css`)) && imported) return []
  return [violation('style-missing', family, group, `Stil ${family.styles}/${group}.css fehlt oder ist nicht in index.css eingebunden.`)]
}

/** Testdateien mit ihren aufgelösten Importen (relativ → absoluter Pfad, sonst Paketname). */
export function testImports(root) {
  const specs = walk(join(root, 'packages-js'), (name) => /\.spec\.tsx?$/.test(name))
  return specs.map((file) => ({
    file,
    imports: importsOf(file).map((specifier) => resolveModule(file, specifier) ?? specifier),
  }))
}

function sidePredicate(root, dir) {
  const absolute = join(root, dir)
  const name = readJson(join(absolute, 'package.json')).name
  const src = join(absolute, 'src')
  return (entry) => entry === name || entry.startsWith(`${name}/`) || within(src, entry)
}

function caseCandidates(root, family, group, tags) {
  const dir = join(root, family.cases)
  const names = new Set([`cases-${group}.ts`, ...tags.map((tag) => `cases-${tag.replace(/^flowaudit-/, '')}.ts`)])
  const local = walk(dir, (name) => names.has(name) || (name.startsWith(`cases-${group}-`) && name.endsWith('.ts')))
  const sibling = walk(join(root, 'packages-js', `${group}-core`, 'test', 'parity'), (name) => /^cases.*\.ts$/.test(name))
  return [...local, ...sibling]
}

/** (c) Paritätsfälle je Gruppe, eingebunden in einen Vue- und einen React-Paritätstest. */
export function checkCases(root, family, vue, tests) {
  const isVue = sidePredicate(root, family.vue)
  const isReact = sidePredicate(root, family.react)
  const groups = [...new Set(vue.map((component) => component.group))].sort()
  const out = []
  for (const group of groups) {
    const tags = vue.filter((component) => component.group === group && component.tag).map((component) => component.tag)
    const candidates = caseCandidates(root, family, group, tags)
    const users = (file) => tests.filter((test) => test.imports.includes(file))
    const covered = candidates.some((file) => {
      const importing = users(file)
      return importing.some((test) => test.imports.some(isVue)) && importing.some((test) => test.imports.some(isReact))
    })
    if (covered) continue
    const detail = candidates.length === 0
      ? `keine Datei ${family.cases}/cases-${group}.ts`
      : `${candidates.map((file) => relativeTo(root, file)).join(', ')} nicht zugleich von einem Vue- und einem React-Paritätstest importiert`
    out.push(violation('parity-cases', family, group, `Gruppe ${group}: ${detail}.`))
  }
  return out
}

const isVueModule = (specifier, vueName) =>
  specifier === vueName || specifier.startsWith(`${vueName}/`) || VUE_MODULES.some((pattern) => pattern.test(specifier))

/** (e) keine Vue-Imports und keine Vue-Laufzeitabhängigkeit im React-Paket. */
export function checkNoVue(root, family) {
  const reactDir = join(root, family.react)
  const vueDir = join(root, family.vue)
  const vueName = readJson(join(vueDir, 'package.json')).name
  const out = []
  for (const file of walk(join(reactDir, 'src'), (name) => /\.(tsx?|mts|js|mjs)$/.test(name))) {
    const bad = importsOf(file).filter((specifier) => isVueModule(specifier, vueName) || within(vueDir, resolveModule(file, specifier) ?? ''))
    for (const specifier of bad) {
      out.push(violation('vue-import', family, `${relative(reactDir, file).split(sep).join('/')}:${specifier}`, `${relativeTo(root, file)} importiert ${specifier} (React-Paket ohne Vue).`))
    }
  }
  const manifest = readJson(join(reactDir, 'package.json'))
  for (const field of ['dependencies', 'peerDependencies', 'optionalDependencies']) {
    for (const dependency of Object.keys(manifest[field] ?? {})) {
      if (isVueModule(dependency, vueName)) {
        out.push(violation('vue-dependency', family, dependency, `${family.react}/package.json: ${field} enthält ${dependency}.`))
      }
    }
  }
  return out
}

/** Alle Prüfungen einer Familie. */
export function checkFamily(root, family, tests) {
  const vue = vueSide(root, family)
  const react = reactComponents(join(root, family.react))
  const groups = [...new Set(vue.map((component) => component.group))].sort()
  return {
    summary: { family: family.id, vueComponents: vue.length, reactComponents: react.length, groups },
    violations: [
      ...checkCounterparts(root, family, vue, react),
      ...checkCore(root, family, groups),
      ...checkCases(root, family, vue, tests),
      ...checkNoVue(root, family),
    ],
  }
}

