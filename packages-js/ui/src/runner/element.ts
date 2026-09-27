import type { ElementDefinition } from '../elements/define'
import RunnerConsole from './RunnerConsole.vue'

/** `<flowaudit-runner-console>`: Eigenschaften `port`, `locale`; Ereignisse `item-select`, `error`. */
export const runnerConsoleElement: ElementDefinition = { tag: 'flowaudit-runner-console', component: RunnerConsole }
