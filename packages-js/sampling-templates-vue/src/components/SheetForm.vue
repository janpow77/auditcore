<script setup lang="ts">
import type { CellAddress, CellValue, RowView, SectionView, Translate } from '@auditcore/sampling-templates-core'
import { useId } from '@auditcore/ui'
import { computed } from 'vue'
import SheetField from './SheetField.vue'
import StrataTable from './StrataTable.vue'

/** Rechenblatt: Abschnitte und Zeilen in der Reihenfolge der Vorlage; Schichtzeilen als Schichttabelle. */
const props = withDefaults(defineProps<{ sections: readonly SectionView[]; t: Translate; strata?: number }>(), { strata: 0 })
defineEmits<{ update: [cell: CellAddress, value: CellValue]; addStratum: []; removeStratum: [] }>()

const id = useId('fa-st-form')

type Block = { key: string; rows: RowView[]; strata: boolean }

/** Erste Schichtzeile des Blatts: Nur ihre Tabelle trägt die Schaltflächen zum Hinzufügen und Entfernen. */
const firstStrataRow = computed(() => props.sections.flatMap((section) => [...section.rows]).find((row) => row.strata !== null)?.cell)

/** Aufeinanderfolgende Schichtzeilen bilden eine Tabelle, alle anderen Zeilen stehen einzeln. */
function blocksOf(rows: readonly RowView[]): Block[] {
  const blocks: Block[] = []
  for (const row of rows) {
    const last = blocks.at(-1)
    if (row.strata && last?.strata) last.rows.push(row)
    else blocks.push({ key: row.cell, rows: [row], strata: row.strata !== null })
  }
  return blocks
}
</script>

<template>
  <div class="fa-st__card fa-st__form">
    <section v-for="section in sections" :key="section.id" class="fa-st__section" :aria-labelledby="`${id}-${section.id}`">
      <div class="fa-st__section-head">
        <h3 :id="`${id}-${section.id}`" class="fa-st__section-title">{{ section.id }} · {{ section.title }}</h3>
        <span v-if="section.reference" class="fa-st__muted">{{ section.reference }}</span>
      </div>
      <template v-for="block in blocksOf(section.rows)" :key="block.key">
        <StrataTable v-if="block.strata" :rows="block.rows" :count="strata" :controls="block.key === firstStrataRow" :t="t" @update="(cell, value) => $emit('update', cell, value)" @add="$emit('addStratum')" @remove="$emit('removeStratum')" />
        <SheetField v-else :row="block.rows[0]!" :t="t" @update="(cell, value) => $emit('update', cell, value)" />
      </template>
    </section>
  </div>
</template>
