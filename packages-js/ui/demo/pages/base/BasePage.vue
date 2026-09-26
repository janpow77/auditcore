<script setup lang="ts">
import { ref } from 'vue'
import { FaBadge, FaButton, FaDialog, FaIcon, FaTextField, ICONS, type IconName } from '@auditcore/ui'

const dialogOpen = ref(false)
const title = ref('')
const iconNames = Object.keys(ICONS) as IconName[]
</script>

<template>
  <h1>Basiskomponenten</h1>
  <section class="demo-section">
    <h2>Schaltflächen</h2>
    <div class="demo-row">
      <FaButton variant="primary" icon="plus">Aufgabe anlegen</FaButton>
      <FaButton>Abbrechen</FaButton>
      <FaButton variant="ghost" icon="filter">Filtern</FaButton>
      <FaButton variant="danger" icon="trash">Löschen</FaButton>
      <FaButton icon="settings" icon-only label="Einstellungen" />
      <FaButton loading>Speichern</FaButton>
    </div>
  </section>
  <section class="demo-section">
    <h2>Kennzeichen</h2>
    <div class="demo-row">
      <FaBadge>neutral</FaBadge>
      <FaBadge tone="accent">in Prüfung</FaBadge>
      <FaBadge tone="success">abgeschlossen</FaBadge>
      <FaBadge tone="warning">fällig in 2 Tagen</FaBadge>
      <FaBadge tone="danger">überfällig</FaBadge>
    </div>
  </section>
  <section class="demo-section">
    <h2>Eingabefeld und Dialog</h2>
    <div class="demo-row">
      <FaTextField v-model="title" label="Titel" placeholder="z. B. Vorhabenprüfung 2026" hint="Pflichtangabe" />
      <FaButton variant="primary" data-testid="open-dialog" @click="dialogOpen = true">Dialog öffnen</FaButton>
    </div>
    <FaDialog v-model:open="dialogOpen" title="Board-Einstellungen" description="Spalten und Farben anpassen">
      <FaTextField label="Spaltenname" model-value="Prüfung" />
      <template #footer>
        <FaButton @click="dialogOpen = false">Abbrechen</FaButton>
        <FaButton variant="primary" @click="dialogOpen = false">Übernehmen</FaButton>
      </template>
    </FaDialog>
  </section>
  <section class="demo-section">
    <h2>Symbole</h2>
    <div class="demo-row">
      <span v-for="name in iconNames" :key="name" :title="name"><FaIcon :name="name" :size="22" /></span>
    </div>
  </section>
</template>
