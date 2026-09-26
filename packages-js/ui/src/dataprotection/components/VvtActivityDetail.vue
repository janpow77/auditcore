<script setup lang="ts">
import { computed } from 'vue'
import FaButton from '../../base/FaButton.vue'
import { useI18n } from '../../i18n'
import { dataprotectionMessages } from '../core'
import { displayValue, fieldIssues } from '../core'
import type { Activity, RegisterColumn, FieldValue, Issue } from '../core'
import VvtField from './VvtField.vue'

const props = withDefaults(defineProps<{
  activity: Activity
  columns?: RegisterColumn[]
  issues?: Issue[]
  departments?: string[]
  editing?: boolean
}>(), { columns: () => [], issues: () => [], departments: () => [], editing: false })

const emit = defineEmits<{ 'field-change': [key: string, value: FieldValue]; remove: [] }>()
const { t } = useI18n(dataprotectionMessages)
const title = computed(() => (typeof props.activity.name === 'string' && props.activity.name.trim()) || t('unnamed'))
const texts = computed(() => ({ yes: t('yes'), no: t('no'), empty: t('empty') }))
</script>

<template>
  <article class="fa-dataprotection__panel" data-testid="vvt-detail" :aria-label="title">
    <div class="fa-dataprotection__bar">
      <h3>{{ title }}</h3>
      <span v-if="activity.id" class="fa-dataprotection__muted">{{ activity.id }}</span>
      <div v-if="editing" class="fa-dataprotection__actions">
        <FaButton variant="ghost" size="sm" icon="trash" :label="t('removeActivity')" @click="emit('remove')" />
      </div>
    </div>
    <div v-if="editing" class="fa-dataprotection__grid">
      <VvtField
        v-for="column in columns"
        :key="column.key"
        :column="column"
        :value="activity[column.key] ?? null"
        :issues="fieldIssues(issues, activity, column.key)"
        :departments="departments"
        @value-change="emit('field-change', column.key, $event)"
      />
    </div>
    <dl v-else class="fa-dataprotection__dl">
      <template v-for="column in columns" :key="column.key">
        <dt>{{ column.title }}<br /><span class="fa-dataprotection__ref">{{ column.reference }}</span></dt>
        <dd>
          {{ displayValue(activity[column.key], texts) }}
          <span v-for="issue in fieldIssues(issues, activity, column.key)" :key="issue.message" class="fa-dataprotection__note" :class="{ 'fa-dataprotection__note--blocking': issue.blocking }">
            <br />{{ issue.message }}
          </span>
        </dd>
      </template>
    </dl>
  </article>
</template>
