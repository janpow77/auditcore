// Bearbeitung der Teilstichprobe einer Einheit (Leitfaden 7.6, 6.5.3) im
// Zustandsautomaten der Hochrechnung: anlegen, öffnen, Teileinheiten pflegen.
import type { Store } from '../store'
import type { ExtrapolationData } from './controller'
import { emptySubItem, emptySubsample, type SubItemRow, type SubsampleRows } from './model-design'
import type { UnitRow } from './model'

function patchUnit(store: Store<ExtrapolationData>, index: number, patch: Partial<UnitRow>): void {
  store.set((state) => ({ form: { ...state.form, units: state.form.units.map((row, position) => (position === index ? { ...row, ...patch } : row)) } }))
}

export function createSubsampleActions(store: Store<ExtrapolationData>, key: (prefix: string) => string) {
  const open = (): { index: number; rows: SubsampleRows } | null => {
    const index = store.get().subsampleUnit
    const rows = index === null ? null : store.get().form.units[index]?.subsample
    return index === null || !rows ? null : { index, rows }
  }
  const patch = (change: (rows: SubsampleRows) => Partial<SubsampleRows>): void => {
    const current = open()
    if (current) patchUnit(store, current.index, { subsample: { ...current.rows, ...change(current.rows) } })
  }
  return {
    /** Teilstichprobe anlegen und öffnen bzw. entfernen (der Fehler kommt dann wieder aus dem Feld). */
    toggleSubsample(index: number): void {
      const unit = store.get().form.units[index]
      if (!unit) return
      if (unit.subsample) {
        patchUnit(store, index, { subsample: null })
        store.set((state) => ({ subsampleUnit: state.subsampleUnit === index ? null : state.subsampleUnit }))
        return
      }
      patchUnit(store, index, { subsample: { ...emptySubsample(), items: [emptySubItem(key('i'))] }, random: '' })
      store.set({ subsampleUnit: index })
    },
    editSubsample: (index: number | null) => store.set({ subsampleUnit: index }),
    updateSubsample: (change: Partial<Omit<SubsampleRows, 'items'>>) => patch(() => change),
    addSubItem: () => patch((rows) => ({ items: [...rows.items, emptySubItem(key('i'))] })),
    updateSubItem: (item: number, change: Partial<SubItemRow>) => patch((rows) => ({ items: rows.items.map((row, position) => (position === item ? { ...row, ...change } : row)) })),
    removeSubItem: (item: number) => patch((rows) => ({ items: rows.items.filter((_, position) => position !== item) })),
  }
}
