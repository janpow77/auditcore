import type { ElementDefinition } from '../elements/define'
import FaTable from './FaTable.vue'

/** `<flowaudit-table>`: Spalten und Zeilen als JS-Eigenschaften, Ereignisse `row-click`, `sort-change`. */
export const tableElement: ElementDefinition = { tag: 'flowaudit-table', component: FaTable }
