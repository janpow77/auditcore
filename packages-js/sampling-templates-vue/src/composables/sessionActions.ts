/**
 * Aktionen auf Schichttabellen und Listenblättern: Schichten hinzufügen und
 * entfernen, Einheiten anlegen, entfernen, einfügen und ihre Summen in das
 * Methodenblatt übernehmen. Jede Aktion schreibt einen neuen Arbeitsstand.
 */
import {
  MAX_LIST_ROWS,
  MAX_STRATA,
  strataColumnsOf,
  subsampleNeeds,
  applySubsamples,
  cellsOf,
  defaultInputs,
  inputFields,
  listRows,
  parsePastedRows,
  type CellMap,
  type CellValue,
  type SheetId,
  type Translate,
  type WorkspaceState,
} from '@auditcore/sampling-templates-core'
import { computed, ref, type ComputedRef, type Ref } from 'vue'
import { ownInputs, type SessionView } from './sessionView'

/** Schichten, die ein geschichtetes Blatt zu Beginn zeigt. */
const INITIAL_STRATA = 3

export interface SheetActions {
  strataCount: ComputedRef<number>
  addStratum: () => void
  removeStratum: () => void
  /** Trägt die letzte Schicht Eingaben? Dann fragt die Oberfläche vor dem Entfernen nach. */
  lastStratumFilled: ComputedRef<boolean>
  addUnit: () => void
  removeUnit: (index: number) => void
  pasteUnits: (text: string) => void
  transferSubsamples: () => void
}

export interface ActionContext {
  view: SessionView
  selectedUnit: Ref<number>
  /** Schreibt die Eingaben eines Blatts und kennzeichnet den Arbeitsstand als geändert. */
  write: (sheet: SheetId, inputs: WorkspaceState['sheets'][SheetId]) => void
  state: () => WorkspaceState
  t: Translate
  say: (text: string) => void
  notify: (tone: 'info' | 'warning', text: string) => void
}

function useStrata(context: ActionContext): Pick<SheetActions, 'strataCount' | 'addStratum' | 'removeStratum' | 'lastStratumFilled'> {
  const chosen = ref<Record<SheetId, number>>({})
  const { view } = context
  const sheetId = (): SheetId => view.currentSheet.value?.id ?? ''
  const strataCount = computed(() => (view.hasStrata.value ? Math.min(MAX_STRATA, Math.max(view.usedStrata.value, chosen.value[sheetId()] ?? INITIAL_STRATA)) : 0))
  const choose = (count: number): void => {
    chosen.value = { ...chosen.value, [sheetId()]: count }
  }
  /** Eingabezellen der letzten Schicht des angezeigten Blatts. */
  const lastCells = (): string[] => {
    const sheet = view.currentSheet.value
    const column = sheet ? strataColumnsOf(sheet.definition)[strataCount.value - 1] : undefined
    if (!sheet || !column) return []
    return inputFields(sheet.definition).filter((field) => field.columns).flatMap(cellsOf).filter((address) => address.replace(/\d+$/, '') === column)
  }
  return {
    strataCount,
    addStratum: () => choose(Math.min(MAX_STRATA, strataCount.value + 1)),
    lastStratumFilled: computed(() => {
      const sheet = view.currentSheet.value
      const inputs = sheet ? ownInputs(context.state(), sheet.id) : {}
      return lastCells().some((cell) => inputs[cell] !== null && inputs[cell] !== undefined && inputs[cell] !== '')
    }),
    /** Entfernt die letzte Schicht samt ihren Eingaben. */
    removeStratum() {
      const sheet = view.currentSheet.value
      const cells = lastCells()
      if (!sheet || strataCount.value <= 1 || cells.length === 0) return
      const inputs: Record<string, CellValue> = { ...ownInputs(context.state(), sheet.id) }
      for (const cell of cells) delete inputs[cell]
      choose(strataCount.value - 1)
      context.write(sheet.id, inputs)
    },
  }
}

function useUnits(context: ActionContext): Pick<SheetActions, 'addUnit' | 'removeUnit' | 'pasteUnits' | 'transferSubsamples'> {
  const { view, selectedUnit, t } = context
  const rows = (): readonly CellMap[] => (view.currentSheet.value ? listRows(context.state(), view.currentSheet.value.id) : [])
  const append = (added: readonly CellMap[]): void => {
    const sheet = view.currentSheet.value
    if (!sheet || added.length === 0) return
    const next = [...rows(), ...added].slice(0, MAX_LIST_ROWS)
    context.write(sheet.id, next)
    selectedUnit.value = next.length - 1
  }
  return {
    addUnit: () => append(view.currentSheet.value ? [defaultInputs(view.currentSheet.value.definition)] : []),
    removeUnit(index) {
      const sheet = view.currentSheet.value
      if (!sheet) return
      context.write(sheet.id, rows().filter((_, position) => position !== index))
      selectedUnit.value = Math.max(0, Math.min(selectedUnit.value, rows().length - 1))
    },
    pasteUnits(text) {
      const sheet = view.currentSheet.value
      if (!sheet) return
      const pasted = parsePastedRows(text, sheet.definition, MAX_LIST_ROWS - rows().length)
      append(pasted.rows)
      context.say(t('listPasted', { count: pasted.rows.length }))
      if (pasted.rejected) context.notify('warning', t('listPasteRejected', { count: pasted.rejected }))
      if (pasted.dropped) context.notify('warning', t('listPasteDropped', { count: pasted.dropped, max: MAX_LIST_ROWS }))
    },
    /** Summen der Einheiten in die gekennzeichneten Felder des gewählten Methodenblatts schreiben. */
    transferSubsamples() {
      const sheet = view.currentSheet.value
      const method = view.activeSheet.value
      const totals = method ? sheet?.totals?.(rows(), view.context.value, subsampleNeeds(method.definition)) : undefined
      if (!method || !totals) return
      const result = applySubsamples(method, ownInputs(context.state(), method.id), totals)
      if (result.applied.length === 0) return context.notify('info', t('listTransferNone'))
      context.write(method.id, result.inputs)
      context.say(t('listTransferred', { number: method.definition.number, fields: result.cells.join(', ') }))
      if (totals.unassigned) context.notify('warning', t('listUnassigned', { count: totals.unassigned }))
    },
  }
}

export function useSheetActions(context: ActionContext): SheetActions {
  return { ...useStrata(context), ...useUnits(context) }
}
