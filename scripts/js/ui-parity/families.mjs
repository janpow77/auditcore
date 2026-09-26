/**
 * Paketfamilien der Oberflächen: je Familie ein Vue-Paket, ein natives
 * React-Paket, ein framework-freier Kern und das Verzeichnis der gemeinsamen
 * Paritätsfälle. Das ist Struktur, keine Komponentenliste: welche Komponenten
 * es gibt, leitet das Gate aus den Quellen ab (Exporte, `ELEMENTS`,
 * `defineCustomElement`).
 */

/**
 * @typedef {object} Family
 * @property {string} id Kurzname in Meldungen und Ausnahme-Kennungen.
 * @property {string} vue Verzeichnis des Vue-Pakets (relativ zur Wurzel).
 * @property {string} react Verzeichnis des React-Pakets.
 * @property {string} core Verzeichnis des Kernpakets.
 * @property {'group' | 'shared'} coreLayout `group`: Kern je Gruppe unter `<core>/<coreSrc>/<gruppe>/`; `shared`: ein Kernordner für alle Gruppen.
 * @property {string} coreSrc Quellordner des Kerns im Kernpaket.
 * @property {string | null} styles Ordner der Gruppenstile (`<gruppe>.css` + `index.css`) oder `null`.
 * @property {string} cases Ordner der Paritätsfälle (`cases-<gruppe>.ts`).
 * @property {string | null} registry Registrierung der Web Components (`ELEMENTS`) oder `null`.
 * @property {(relative: string) => string} groupOf Gruppe einer Vue-Datei (Pfad relativ zu `<vue>/src`).
 */

/** Erster Ordner unterhalb von `src` (`risk/RiskFlags.vue` → `risk`). */
function firstSegment(relative) {
  const parts = relative.split('/')
  return parts.length > 1 ? parts[0] : 'root'
}

/**
 * BPMN: `components/` ist nur ein Sammelordner (`components/collection/X.vue` →
 * `collection`); Dateien direkt darin oder in `src` gehören zum Editor.
 */
function bpmnGroup(relative) {
  const parts = relative.split('/')
  const rest = parts[0] === 'components' ? parts.slice(1) : parts
  return rest.length > 1 ? rest[0] : 'editor'
}

/** @type {readonly Family[]} */
export const FAMILIES = [
  {
    id: 'ui',
    vue: 'packages-js/ui',
    react: 'packages-js/ui-react',
    core: 'packages-js/ui-core',
    coreLayout: 'group',
    coreSrc: 'src',
    styles: 'packages-js/ui-core/styles',
    cases: 'packages-js/ui-core/test/parity',
    registry: 'packages-js/ui/src/registry.ts',
    groupOf: firstSegment,
  },
  {
    id: 'bpmn',
    vue: 'packages-js/bpmn-vue',
    react: 'packages-js/bpmn-react',
    core: 'packages-js/bpmn-flowaudit',
    coreLayout: 'shared',
    coreSrc: 'src/ui',
    styles: null,
    cases: 'packages-js/bpmn-flowaudit/test/parity',
    registry: null,
    groupOf: bpmnGroup,
  },
]

/** Paketnamen, die im React-Paket nie als Laufzeitabhängigkeit oder Import vorkommen dürfen. */
export const VUE_MODULES = [/^vue$/, /^@vue\//, /^vue-/, /\.vue$/]
