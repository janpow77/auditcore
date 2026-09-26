<script setup lang="ts">
import { computed, ref } from 'vue'
import FaButton from '../../base/FaButton.vue'
import FaTextField from '../../base/FaTextField.vue'
import { useI18n } from '../../i18n'
import { dataprotectionMessages } from '../messages'
import { coverIssues } from '../registerView'
import type { Issue, Person, RegisterContent } from '../types'

const props = withDefaults(defineProps<{
  content: RegisterContent
  issues?: Issue[]
  editing?: boolean
}>(), { issues: () => [], editing: false })

const emit = defineEmits<{
  'person-change': [part: 'verantwortlicher' | 'dsb', person: Person]
  'departments-change': [departments: string[]]
}>()
const { t } = useI18n(dataprotectionMessages)
const fresh = ref('')
const notes = computed(() => coverIssues(props.issues))
const parts = computed(() => [
  { part: 'verantwortlicher' as const, label: t('controller'), person: props.content.deckblatt.verantwortlicher ?? {} },
  { part: 'dsb' as const, label: t('dpo'), person: props.content.deckblatt.dsb ?? {} },
])

function addDepartment(): void {
  const name = fresh.value.trim()
  if (!name || props.content.referate.includes(name)) return
  emit('departments-change', [...props.content.referate, name])
  fresh.value = ''
}
</script>

<template>
  <section class="fa-dataprotection__panel" data-testid="vvt-cover" :aria-label="t('cover')">
    <h3>{{ t('cover') }}</h3>
    <div class="fa-dataprotection__grid">
      <template v-for="entry in parts" :key="entry.part">
        <FaTextField
          v-if="editing"
          :model-value="entry.person.name ?? ''"
          :label="entry.label"
          required
          @update:model-value="emit('person-change', entry.part, { name: $event })"
        />
        <div v-else class="fa-dataprotection__field">
          <span class="fa-dataprotection__label">{{ entry.label }}</span>
          <span>{{ entry.person.name || t('empty') }}</span>
        </div>
      </template>
    </div>
    <ul v-if="notes.length" class="fa-dataprotection__issues">
      <li v-for="issue in notes" :key="issue.subject" class="is-blocking">{{ issue.message }}</li>
    </ul>
    <h4>{{ t('departments') }}</h4>
    <ul class="fa-dataprotection__chips">
      <li v-for="name in content.referate" :key="name">
        {{ name }}
        <FaButton
          v-if="editing"
          variant="ghost"
          size="sm"
          icon="close"
          icon-only
          :label="t('departmentRemove', { name })"
          @click="emit('departments-change', content.referate.filter((entry) => entry !== name))"
        />
      </li>
    </ul>
    <div v-if="editing" class="fa-dataprotection__bar">
      <FaTextField v-model="fresh" :label="t('departmentNew')" hide-label :placeholder="t('departmentNew')" @keydown.enter.prevent="addDepartment" />
      <FaButton icon="plus" :label="t('departmentAdd')" @click="addDepartment" />
    </div>
  </section>
</template>
