<script setup lang="ts">
import type { CellAddress, CellValue, ReportBlock, ReportCell, ReportPage, ReportRow, Translate } from '@auditcore/sampling-templates-core'
import { FaButton, useId } from '@auditcore/ui'
import { computed } from 'vue'
import CellControl from './CellControl.vue'
import SheetField from './SheetField.vue'

/**
 * Bericht (Blatt 20, Druckfassung für die Kommission): die Seite in A4-Proportion
 * mit bearbeitbaren Freitexten und Fehlerfällen, daneben die Steuerfelder, die
 * nicht gedruckt werden. `report` ist das Ergebnis von `buildReport`. Gedruckt
 * wird über das Ereignis `print`; die einbindende Komponente ruft `window.print()`.
 */
const props = defineProps<{ report: ReportPage; t: Translate }>()
const emit = defineEmits<{ update: [cell: CellAddress, value: CellValue]; print: [] }>()

const id = useId('fa-st-report')
const printedHints = computed(() => props.report.hints.filter((hint) => hint.printed))
const screenHints = computed(() => props.report.hints.filter((hint) => !hint.printed))

type TableBlock = Extract<ReportBlock, { kind: 'table' }>

/** Tabellenkörper und, wenn vorhanden, die Summenzeile als Tabellenfuß. */
function groupsOf(block: TableBlock): { tag: 'tbody' | 'tfoot'; rows: readonly ReportRow[] }[] {
  return [{ tag: 'tbody', rows: block.rows }, ...(block.foot ? [{ tag: 'tfoot' as const, rows: [block.foot] }] : [])]
}

const cellClass = (cell: ReportCell): Record<string, boolean> => ({ 'fa-st__report-num': cell.numeric, 'fa-st__report-missing': cell.missing })

/** Freitext: leer heißt keine Eingabe; sonst der Text, wie er eingegeben ist. */
function onText(cell: CellAddress, event: Event): void {
  const text = (event.target as HTMLTextAreaElement).value
  emit('update', cell, text.trim() === '' ? null : text)
}
</script>

<template>
  <section class="fa-st__report" :aria-labelledby="`${id}-title`">
    <div class="fa-st__report-tools">
      <FaButton variant="primary" :label="report.labels.print" data-action="print" @click="emit('print')" />
    </div>
    <div class="fa-st__report-layout">
      <article class="fa-st__report-page" data-report-page>
        <header class="fa-st__report-head">
          <p class="fa-st__report-eu">
            <span v-for="line in report.cofinanced" :key="line">{{ line }}</span>
          </p>
          <h3 :id="`${id}-title`" class="fa-st__report-title">{{ report.title }}</h3>
          <div class="fa-st__report-sub">
            <p data-report-subtitle>{{ report.subtitle }}</p>
            <p v-if="report.asOf" data-report-as-of>{{ report.asOf }}</p>
          </div>
        </header>

        <section v-for="section in report.sections" :key="section.id" class="fa-st__report-section" :aria-labelledby="`${id}-s${section.id}`">
          <h4 :id="`${id}-s${section.id}`" class="fa-st__report-heading">{{ section.title }}</h4>
          <template v-for="block in section.blocks" :key="block.key">
            <div v-if="block.kind === 'text'" class="fa-st__report-free" :data-cell="block.field.cell">
              <textarea
                class="fa-st__input fa-st__report-textarea fa-st__report-screen"
                rows="3"
                spellcheck="true"
                :value="block.text"
                :placeholder="block.placeholder"
                :aria-label="section.title"
                @input="onText(block.field.cell, $event)"
              ></textarea>
              <p class="fa-st__report-print" :class="{ 'fa-st__report-placeholder': !block.text }">{{ block.text || block.placeholder }}</p>
            </div>
            <p v-else-if="block.kind === 'statement'" class="fa-st__report-statement" data-report-statement>{{ block.text }}</p>
            <table v-else class="fa-st__report-table" :class="{ 'fa-st__report-table--figures': block.columns.length === 0 }">
              <caption class="fa-sr-only">{{ section.title }}</caption>
              <thead v-if="block.columns.length">
                <tr>
                  <template v-for="(column, index) in block.columns" :key="index">
                    <th v-if="column.label" scope="col" :class="{ 'fa-st__report-num': column.numeric }">{{ column.label }}</th>
                    <td v-else></td>
                  </template>
                </tr>
              </thead>
              <component :is="group.tag" v-for="group in groupsOf(block)" :key="group.tag">
                <tr v-for="row in group.rows" :key="row.key">
                  <th v-if="row.header" scope="row">{{ row.header }}</th>
                  <td v-for="(cell, index) in row.cells" :key="index" :class="cellClass(cell)" :colspan="cell.span > 1 ? cell.span : undefined" :data-cell="cell.cell ?? undefined">
                    <template v-if="cell.input && cell.cell">
                      <span class="fa-st__report-screen">
                        <CellControl :id="`${id}-${cell.cell}`" :row="cell.input" :cell="cell.input" :t="t" :label="cell.input.label" @update="(address, value) => emit('update', address, value)" />
                      </span>
                      <span class="fa-st__report-print">{{ cell.text }}</span>
                    </template>
                    <template v-else>{{ cell.text }}</template>
                  </td>
                </tr>
              </component>
            </table>
          </template>
        </section>

        <section class="fa-st__report-notes" :aria-labelledby="`${id}-notes`">
          <h4 :id="`${id}-notes`" class="fa-st__report-heading fa-st__report-heading--notes">{{ report.labels.hints }}</h4>
          <ul v-if="printedHints.length" class="fa-st__report-hints" data-report-hints>
            <li v-for="hint in printedHints" :key="hint.id">{{ hint.text }}</li>
          </ul>
          <p v-for="note in report.notes" :key="note">{{ note }}</p>
        </section>
        <footer class="fa-st__report-footer">{{ report.footer }}</footer>
      </article>

      <aside class="fa-st__card fa-st__report-controls" :aria-labelledby="`${id}-controls`" data-report-controls>
        <h3 :id="`${id}-controls`" class="fa-st__section-title">{{ report.controls.title }}</h3>
        <SheetField v-for="field in report.controls.fields" :key="field.cell" :row="field" :t="t" @update="(address, value) => emit('update', address, value)" />
        <p class="fa-st__muted">{{ report.controls.note }}</p>
        <ul v-if="screenHints.length" class="fa-st__report-hints fa-st__muted" data-report-screen-hints>
          <li v-for="hint in screenHints" :key="hint.id">
            <strong>{{ t('webHint') }}:</strong> {{ hint.text }}
          </li>
        </ul>
      </aside>
    </div>
  </section>
</template>
