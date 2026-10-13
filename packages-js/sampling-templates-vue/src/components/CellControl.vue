<script setup lang="ts">
import { INPUT_FAILURE_HINTS, choiceValue, parseFieldInput, type CellAddress, type CellValue, type CellView, type RowView, type Translate } from '@auditcore/sampling-templates-core'
import { FaBadge } from '@auditcore/ui'
import { computed, nextTick, ref, watch } from 'vue'

/**
 * Bedienelement einer Zelle: Eingabe, Auswahl, berechneter Wert oder Prüfhinweis.
 * `row` beschreibt das Feld, `cell` die Zelle (bei Schichtzeilen eine je Schicht).
 */
const props = defineProps<{ row: RowView; cell: CellView; id: string; t: Translate; label?: string; describedBy?: string }>()
const emit = defineEmits<{ update: [cell: CellAddress, value: CellValue] }>()

const text = ref(props.cell.inputText)
const error = ref('')
/** Fehler erst zeigen, wenn das Feld einmal verlassen wurde – nicht bei jedem Tastendruck. */
const touched = ref(false)
const focused = ref(false)
const shownError = computed(() => (touched.value ? error.value : ''))
const described = computed(() => [props.describedBy ?? '', shownError.value ? `${props.id}-error` : ''].filter(Boolean).join(' ') || undefined)

watch(
  () => props.cell.inputText,
  (next) => {
    if (!focused.value && !error.value) text.value = next
  },
)

function onInput(event: Event): void {
  text.value = (event.target as HTMLInputElement).value
  const result = parseFieldInput(props.row, text.value)
  error.value = result.ok ? '' : props.t('errorInput', { reason: INPUT_FAILURE_HINTS[result.reason] })
  emit('update', props.cell.cell, result.ok ? result.value : null)
}

function onBlur(): void {
  focused.value = false
  touched.value = true
  if (!error.value) void nextTick(() => (text.value = props.cell.inputText))
}

function onSelect(event: Event): void {
  emit('update', props.cell.cell, choiceValue(props.row.options, (event.target as HTMLSelectElement).value))
}
</script>

<template>
  <select v-if="row.control === 'select'" :id="id" class="fa-st__input" :value="cell.value === null ? '' : String(cell.value)" :aria-label="label" :aria-describedby="described" @change="onSelect">
    <option value="">{{ t('choose') }}</option>
    <option v-for="option in row.options" :key="String(option.value)" :value="String(option.value)">{{ option.label }}</option>
  </select>
  <input
    v-else-if="row.control === 'text' || row.control === 'number'"
    :id="id"
    class="fa-st__input"
    :class="{ 'fa-st__input--number': row.control === 'number' }"
    type="text"
    :inputmode="row.control === 'number' ? 'decimal' : undefined"
    autocomplete="off"
    spellcheck="false"
    :placeholder="row.type === 'percent' ? t('percentPlaceholder') : undefined"
    :value="text"
    :aria-label="label"
    :aria-invalid="shownError ? 'true' : undefined"
    :aria-describedby="described"
    @input="onInput"
    @focus="focused = true"
    @blur="onBlur"
  />
  <div v-else-if="row.control === 'check'" class="fa-st__check">
    <FaBadge class="fa-st__pill" :tone="cell.tone" :label="cell.display" />
  </div>
  <p v-else class="fa-st__value" :class="{ 'fa-st__value--missing': cell.missing }">{{ cell.display }}</p>
  <p v-if="cell.missingNote" class="fa-st__note" data-missing-note>{{ cell.missingNote }}</p>
  <p v-if="cell.zeroNote" class="fa-st__note fa-st__note--warning" data-zero-note><strong>{{ t('webHint') }}:</strong> {{ cell.zeroNote }}</p>
  <p v-if="cell.caveatNote" class="fa-st__note fa-st__note--warning" data-caveat-note><strong>{{ t('webHint') }}:</strong> {{ cell.caveatNote }}</p>
  <p v-if="shownError" :id="`${id}-error`" class="fa-st__error" role="alert">{{ shownError }}</p>
</template>
