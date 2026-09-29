import type { ElementDefinition } from '../elements/define'
import AccountWorkspace from './AccountWorkspace.vue'

/** `<flowaudit-account-workspace>`: Eigenschaften `port`, `locale`; Ereignisse `item-select`, `error`. */
export const accountWorkspaceElement: ElementDefinition = { tag: 'flowaudit-account-workspace', component: AccountWorkspace }
