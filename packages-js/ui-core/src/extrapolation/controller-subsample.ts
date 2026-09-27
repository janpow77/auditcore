// Bearbeitung der Teilstichprobe einer Einheit (Leitfaden 7.6, 6.5.3) im
// Zustandsautomaten der Hochrechnung: anlegen, öffnen, Teilschichten und
// Teileinheiten pflegen, Teilstichprobe einer Teileinheit (dreistufig).
import type { Store } from '../store'
import type { ExtrapolationData } from './controller'
import type { UnitRow } from './model'
import { emptySubItem, emptySubsample, emptySubStratum, type SubItemRow, type SubsampleRows, type SubStratumRow } from './model-subsample'

function patchUnit(store: Store<ExtrapolationData>, index: number, patch: Partial<UnitRow>): void {
  store.set((state) => ({ form: { ...state.form, units: state.form.units.map((row, position) => (position === index ? { ...row, ...patch } : row)) } }))
}

function replaceAt<T>(rows: readonly T[], index: number, change: Partial<T>): T[] {
  return rows.map((row, position) => (position === index ? { ...row, ...change } : row))
}

/** Gerade bearbeitete Teilstichprobe: die der Einheit oder die einer ihrer Teileinheiten. */
export function openSubsample(state: ExtrapolationData): SubsampleRows | null {
  const unit = state.subsampleUnit === null ? null : state.form.units[state.subsampleUnit]?.subsample ?? null
  if (!unit || state.subsampleItem === null) return unit
  return unit.items[state.subsampleItem]?.subsample ?? null
}

export function createSubsampleActions(store: Store<ExtrapolationData>, key: (prefix: string) => string) {
  const patch = (change: (rows: SubsampleRows) => Partial<SubsampleRows>): void => {
    const state = store.get()
    const index = state.subsampleUnit
    const unit = index === null ? null : state.form.units[index]?.subsample
    if (index === null || !unit) return
    if (state.subsampleItem === null) {
      patchUnit(store, index, { subsample: { ...unit, ...change(unit) } })
      return
    }
    const nested = unit.items[state.subsampleItem]?.subsample
    if (!nested) return
    patchUnit(store, index, { subsample: { ...unit, items: replaceAt(unit.items, state.subsampleItem, { subsample: { ...nested, ...change(nested) } }) } })
  }
  const fresh = (): SubsampleRows => ({ ...emptySubsample(), items: [emptySubItem(key('i'))] })
  return {
    /** Teilstichprobe anlegen und öffnen bzw. entfernen (der Fehler kommt dann wieder aus dem Feld). */
    toggleSubsample(index: number): void {
      const unit = store.get().form.units[index]
      if (!unit) return
      if (unit.subsample) {
        patchUnit(store, index, { subsample: null })
        store.set((state) => (state.subsampleUnit === index ? { subsampleUnit: null, subsampleItem: null } : {}))
        return
      }
      patchUnit(store, index, { subsample: fresh(), random: '' })
      store.set({ subsampleUnit: index, subsampleItem: null })
    },
    editSubsample: (index: number | null) => store.set({ subsampleUnit: index, subsampleItem: null }),
    /** Teilstichprobe einer Teileinheit anlegen bzw. entfernen (nur in der Teilstichprobe der Einheit). */
    toggleNestedSubsample(item: number): void {
      if (store.get().subsampleItem !== null) return
      const current = store.get()
      const unit = current.subsampleUnit === null ? null : current.form.units[current.subsampleUnit]?.subsample
      const row = unit?.items[item]
      if (!row) return
      patch((rows) => ({ items: replaceAt(rows.items, item, row.subsample ? { subsample: null } : { subsample: fresh(), random: '' }) }))
      if (!row.subsample) store.set({ subsampleItem: item })
    },
    editNestedSubsample: (item: number | null) => store.set({ subsampleItem: item }),
    updateSubsample: (change: Partial<Pick<SubsampleRows, 'estimator' | 'populationSize'>>) => patch(() => change),
    addSubStratum: () => patch((rows) => ({ strata: [...rows.strata, emptySubStratum(key('t'))] })),
    updateSubStratum: (index: number, change: Partial<SubStratumRow>) => patch((rows) => ({ strata: replaceAt(rows.strata, index, change) })),
    removeSubStratum: (index: number) => patch((rows) => ({ strata: rows.strata.filter((_, position) => position !== index) })),
    addSubItem: () => patch((rows) => ({ items: [...rows.items, emptySubItem(key('i'), rows.strata[0]?.name ?? '')] })),
    updateSubItem: (item: number, change: Partial<SubItemRow>) => patch((rows) => ({ items: replaceAt(rows.items, item, change) })),
    removeSubItem: (item: number) => patch((rows) => ({ items: rows.items.filter((_, position) => position !== item) })),
  }
}
