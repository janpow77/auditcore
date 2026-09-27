import type { ElementDefinition } from '../elements/define'
import RunnerConsole from './RunnerConsole.vue'

/**
 * `<flowaudit-runner-console>`: Attribut `api` (Basis-URL der JSON-API von
 * `auditcore-runner ui`, z. B. `/api`), `ansicht`, `locale`; Eigenschaft `port`.
 * Ereignisse `applied` (Version), `error` (Meldung).
 */
export const runnerConsoleElement: ElementDefinition = { tag: 'flowaudit-runner-console', component: RunnerConsole }
