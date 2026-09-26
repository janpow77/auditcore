<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useId } from '../../composables/useId'
import { useI18n } from '../../i18n'
import { dataprotectionMessages } from '../core'
import { parseCount } from '../core'
import type { RegisterColumn, FieldValue, Issue } from '../core'

const props = withDefaults(defineProps<{
  column: RegisterColumn
  value?: FieldValue
  issues?: Issue[]
  departments?: string[]
}>(), { value: null, issues: () => [], departments: () => [] })

const emit = defineEmits<{ 'value-change': [value: FieldValue] }>()
const { t } = useI18n(dataprotectionMessages)
const id = useId('fa-vvt-field')
const noteId = `${id}-note`
const countText = ref('')
const countError = ref(false)
const long = computed(() => !['name', 'referat', 'ansprechperson'].includes(props.column.key))
const blocking = computed(() => props.issues.some((issue) => issue.blocking))
const described = computed(() => (props.issues.length || countError.value ? noteId : undefined))

watch(() => props.value, (value) => {
  countText.value = value === null || value === undefined ? '' : String(value)
  countError.value = false
}, { immediate: true })

function onText(event: Event): void {
  emit('value-change', (event.target as HTMLInputElement | HTMLTextAreaElement).value)
}

function onCount(event: Event): void {
  countText.value = (event.target as HTMLInputElement).value
  const parsed = parseCount(countText.value)
  countError.value = parsed === undefined
  if (parsed !== undefined) emit('value-change', parsed)
}

function flagValue(choice: 'yes' | 'no' | 'open'): boolean | null {
  return choice === 'yes' ? true : choice === 'no' ? false : null
}
</script>

<template>
  <fieldset v-if="column.kind === 'flag'" class="fa-dataprotection__field" :class="{ 'fa-dataprotection__field--required': column.required }" :aria-describedby="described">
    <legend>{{ column.title }}</legend>
    <div class="fa-dataprotection__choices">
      <label v-for="choice in (['yes', 'no', 'open'] as const)" :key="choice" class="fa-dataprotection__choice">
        <input
          type="radio"
          :name="id"
          :checked="value === flagValue(choice)"
          :aria-invalid="blocking ? 'true' : undefined"
          @change="emit('value-change', flagValue(choice))"
        />
        {{ t(choice) }}
      </label>
    </div>
    <span v-if="column.reference" class="fa-dataprotection__ref">{{ column.reference }}</span>
    <div v-if="issues.length" :id="noteId">
      <p v-for="issue in issues" :key="issue.code + issue.message" class="fa-dataprotection__note" :class="{ 'fa-dataprotection__note--blocking': issue.blocking }">{{ issue.message }}</p>
    </div>
  </fieldset>
  <div v-else class="fa-dataprotection__field" :class="{ 'fa-dataprotection__field--required': column.required }">
    <label :for="id">{{ column.title }}</label>
    <input
      v-if="column.kind === 'count'"
      :id="id"
      type="text"
      inputmode="numeric"
      :value="countText"
      :aria-invalid="blocking || countError ? 'true' : undefined"
      :aria-describedby="described"
      @input="onCount"
    />
    <textarea
      v-else-if="long"
      :id="id"
      rows="2"
      :value="typeof value === 'string' ? value : ''"
      :required="column.required"
      :aria-invalid="blocking ? 'true' : undefined"
      :aria-describedby="described"
      @input="onText"
    />
    <input
      v-else
      :id="id"
      type="text"
      :value="typeof value === 'string' ? value : ''"
      :list="column.key === 'referat' ? `${id}-list` : undefined"
      :required="column.required"
      :aria-invalid="blocking ? 'true' : undefined"
      :aria-describedby="described"
      @input="onText"
    />
    <datalist v-if="column.key === 'referat'" :id="`${id}-list`">
      <option v-for="department in departments" :key="department" :value="department" />
    </datalist>
    <span v-if="column.reference" class="fa-dataprotection__ref">{{ column.reference }}</span>
    <div v-if="issues.length || countError" :id="noteId">
      <p v-if="countError" class="fa-dataprotection__note fa-dataprotection__note--blocking">{{ t('invalidCount') }}</p>
      <p v-for="issue in issues" :key="issue.code + issue.message" class="fa-dataprotection__note" :class="{ 'fa-dataprotection__note--blocking': issue.blocking }">{{ issue.message }}</p>
    </div>
  </div>
</template>
