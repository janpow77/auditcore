<script setup lang="ts">
import { computed, ref, shallowRef } from 'vue'
import { KanbanBoard, KanbanBoardList, type Locale } from '@auditcore/ui'
import { MemoryBoardPort, type CardLink } from '@auditcore/kanban-core'
import { demoLocale } from '../../locale'
import { DEMO_USERS, demoBoards } from './demoData'

const port = shallowRef(new MemoryBoardPort({ userId: 'anna', boards: demoBoards(), users: DEMO_USERS, latency: 120 }))
const userId = ref('anna')
const boardId = ref('vp-2026')
const revision = ref(0)
const last = ref('')
const locale = computed<Locale>(() => demoLocale.value)

function switchUser(id: string): void {
  port.value.switchUser(id)
  userId.value = id
  revision.value += 1
}

function navigate(link: CardLink): void {
  last.value = `navigate → ${link.kind}:${link.target}`
}
</script>

<template>
  <h1>Kanban</h1>
  <p>
    Board mit In-Memory-Port (gleiche Regeln wie <code>auditcore_kanban</code>): Ziehen mit Maus oder Touch,
    Tastatur (Leertaste, Pfeiltasten, Strg+Pfeile), WIP-Limit in „Prüfung“, eingeschränkte Übergänge im cockpit-Board.
  </p>
  <label class="fa-field" style="max-width: 16rem; margin-bottom: 1rem">
    <span class="fa-field__label">Angemeldet als</span>
    <select class="fa-kanban-select" :value="userId" data-testid="demo-user" @change="switchUser(($event.target as HTMLSelectElement).value)">
      <option v-for="user in DEMO_USERS" :key="user.id" :value="user.id">{{ user.name }}</option>
    </select>
  </label>
  <div style="display: grid; grid-template-columns: 15rem minmax(0, 1fr); gap: 1.5rem; align-items: start">
    <KanbanBoardList :key="`list-${revision}`" :port="port" :active-id="boardId" :locale="locale" @board-select="boardId = $event" />
    <KanbanBoard :key="`${boardId}-${revision}`" :port="port" :board-id="boardId" :users="DEMO_USERS" :locale="locale" shared-by-name="Anna Becker" @navigate="navigate" />
  </div>
  <p aria-live="polite" data-testid="demo-last">{{ last }}</p>
</template>
