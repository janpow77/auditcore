<script setup lang="ts">
import { computed, ref } from 'vue'
import FaBadge from '../../base/FaBadge.vue'
import FaButton from '../../base/FaButton.vue'
import FaTextField from '../../base/FaTextField.vue'
import { useId } from '../../composables/useId'
import { useI18n } from '../../i18n'
import { dataprotectionMessages } from '../core'
import { completeness, completenessTone, groupByDepartment, issuesFor, type Completeness } from '../core'
import type { Activity, Issue, RegisterContent } from '../core'

const props = withDefaults(defineProps<{
  content: RegisterContent
  issues?: Issue[]
  selected?: number | null
  editing?: boolean
}>(), { issues: () => [], selected: null, editing: false })

const emit = defineEmits<{ 'activity-select': [index: number]; add: [department: string] }>()
const { t } = useI18n(dataprotectionMessages)
const query = ref('')
const department = ref('')
const selectId = useId('fa-vvt-department')
const groups = computed(() => groupByDepartment(props.content, query.value))

function state(activity: Activity): Completeness {
  return completeness(issuesFor(props.issues, activity))
}

function stateLabel(value: Completeness): string {
  if (value.blocking) return value.blocking === 1 ? t('missingOne') : t('missing', { count: value.blocking })
  if (value.hints) return value.hints === 1 ? t('hintOne') : t('hints', { count: value.hints })
  return t('complete')
}

function name(activity: Activity): string {
  return (typeof activity.name === 'string' && activity.name.trim()) || t('unnamed')
}
</script>

<template>
  <nav class="fa-dataprotection__panel" :aria-label="t('activities', { count: content.taetigkeiten.length })" data-testid="vvt-list">
    <h3>{{ t('activities', { count: content.taetigkeiten.length }) }}</h3>
    <FaTextField v-model="query" type="search" :label="t('search')" hide-label :placeholder="t('search')" />
    <p v-if="!content.taetigkeiten.length" class="fa-dataprotection__muted">{{ t('noActivities') }}</p>
    <p v-else-if="!groups.length" class="fa-dataprotection__muted">{{ t('noMatches') }}</p>
    <template v-for="group in groups" :key="group.department">
      <h4>{{ group.department || t('withoutDepartment') }}</h4>
      <ul class="fa-vvt__list">
        <li v-for="item in group.items" :key="item.index">
          <button
            type="button"
            class="fa-vvt__item"
            :aria-current="item.index === selected ? 'true' : undefined"
            @click="emit('activity-select', item.index)"
          >
            <span>{{ name(item.activity) }}</span>
            <FaBadge :tone="completenessTone(state(item.activity))">{{ stateLabel(state(item.activity)) }}</FaBadge>
          </button>
        </li>
      </ul>
    </template>
    <div v-if="editing" class="fa-dataprotection__field">
      <label :for="selectId">{{ t('colDepartment') }}</label>
      <select :id="selectId" v-model="department">
        <option value="">{{ t('withoutDepartment') }}</option>
        <option v-for="entry in content.referate" :key="entry" :value="entry">{{ entry }}</option>
      </select>
      <FaButton icon="plus" :label="t('addActivity')" @click="emit('add', department)" />
    </div>
  </nav>
</template>
