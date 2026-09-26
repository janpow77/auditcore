<script setup lang="ts">
import {
  extrapolationCellLabel,
  extrapolationIssueText,
  extrapolationMessages,
  STRATUM_FIELDS,
  type ExtrapolationController,
  type ExtrapolationData,
} from '@auditcore/ui-core'
import FaButton from '../base/FaButton.vue'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'

const props = withDefaults(defineProps<{ controller: ExtrapolationController; state: ExtrapolationData; locale?: Locale }>(), { locale: undefined })
const { t } = useI18n(extrapolationMessages, () => props.locale)
const id = useId('fa-extrapolation-strata')
const issue = (index: number, key: string): string => extrapolationIssueText(props.state.issues, `strata.${index}.${key}`, t)
const value = (event: Event): string => (event.target as HTMLInputElement).value
</script>

<template>
  <section class="fa-extrapolation__card" :aria-labelledby="`${id}-title`">
    <h3 :id="`${id}-title`" class="fa-extrapolation__heading">{{ t('strata') }}</h3>
    <p class="fa-extrapolation__hint">{{ t('strataHint') }}</p>
    <div class="fa-extrapolation__scroll">
      <table class="fa-extrapolation__grid" data-testid="extrapolation-strata">
        <thead>
          <tr>
            <th v-for="field in STRATUM_FIELDS" :key="field.key" scope="col">{{ t(field.label) }}</th>
            <th scope="col">{{ t('remove') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in state.form.strata" :key="row.key">
            <td v-for="field in STRATUM_FIELDS" :key="field.key">
              <input
                class="fa-extrapolation__input"
                :class="{ 'fa-extrapolation__input--number': field.numeric }"
                :inputmode="field.numeric ? 'decimal' : undefined"
                :value="row[field.key]"
                :aria-label="extrapolationCellLabel(t, field.label, index + 1)"
                :aria-invalid="issue(index, field.key) ? 'true' : undefined"
                :title="issue(index, field.key) || undefined"
                @input="controller.updateStratum(index, { [field.key]: value($event) })"
              />
            </td>
            <td>
              <FaButton size="sm" variant="ghost" icon="trash" icon-only :label="t('removeRow', { what: t('stratumName'), row: index + 1 })" :disabled="state.form.strata.length <= 1" @click="controller.removeStratum(index)" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="fa-extrapolation__actions">
      <FaButton size="sm" icon="plus" data-testid="extrapolation-add-stratum" @click="controller.addStratum">{{ t('addStratum') }}</FaButton>
    </div>
  </section>
</template>
