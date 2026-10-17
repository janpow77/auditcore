<script setup lang="ts">
import '@auditcore/ui-core/styles/tokens.css'
import '@auditcore/ui-core/styles/base.css'
import './demo.css'
import { FaButton, applyTheme, type ThemeMode } from '@auditcore/ui'
import { ref } from 'vue'
import { SHEETS, plannedSheet } from '@auditcore/sampling-templates-core'
import { SamplingCalculator } from '../src/index'

/**
 * Demo des Stichprobenrechners. Parameter der Adresse: `?theme=dark|light`,
 * `?entwurf=0` (lokalen Entwurf abschalten), `?tokens=app` (Beispiel für die
 * Zuordnung anwendungseigener Tokens), `?sprache=en` (englische Arbeitsübersetzung),
 * `?blaetter=…` (nur diese Blätter verfügbar).
 */
const query = new URLSearchParams(window.location.search)
const theme = ref<ThemeMode>(query.get('theme') === 'dark' || query.get('theme') === 'light' ? (query.get('theme') as ThemeMode) : 'system')
const appTokens = ref(query.get('tokens') === 'app')
const localDraft = query.get('entwurf') !== '0'
const lastEvent = ref('')
/** `?blaetter=02_Grundgesamtheit,03_MUS_1Z` zeigt nur diese Blätter als verfügbar (stabile Browsertests). */
const only = query.get('blaetter')?.split(',') ?? null
const sheets = only ? SHEETS.map((sheet) => (only.includes(sheet.id) ? sheet : plannedSheet(sheet.id))) : SHEETS
const language = ref<'de' | 'en'>(query.get('sprache') === 'en' ? 'en' : 'de')
applyTheme(theme.value)

function setTheme(mode: ThemeMode): void {
  theme.value = mode
  applyTheme(mode)
}
</script>

<template>
  <div :class="{ 'demo--app-tokens': appTokens && theme !== 'dark' }">
    <div class="demo__bar">
      <strong>Demo @auditcore/sampling-templates-vue</strong>
      <span data-demo-event>{{ lastEvent }}</span>
      <span class="demo__spacer"></span>
      <FaButton size="sm" variant="ghost" :pressed="theme === 'light'" label="Hell" @click="setTheme('light')" />
      <FaButton size="sm" variant="ghost" :pressed="theme === 'dark'" label="Dunkel" @click="setTheme('dark')" />
      <FaButton size="sm" variant="ghost" :pressed="theme === 'system'" label="System" @click="setTheme('system')" />
      <FaButton size="sm" variant="ghost" :pressed="appTokens" label="Eigene Tokens" @click="appTokens = !appTokens" />
      <FaButton size="sm" variant="ghost" :pressed="language === 'en'" label="English" @click="language = language === 'en' ? 'de' : 'en'" />
    </div>
    <SamplingCalculator
      :sheets="sheets"
      :locale="language"
      :local-draft="localDraft"
      draft-key="demo"
      @saved="lastEvent = `gespeichert: ${$event}`"
      @opened="lastEvent = `geöffnet: ${$event}`"
      @exported="lastEvent = `exportiert: ${$event}`"
    />
  </div>
</template>
