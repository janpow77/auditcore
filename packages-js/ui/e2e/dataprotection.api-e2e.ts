import { readFileSync } from 'node:fs'
import { expect, test, type Page } from '@playwright/test'

const SCREENSHOTS = process.env.FA_SCREENSHOTS

async function openPage(page: Page): Promise<string[]> {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  page.on('console', (message) => {
    // Abgelehnte Vier-Augen-Anfragen (403/409) meldet der Browser als Konsolenfehler der Ressource.
    if (message.type() === 'error' && !/40[39]/.test(message.text())) errors.push(message.text())
  })
  await page.goto('/#/datenschutz')
  return errors
}

async function shot(page: Page, name: string): Promise<void> {
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/${name}.png`, fullPage: true })
}

test('VVT: Hinweise der Bibliothek, Entwurf ergänzen, Vier-Augen-Freigabe und CSV mit Formelschutz', async ({ page }) => {
  const errors = await openPage(page)
  const vvt = page.getByTestId('vvt')
  await expect(vvt.getByRole('heading', { name: /Verzeichnis von Verarbeitungstätigkeiten/ })).toBeVisible()
  await expect(vvt.getByTestId('vvt-status')).toContainText('Fassung 2 – Entwurf')
  await vvt.getByRole('button', { name: /Terminplanung über Online-Dienst/ }).click()
  await expect(vvt.getByTestId('vvt-list')).toContainText('2 Pflichtangaben fehlen')
  await expect(vvt.getByLabel('Speicherdauer', { exact: true })).toHaveAttribute('aria-invalid', 'true')
  await shot(page, 'dataprotection-1-vvt-hinweise')

  const detail = vvt.getByTestId('vvt-detail')
  await detail.getByLabel('Speicherdauer', { exact: true }).fill('Bis zum Abschluss der Prüfung, höchstens 2 Jahre')
  await detail.getByLabel('Garantien der Drittlandsübermittlung (Art. 46/49)').fill('Standardvertragsklauseln (Art. 46 Abs. 2 lit. c DSGVO)')
  await detail.getByRole('group', { name: 'Besondere Kategorien personenbezogener Daten' }).getByLabel('nein').check()
  await detail.getByLabel('Zahl der betroffenen Personen').fill('40')
  await expect(vvt.getByTestId('vvt-issues')).toContainText('Alle Pflichtangaben nach Art. 30 Abs. 1 DSGVO sind ausgefüllt.')
  await vvt.getByRole('button', { name: 'Entwurf speichern' }).click()
  await expect(vvt.locator('.fa-dataprotection__live')).toContainText('Entwurf gespeichert')
  await expect(vvt.getByRole('button', { name: 'Freigeben (Vier-Augen-Prinzip)' })).toBeDisabled()
  await expect(vvt.getByTestId('vvt-release-hint')).toContainText('Vier-Augen-Prinzip')

  await page.getByTestId('dp-actor').selectOption('daten-b')
  const other = page.getByTestId('vvt')
  await other.getByRole('button', { name: 'Freigeben (Vier-Augen-Prinzip)' }).click()
  await expect(other.getByTestId('vvt-status')).toContainText('Fassung 2 – freigegeben')
  await other.getByRole('button', { name: 'Versionshistorie' }).click()
  await expect(other.getByTestId('vvt-history')).toContainText('abgelöst')
  await shot(page, 'dataprotection-2-vvt-freigegeben')

  const [download] = await Promise.all([page.waitForEvent('download'), other.getByRole('button', { name: 'CSV' }).click()])
  expect(download.suggestedFilename()).toBe('Verarbeitungsverzeichnis_Fassung_2.csv')
  const csv = readFileSync(await download.path(), 'utf-8')
  expect(csv).toContain("'=Voreinstellung des Anbieters")
  expect(errors).toEqual([])
})

test('DSFA: Schwellwertanalyse, Risiko mit Vorschau der Bibliothek, Entscheidung und Tastatur', async ({ page }) => {
  const errors = await openPage(page)
  await page.getByTestId('dp-view').selectOption('dsfa')
  const dsfa = page.getByTestId('dsfa')
  await expect(dsfa.getByTestId('dsfa-overview')).toContainText('Vorhabenprüfung mit Stichprobe')
  await dsfa.getByRole('button', { name: 'Öffnen: Bewilligung von Zuwendungen' }).click()
  await expect(dsfa.getByTestId('dsfa-head')).toContainText('Fassung 1 – Entwurf')
  for (const key of ['art35_3_a', 'art35_3_b', 'art35_3_c', 'dsk_nr08_beschaeftigte']) {
    await dsfa.locator(`[data-question="${key}"]`).getByLabel('Nein').check()
  }
  await dsfa.locator('[data-question="edsa_05_umfang"]').getByLabel('Ja').check()
  await dsfa.locator('[data-question="edsa_04_sensible_daten"]').getByLabel('Ja').check()
  await expect(dsfa.getByTestId('dsfa-screening')).toContainText('Vorschau der Bibliothek')
  await expect(dsfa.getByTestId('dsfa-screening')).toContainText('DSFA erforderlich')
  await shot(page, 'dataprotection-3-dsfa-schwellwert')

  await dsfa.getByRole('tab', { name: '1. Schwellwertanalyse' }).focus()
  await page.keyboard.press('ArrowRight')
  await expect(dsfa.getByRole('tab', { name: '2. Risiko und Maßnahmen' })).toHaveAttribute('aria-selected', 'true')
  await expect(dsfa.getByRole('tab', { name: '2. Risiko und Maßnahmen' })).toBeFocused()
  await dsfa.getByRole('button', { name: 'Szenario hinzufügen' }).click()
  const scenario = dsfa.locator('[data-scenario="0"]')
  await scenario.getByLabel('Beschreibung des Risikos').fill('Bankverbindungen werden unbefugt eingesehen')
  await scenario.getByLabel('Schwere vor Maßnahmen').selectOption('3')
  await scenario.getByLabel('Eintrittswahrscheinlichkeit vor Maßnahmen').selectOption('3')
  await scenario.getByLabel('Rollenbasierte Zugriffskontrolle, Mehrfaktor-Anmeldung, geringste Rechte').check()
  await expect(scenario).toContainText('brutto 9 (hoch) → netto 3 (mittel)')
  await dsfa.getByLabel('An der Abschätzung Beteiligte (Rollen und Aufgaben)').fill('Referat Z 1, DSB')
  await dsfa.getByLabel('Umfang der Abschätzung (was einbezogen ist, was nicht und warum)').fill('Bewilligungsverfahren 2026')
  await dsfa.getByRole('button', { name: 'Entwurf speichern' }).click()
  await expect(dsfa.locator('.fa-dataprotection__live')).toContainText('Folgenabschätzung gespeichert')
  await shot(page, 'dataprotection-4-dsfa-risiko')

  await dsfa.getByRole('tab', { name: '3. Ergebnis und Freigabe' }).click()
  await expect(dsfa.getByTestId('dsfa-proposal')).toContainText('Freigabe mit Auflagen')
  await dsfa.getByTestId('dsfa-decision').getByLabel('Auflagen (eine je Zeile)').fill('Mehrfaktor-Anmeldung vor Start')
  await dsfa.getByRole('button', { name: 'Entscheidung speichern' }).click()
  await expect(dsfa.locator('.fa-dataprotection__live')).toContainText('Entscheidung gespeichert')
  await expect(dsfa.getByTestId('dsfa-four-eyes')).toBeVisible()
  await shot(page, 'dataprotection-5-dsfa-ergebnis')

  await page.getByTestId('theme-toggle').click()
  await dsfa.getByRole('button', { name: 'Öffnen: Vorhabenprüfung mit Stichprobe' }).click()
  await expect(dsfa.getByTestId('dsfa-head')).toContainText('freigegeben')
  await shot(page, 'dataprotection-6-dsfa-dunkel')
  expect(errors).toEqual([])
})
