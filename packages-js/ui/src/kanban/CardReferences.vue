<script setup lang="ts">
import type { Attachment, CardLink } from '@flowaudit/kanban-core'
import FaIcon from '../base/FaIcon.vue'
import { formatNumber, useI18n, type Locale } from '../i18n'
import { kanbanDialogMessages } from './messages'

const props = withDefaults(defineProps<{ links: readonly CardLink[]; attachments: readonly Attachment[]; locale?: Locale }>(), { locale: undefined })
const emit = defineEmits<{ navigate: [link: CardLink]; attachment: [attachment: Attachment] }>()
const { t, locale: active } = useI18n(kanbanDialogMessages, () => props.locale)

function size(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  const units = ['KB', 'MB', 'GB']
  let value = bytes / 1024
  let unit = 0
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024
    unit += 1
  }
  return `${formatNumber(value, active.value, { maximumFractionDigits: 1 })} ${units[unit]}`
}
</script>

<template>
  <div v-if="links.length" class="fa-kanban-detail__section">
    <span class="fa-kanban-detail__label">{{ t('links') }}</span>
    <ul class="fa-kanban-detail__list">
      <li v-for="link in links" :key="`${link.kind}:${link.target}`" class="fa-kanban-detail__item">
        <FaIcon name="share" :size="14" />
        <button type="button" class="fa-kanban-toolbar__rename" :aria-label="t('openLink', { title: link.title || link.target })" @click="emit('navigate', link)">
          {{ link.title || link.target }}
        </button>
        <span class="fa-badge">{{ link.kind }}</span>
      </li>
    </ul>
  </div>
  <div class="fa-kanban-detail__section">
    <span class="fa-kanban-detail__label">{{ t('attachments') }}</span>
    <ul v-if="attachments.length" class="fa-kanban-detail__list">
      <li v-for="file in attachments" :key="file.id" class="fa-kanban-detail__item">
        <FaIcon name="paperclip" :size="14" />
        <button type="button" class="fa-kanban-toolbar__rename" @click="emit('attachment', file)">{{ file.filename }}</button>
        <span class="fa-kanban-detail__meta-inline">{{ size(file.size) }}</span>
      </li>
    </ul>
    <p v-else class="fa-kanban-settings__hint">{{ t('noAttachments') }}</p>
    <slot name="attachments" />
  </div>
</template>
