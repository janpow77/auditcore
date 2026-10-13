/**
 * Quell-Aliasse für Entwicklung, Tests und Demo: Die Geschwisterpakete werden
 * aus dem Quelltext benutzt, eine Baureihenfolge ist nicht nötig. Speziellere
 * Einträge stehen zuerst.
 */
import { fileURLToPath } from 'node:url'

const path = (relative: string): string => fileURLToPath(new URL(relative, import.meta.url))

export const sourceAliases = [
  { find: /^@auditcore\/sampling-templates-core\/style\.css$/, replacement: path('../sampling-templates-core/styles/sampling-templates.css') },
  { find: /^@auditcore\/sampling-templates-core\/xlsx$/, replacement: path('../sampling-templates-core/src/xlsx/index.ts') },
  { find: /^@auditcore\/sampling-templates-core$/, replacement: path('../sampling-templates-core/src/index.ts') },
  { find: /^@auditcore\/ui-core\/style\.css$/, replacement: path('../ui-core/styles/index.css') },
  { find: /^@auditcore\/ui-core\/styles\/(.*)$/, replacement: path('../ui-core/styles/$1') },
  { find: /^@auditcore\/ui-core$/, replacement: path('../ui-core/src/index.ts') },
  { find: /^@auditcore\/ui$/, replacement: path('../ui/src/index.ts') },
  { find: /^@auditcore\/kanban-core$/, replacement: path('../kanban-core/src/index.ts') },
  { find: /^@auditcore\/common\/browser$/, replacement: path('../common/src/browser.ts') },
  { find: /^@auditcore\/common$/, replacement: path('../common/src/index.ts') },
]

/** Im Bibliotheksbau bleibt alles außer dem Stil des Kerns extern. */
export const isExternal = (id: string): boolean => /^(vue|fflate)($|\/)/.test(id) || (/^@auditcore\//.test(id) && !id.endsWith('.css'))

/** Der Stil des Kerns wird in `sampling-templates-vue.css` gebündelt: ein Import für die Anwendung. */
export const styleAlias = [sourceAliases[0]!]
