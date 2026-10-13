<script setup lang="ts">
import type { ListView, Translate } from '@auditcore/sampling-templates-core'
import { FaButton, FaDialog, useId, type Locale } from '@auditcore/ui'
import { ref } from 'vue'

/**
 * Liste der Stichprobeneinheiten (Blatt 17): Übersicht, Hinzufügen, Entfernen,
 * Einfügen aus Zwischenablage oder CSV und Übernahme der Summen ins Methodenblatt.
 * Die gewählte Einheit bearbeitet das Formular darunter.
 */
defineProps<{ view: ListView; selected: number; methodNumber: string; pasteColumns: string; t: Translate; locale?: Locale }>()
const emit = defineEmits<{ select: [index: number]; add: []; remove: [index: number]; paste: [text: string]; transfer: [] }>()

const id = useId('fa-st-units')
const pasting = ref(false)
const pasted = ref('')

function applyPaste(): void {
  emit('paste', pasted.value)
  pasted.value = ''
  pasting.value = false
}
</script>

<template>
  <section class="fa-st__card fa-st__units" :aria-labelledby="id" data-units>
    <div class="fa-st__section-head">
      <h3 :id="id" class="fa-st__section-title">{{ t('listUnits') }}</h3>
      <div class="fa-st__units-actions">
        <FaButton size="sm" icon="plus" :label="t('listAdd')" data-action="unit-add" @click="$emit('add')" />
        <FaButton size="sm" :label="t('listPaste')" data-action="unit-paste" @click="pasting = true" />
      </div>
    </div>
    <p v-if="view.rows.length === 0" class="fa-st__muted">{{ t('listEmpty') }}</p>
    <div v-else class="fa-st__strata-scroll" role="region" tabindex="0" :aria-label="t('listUnits')">
      <table class="fa-st__units-table">
        <thead>
          <tr>
            <th scope="col">#</th>
            <th v-for="column in view.columns" :key="column" scope="col">{{ column }}</th>
            <td></td>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in view.rows" :key="index" :aria-current="index === selected ? 'true' : undefined" :data-unit="index">
            <th scope="row">
              <button type="button" class="fa-st__unit-select" :aria-label="t('listSelect', { number: index + 1 })" :aria-pressed="index === selected" @click="$emit('select', index)">{{ index + 1 }}</button>
            </th>
            <td v-for="(value, column) in row" :key="column">{{ value }}</td>
            <td><FaButton size="sm" variant="ghost" icon="trash" icon-only :label="t('listRemove', { number: index + 1 })" @click="$emit('remove', index)" /></td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="fa-st__units-totals" data-totals>
      <h4 class="fa-st__caption">{{ t('listTotals') }}</h4>
      <dl v-if="view.totals.length" class="fa-st__kv">
        <template v-for="total in view.totals" :key="total.role">
          <dt>{{ total.label }} → {{ total.target }}</dt>
          <dd :data-total="total.role">{{ total.value }}</dd>
        </template>
      </dl>
      <p v-else class="fa-st__muted">{{ methodNumber ? t('listTransferNone') : t('chooseMethodFirst') }}</p>
      <p v-if="view.incomplete" class="fa-st__muted">{{ t('listIncomplete', { count: view.incomplete }) }}</p>
      <p class="fa-st__hint"><strong>{{ t('webHint') }}:</strong> {{ t('listTotalsNote') }}</p>
      <FaButton variant="primary" :label="t('listTransfer', { number: methodNumber || '–' })" :disabled="!view.transferable || view.rows.length === 0" data-action="unit-transfer" @click="$emit('transfer')" />
    </div>

    <FaDialog :open="pasting" :title="t('listPasteTitle')" size="lg" :locale="locale" @update:open="pasting = false">
      <p :id="`${id}-help`" class="fa-st__muted">{{ t('listPasteHelp', { columns: pasteColumns }) }}</p>
      <label class="fa-st__label-text" :for="`${id}-paste`">{{ t('listPasteLabel') }}</label>
      <textarea :id="`${id}-paste`" v-model="pasted" class="fa-st__input fa-st__textarea" rows="8" spellcheck="false" :aria-describedby="`${id}-help`"></textarea>
      <template #footer>
        <FaButton :label="t('cancel')" @click="pasting = false" />
        <FaButton variant="primary" :label="t('listPasteApply')" :disabled="!pasted.trim()" data-action="unit-paste-apply" @click="applyPaste" />
      </template>
    </FaDialog>
  </section>
</template>
