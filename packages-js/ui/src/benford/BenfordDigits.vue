<script setup lang="ts">
import { computed } from 'vue'
import { benfordDigitColumns, benfordDigitRows, benfordMessages, type Conformity } from '@flowaudit/ui-core'
import { useI18n, type Locale } from '../i18n'
import FaTable from '../table/FaTable.vue'

const props = withDefaults(defineProps<{ conformity: Conformity; locale?: Locale }>(), { locale: undefined })
const { t, locale: active } = useI18n(benfordMessages, () => props.locale)
const columns = computed(() => benfordDigitColumns(t, active.value))
const rows = computed(() => benfordDigitRows(props.conformity))
</script>

<template>
  <details class="fa-benford__digits" :open="conformity.rows.length <= 10">
    <summary>{{ t('table') }}</summary>
    <FaTable :columns="columns" :rows="rows" :caption="t('table')" :locale="locale" data-testid="benford-table">
      <template #cell-exceeds="{ value }">
        <span v-if="value === true" class="fa-benford__flag">{{ t('yes') }}</span>
      </template>
    </FaTable>
  </details>
</template>
