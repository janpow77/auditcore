<script setup lang="ts">
import { computed } from 'vue'
import {
  extrapolationCellLabel,
  extrapolationIssueText,
  extrapolationMessages,
  UNIT_FIELDS,
  UNIT_FLAGS,
  type ExtrapolationController,
  type ExtrapolationData,
} from '@auditcore/ui-core'
import FaButton from '../base/FaButton.vue'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'

const props = withDefaults(defineProps<{ controller: ExtrapolationController; state: ExtrapolationData; locale?: Locale }>(), { locale: undefined })
const { t } = useI18n(extrapolationMessages, () => props.locale)
const id = useId('fa-extrapolation-units')
const names = computed(() => props.state.form.strata.map((row) => row.name.trim()).filter(Boolean))
const issue = (index: number, key: string): string => extrapolationIssueText(props.state.issues, `units.${index}.${key}`, t)
const value = (event: Event): string => (event.target as HTMLInputElement).value
const checked = (event: Event): boolean => (event.target as HTMLInputElement).checked
</script>

<template>
  <section class="fa-extrapolation__card" :aria-labelledby="`${id}-title`">
    <h3 :id="`${id}-title`" class="fa-extrapolation__heading">{{ t('units') }}</h3>
    <p class="fa-extrapolation__hint">{{ t('unitsHint') }}</p>
    <p v-if="state.form.units.length === 0" class="fa-extrapolation__muted">{{ t('noUnits') }}</p>
    <div v-else class="fa-extrapolation__scroll">
      <table class="fa-extrapolation__grid" data-testid="extrapolation-units">
        <thead>
          <tr>
            <th scope="col">{{ t('stratum') }}</th>
            <th v-for="field in UNIT_FIELDS" :key="field.key" scope="col">{{ t(field.label) }}</th>
            <th v-for="flag in UNIT_FLAGS" :key="flag.key" scope="col">{{ t(flag.label) }}</th>
            <th scope="col">{{ t('remove') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in state.form.units" :key="row.key">
            <td>
              <select class="fa-extrapolation__select" :value="row.stratum" :aria-label="extrapolationCellLabel(t, 'stratum', index + 1)" :aria-invalid="issue(index, 'stratum') ? 'true' : undefined" @change="controller.updateUnit(index, { stratum: value($event) })">
                <option value="">{{ t('choose') }}</option>
                <option v-for="name in names" :key="name" :value="name">{{ name }}</option>
              </select>
            </td>
            <td v-for="field in UNIT_FIELDS" :key="field.key">
              <input
                class="fa-extrapolation__input"
                :class="{ 'fa-extrapolation__input--number': field.numeric }"
                :inputmode="field.numeric ? 'decimal' : undefined"
                :value="row[field.key]"
                :aria-label="extrapolationCellLabel(t, field.label, index + 1)"
                :aria-invalid="issue(index, field.key) ? 'true' : undefined"
                :title="issue(index, field.key) || undefined"
                @input="controller.updateUnit(index, { [field.key]: value($event) })"
              />
            </td>
            <td v-for="flag in UNIT_FLAGS" :key="flag.key">
              <input type="checkbox" class="fa-extrapolation__check" :checked="row[flag.key]" :aria-label="extrapolationCellLabel(t, flag.label, index + 1)" @change="controller.updateUnit(index, { [flag.key]: checked($event) })" />
            </td>
            <td>
              <FaButton size="sm" variant="ghost" icon="trash" icon-only :label="t('removeRow', { what: t('unitId'), row: index + 1 })" @click="controller.removeUnit(index)" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="fa-extrapolation__actions">
      <FaButton size="sm" icon="plus" data-testid="extrapolation-add-unit" @click="controller.addUnit">{{ t('addUnit') }}</FaButton>
    </div>
  </section>
</template>
