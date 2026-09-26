<script setup lang="ts">
import { ref, watch } from 'vue'
import { createShareSearch, shareName, type Share, type SharePermission, type UserRef } from '@flowaudit/kanban-core'
import FaButton from '../base/FaButton.vue'
import FaDialog from '../base/FaDialog.vue'
import FaTextField from '../base/FaTextField.vue'
import { useStore } from '../composables/useStore'
import { useI18n, type Locale } from '../i18n'
import { initials } from './cardView'
import { kanbanDialogMessages } from './messages'

const PERMISSIONS: readonly SharePermission[] = ['read', 'edit']

const props = withDefaults(defineProps<{
  open: boolean
  shares: readonly Share[]
  search?: ((query: string) => Promise<UserRef[]>) | null
  users?: readonly UserRef[]
  locale?: Locale
}>(), { search: null, users: () => [], locale: undefined })

const emit = defineEmits<{ close: []; share: [userId: string, permission: SharePermission]; revoke: [userId: string] }>()
const { t } = useI18n(kanbanDialogMessages, () => props.locale)
const query = ref('')
const permission = ref<SharePermission>('read')
const confirming = ref<string | null>(null)
const finder = createShareSearch()
const found = useStore(finder.store)
const name = (userId: string): string => shareName(userId, found.value.known, props.users)

watch(query, (value) => void finder.query(value, props.search, props.shares))

watch(() => props.open, (open) => {
  if (open) return
  query.value = ''
  confirming.value = null
})

function add(user: UserRef): void {
  emit('share', user.id, permission.value)
  query.value = ''
}

function revoke(userId: string): void {
  if (confirming.value !== userId) {
    confirming.value = userId
    return
  }
  confirming.value = null
  emit('revoke', userId)
}
</script>

<template>
  <FaDialog :open="open" :title="t('shareTitle')" :description="t('shareDescription')" :locale="locale" @close="emit('close')">
    <div v-if="search" class="fa-kanban-detail__row">
      <FaTextField v-model="query" type="search" :label="t('searchUser')" style="flex: 1" autofocus />
      <label class="fa-field">
        <span class="fa-field__label">{{ t('permission') }}</span>
        <select v-model="permission" class="fa-kanban-select">
          <option v-for="entry in PERMISSIONS" :key="entry" :value="entry">{{ t(`permission_${entry}`) }}</option>
        </select>
      </label>
    </div>
    <ul v-if="found.results.length" class="fa-kanban-share__results" role="listbox" :aria-label="t('searchUser')">
      <li v-for="user in found.results" :key="user.id" role="option" aria-selected="false">
        <button type="button" @click="add(user)">{{ user.name }} <small v-if="user.email">· {{ user.email }}</small></button>
      </li>
    </ul>
    <p v-if="shares.length === 0" class="fa-kanban-settings__hint">{{ t('noShares') }}</p>
    <div v-for="share in shares" :key="share.user_id" class="fa-kanban-share__person" :data-share="share.user_id">
      <span class="fa-kanban-share__avatar" aria-hidden="true">{{ initials(name(share.user_id)) }}</span>
      <span class="fa-kanban-share__name">{{ name(share.user_id) }}</span>
      <select class="fa-kanban-select" :value="share.permission" :aria-label="t('permission')" @change="emit('share', share.user_id, ($event.target as HTMLSelectElement).value as SharePermission)">
        <option v-for="entry in PERMISSIONS" :key="entry" :value="entry">{{ t(`permission_${entry}`) }}</option>
      </select>
      <FaButton size="sm" :variant="confirming === share.user_id ? 'danger' : 'ghost'" icon="trash" :icon-only="confirming !== share.user_id" :label="confirming === share.user_id ? t('confirmRevoke') : t('revoke', { name: name(share.user_id) })" @click="revoke(share.user_id)" />
    </div>
  </FaDialog>
</template>
