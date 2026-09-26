<script setup lang="ts">
/**
 * Notes: internal note in the XML (`flowaudit:interneNotiz`) and comments
 * per element (legacy `comments` of the audit_designer, kept by the app).
 */
import { computed, ref } from 'vue'
import type { Comment } from '@flowaudit/bpmn-flowaudit'
import { commentsOf, newComment, toggleResolved as toggled } from '@flowaudit/bpmn-flowaudit/ui'
import FaIcon from '../../components/base/FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'
import { useEditorContext } from '../../stores/context'

const props = defineProps<{ comments: Comment[]; author: string }>()
const emit = defineEmits<{ (e: 'update:comments', value: Comment[]): void }>()
const { selection, readonly } = useEditorContext()
const { t } = useI18n()
const draft = ref('')

const elementId = computed(() => selection.element.value?.id ?? '')
const own = computed(() => commentsOf(props.comments, elementId.value))

function addComment(): void {
  if (!draft.value.trim() || !elementId.value) return
  emit('update:comments', [...props.comments, newComment(elementId.value, draft.value, props.author)])
  draft.value = ''
}

const toggleResolved = (id: string) => emit('update:comments', toggled(props.comments, id))
</script>

<template>
  <div class="fa-tab-notes">
    <label class="fa-field">
      <span class="fa-label">{{ t('props.internalNote') }}</span>
      <textarea
        class="fa-textarea"
        rows="4"
        :value="selection.extensions.value.internalNote ?? ''"
        :disabled="readonly()"
        @change="selection.write({ internalNote: ($event.target as HTMLTextAreaElement).value })"
      />
      <span class="fa-help">{{ t('props.internalNoteHelp') }}</span>
    </label>
    <section class="fa-section">
      <h3 class="fa-section__title">{{ t('props.comments') }}</h3>
      <ul class="fa-comments">
        <li v-for="comment in own" :key="comment.id" class="fa-card fa-comment" :class="{ 'fa-comment--resolved': comment.resolved }">
          <p>{{ comment.text }}</p>
          <footer>
            <span class="fa-help">{{ comment.author }} · {{ new Date(comment.timestamp).toLocaleString() }}</span>
            <label class="fa-check"><input type="checkbox" :checked="comment.resolved" @change="toggleResolved(comment.id)" />{{ t('props.commentResolved') }}</label>
          </footer>
        </li>
      </ul>
      <div class="fa-comments__new">
        <input v-model="draft" class="fa-input" :placeholder="t('props.commentAdd')" @keydown.enter.prevent="addComment" />
        <button type="button" class="fa-btn" :disabled="!draft.trim()" @click="addComment"><FaIcon name="comment" :size="16" />{{ t('common.add') }}</button>
      </div>
    </section>
  </div>
</template>
