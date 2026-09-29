<script setup lang="ts">
import { computed, onBeforeUnmount, watch } from 'vue'
import { createAccountController, accountMessages, accountIsEmpty, accountRows, accountImageUrl, accountPreviewStyle, accountWelcomePreview, type AccountItem, type AccountPort } from '@auditcore/ui-core'
import { useStore } from '../composables/useStore'
import { useI18n, type Locale } from '../i18n'
import AccountImageField from './AccountImageField.vue'
const props = withDefaults(defineProps<{ port?: AccountPort | null; locale?: Locale }>(), { port: null, locale: undefined })
const emit = defineEmits<{ 'item-select': [item: AccountItem]; error: [message: string] }>()
const { t, locale: active } = useI18n(accountMessages, () => props.locale)
const controller = createAccountController({ port: () => props.port, callbacks: () => ({
  selected: (item) => emit('item-select', item), failed: (message) => emit('error', message),
}) })
const state = useStore(controller.store)
const rows = computed(() => accountRows(state.value))
watch(() => props.port, () => void controller.load(), { immediate: true })
onBeforeUnmount(controller.dispose)
</script>
<template>
  <section class="fa-account" :lang="active" :aria-label="t('title')">
    <header class="fa-account__header"><span class="fa-account__eyebrow">FlowAudit</span><h2>{{ t('title') }}</h2></header>
    <p v-if="state.busy" role="status">{{ t('loading') }}</p>
    <p v-if="state.error" class="fa-account__failure" role="alert">{{ t('failed', { message: state.error }) }}</p>
    <p v-if="state.notice" role="status">{{ t('saved') }}</p>
    <p v-if="state.dirty" class="fa-account__muted" role="status">{{ t('dirty') }}</p>
    <p v-if="accountIsEmpty(state)" class="fa-account__muted">{{ t('empty') }}</p>
    <div class="fa-account__layout">
      <nav :aria-label="t('title')"><ul class="fa-account__list">
        <li v-for="(row, index) in rows" :key="row.id">
          <small v-if="state.items[index]?.group && (index === 0 || state.items[index]?.group !== state.items[index - 1]?.group)" class="fa-account__group">{{ state.items[index]?.group }}</small>
          <button type="button" :class="['fa-account__item', row.selected && 'fa-account__item--selected']" :aria-pressed="row.selected" :disabled="state.dirty || !!state.busy" @click="controller.select(row.id)">{{ row.label }}</button>
        </li>
      </ul></nav>
      <form v-if="state.document" :key="state.document.id" class="fa-account__card" @submit.prevent="controller.save">
        <h3>{{ state.document.title }}</h3><p class="fa-account__muted">{{ state.document.description }}</p>
        <p v-if="!state.document.editable">{{ t('readonly') }}</p>
        <fieldset :disabled="!!state.busy || !state.document.editable" class="fa-account__fields">
          <component :is="field.type === 'image' ? 'div' : 'label'" v-for="field in state.document.fields" :key="field.id" class="fa-account__field" :class="{ 'fa-account__wide': ['textarea', 'image'].includes(field.type ?? '') }">
            <span>{{ field.label }}{{ field.required ? ' *' : '' }}</span>
            <AccountImageField v-if="field.type === 'image'" :label="field.label" :allow-camera="state.document.id === 'profile'" :url="state.images[field.id] ?? accountImageUrl(port, state.draft[field.id] ?? '')" :disabled="!!state.busy || !state.document.editable || !!field.readonly" :locale="active" @upload="controller.upload(field.id, $event)" @remove="controller.edit(field.id, '')" />
            <textarea v-else-if="field.type === 'textarea'" :value="state.draft[field.id] ?? ''" :readonly="field.readonly" :required="field.required" rows="6" @input="controller.edit(field.id, ($event.target as HTMLTextAreaElement).value)" />
            <select v-else-if="field.type === 'select' || field.type === 'multiselect'" :multiple="field.type === 'multiselect'" :value="field.type === 'multiselect' ? (state.draft[field.id] ?? '').split('\n') : state.draft[field.id] ?? ''" :disabled="field.readonly" :required="field.required" @change="controller.edit(field.id, field.type === 'multiselect' ? Array.from(($event.target as HTMLSelectElement).selectedOptions, option => option.value).join('\n') : ($event.target as HTMLSelectElement).value)">
              <option value="">—</option><option v-for="option in field.options" :key="option.value" :value="option.value">{{ option.label }}</option>
            </select>
            <input v-else :type="field.type ?? 'text'" :value="state.draft[field.id] ?? ''" :readonly="field.readonly" :required="field.required" :autocomplete="field.autocomplete ?? 'off'" @input="controller.edit(field.id, ($event.target as HTMLInputElement).value)">
            <small v-if="field.hint">{{ field.hint }}</small>
          </component>
        </fieldset>
        <aside v-if="state.document.kind === 'branding'" class="fa-account__preview" :style="accountPreviewStyle(state.draft)"><strong>{{ t('preview') }}</strong><p>{{ state.draft.document_header }}</p><p>{{ state.draft.document_footer }}</p></aside>
        <aside v-if="state.document.kind === 'welcome'" class="fa-account__welcome"><strong>{{ t('preview') }}</strong><p>{{ accountWelcomePreview(state.document, state.draft) }}</p></aside>
        <footer v-if="state.document.editable" class="fa-account__actions">
          <button type="button" :disabled="!state.dirty || !!state.busy" @click="controller.discard">{{ t('discard') }}</button>
          <button type="submit" class="fa-account__primary" :disabled="!state.dirty || !!state.busy">{{ state.document.submitLabel || t('save') }}</button>
        </footer>
      </form>
      <p v-else-if="rows.length && !state.busy" class="fa-account__card fa-account__muted">{{ t('choose') }}</p>
    </div>
  </section>
</template>
