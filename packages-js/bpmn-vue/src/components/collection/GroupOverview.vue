<script setup lang="ts">
/**
 * Overview of a folder (top level: the whole collection): one card per
 * subfolder with description and its diagrams, one card for the diagrams
 * directly in the folder. Legal basis coverage, expired validity and
 * collection issues sit in the collapsed section „Prüfhinweise“. Key
 * requirement coverage and status distribution stay available in
 * `groupOverview` but are no longer shown here.
 */
import { computed } from 'vue'
import { issueMessage, type FolderCard, type GroupOverview as Overview, type ProfileData, type ValidationIssue } from '@auditcore/bpmn-flowaudit'
import { hintCount, statusLabel as statusText, type FolderAction } from '@auditcore/bpmn-flowaudit/ui'
import { useI18n } from '../../i18n/useI18n'
import ToolbarMenu from '../base/ToolbarMenu.vue'
import InlineDescription from './InlineDescription.vue'
import InlineName from './InlineName.vue'

const props = withDefaults(
  defineProps<{ overview: Overview; profile?: ProfileData | null; issues: ValidationIssue[]; title: string; cards?: FolderCard[]; topLevel?: boolean; readonly?: boolean; folderActions?: FolderAction[] }>(),
  { profile: null, cards: () => [], topLevel: true, readonly: false, folderActions: () => [] },
)
const emit = defineEmits<{
  (e: 'open', id: string): void
  (e: 'describe-folder', id: string, text: string): void
  (e: 'rename-folder', id: string, name: string): void
  (e: 'describe-diagram', id: string, text: string): void
  (e: 'folder-action', id: string, folderId: string, diagramIds: string[]): void
}>()
const { t, locale } = useI18n()

const percent = computed(() => Math.round((props.overview.legalBasisCoverage ?? 0) * 100))
const hints = computed(() => hintCount(props.overview, props.issues))
const cardName = (card: FolderCard) => card.name || (props.topLevel ? t('collection.overview.loose') : props.title)
const countText = (count: number) => (count === 1 ? t('collection.overview.diagram') : t('collection.overview.diagrams', { count }))
const statusLabel = (code: string) => statusText(code, t, locale.value)
</script>

<template>
  <section class="fa-overview" :aria-label="t('collection.overview')">
    <h2>{{ title }}</h2>
    <p v-if="!cards.length" class="fa-help">{{ t('collection.overview.empty') }}</p>
    <div class="fa-overview__folders">
      <article v-for="card in cards" :key="card.folderId ?? '_'" class="fa-card fa-folder-card">
        <header class="fa-folder-card__head">
          <h3 class="fa-folder-card__name">
            <InlineName v-if="card.folderId" :text="card.name" :readonly="readonly" @save="emit('rename-folder', card.folderId, $event)" />
            <template v-else>{{ cardName(card) }}</template>
          </h3>
          <span class="fa-folder-card__count">{{ countText(card.count) }}</span>
          <ToolbarMenu v-if="card.folderId && folderActions.length" v-slot="{ close }" :label="t('collection.folderActions', { name: card.name })" icon="more" align="right">
            <button
              v-for="action in folderActions"
              :key="action.id"
              type="button"
              role="menuitem"
              class="fa-menu-item"
              @click="(emit('folder-action', action.id, card.folderId, card.diagrams.map((diagram) => diagram.id)), close())"
            >
              <span>{{ action.label }}</span>
            </button>
          </ToolbarMenu>
        </header>
        <InlineDescription v-if="card.folderId" :text="card.description" :name="card.name" :readonly="readonly" @save="emit('describe-folder', card.folderId, $event)" />
        <ul v-if="card.diagrams.length" class="fa-folder-card__list">
          <li v-for="diagram in card.diagrams" :key="diagram.id" class="fa-folder-card__item">
            <div class="fa-folder-card__row">
              <button type="button" class="fa-folder-card__open" @click="emit('open', diagram.id)">{{ diagram.name }}</button>
              <span v-if="diagram.status" class="fa-badge">{{ statusLabel(diagram.status) }}</span>
            </div>
            <InlineDescription :text="diagram.description" :name="diagram.name" :readonly="readonly" @save="emit('describe-diagram', diagram.id, $event)" />
          </li>
        </ul>
        <p v-else class="fa-help">{{ t('collection.overview.emptyFolder') }}</p>
      </article>
    </div>
    <details class="fa-overview__hints">
      <summary>{{ t('collection.overview.hints', { count: hints }) }}</summary>
      <div class="fa-overview__hints-body">
        <div class="fa-overview__legal">
          <span class="fa-label">{{ t('collection.overview.legal') }}</span>
          <strong>{{ overview.legalBasisCoverage === null ? '–' : `${percent} %` }}</strong>
          <div class="fa-meter" role="meter" :aria-valuenow="percent" aria-valuemin="0" aria-valuemax="100"><span :style="{ width: `${percent}%` }" /></div>
          <span class="fa-help">{{ t('collection.overview.legalValue', { with: overview.activitiesWithLegalBasis, total: overview.activities, percent }) }}</span>
        </div>
        <template v-if="overview.expired.length">
          <h3 class="fa-section__title fa-section">{{ t('collection.overview.expired') }}</h3>
          <button v-for="id in overview.expired" :key="id" type="button" class="fa-chip" @click="emit('open', id)">{{ id }}</button>
        </template>
        <template v-if="issues.length">
          <h3 class="fa-section__title fa-section">{{ t('collection.overview.issues') }}</h3>
          <ul class="fa-overview__issues">
            <li v-for="(item, index) in issues" :key="index">{{ issueMessage(item, locale) }}</li>
          </ul>
        </template>
        <p v-if="!hints" class="fa-help">{{ t('collection.overview.noHints') }}</p>
      </div>
    </details>
  </section>
</template>
