import { expect, test } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test.beforeEach(async ({ page }) => {
  await page.goto('/#/konto')
  await page.getByRole('button', { name: 'Persönliche Angaben', exact: true }).click()
})

test('Profil speichern und Navigation bei offenen Änderungen sperren', async ({ page }) => {
  await page.getByLabel('Anzeigename').fill('Alex Geändert')
  await expect(page.getByRole('button', { name: 'Corporate Design', exact: true })).toBeDisabled()
  await page.getByRole('button', { name: 'Änderungen speichern', exact: true }).click()
  await expect(page.getByRole('status')).toContainText('Änderungen gespeichert.')
  await page.getByRole('button', { name: 'Funktion und Kontakt', exact: true }).click()
  await page.getByRole('button', { name: 'Persönliche Angaben', exact: true }).click()
  await expect(page.getByLabel('Anzeigename')).toHaveValue('Alex Geändert')
})

test('Begrüßungsvorschau rendert keinen HTML-Code', async ({ page }) => {
  await page.getByRole('button', { name: 'Begrüßung', exact: true }).click()
  await page.getByLabel('Begrüßungstext').fill('Hallo {{display_name}} <img src=x onerror=alert(1)>')
  await expect(page.locator('.fa-account__welcome')).toContainText('Hallo Alex Beispiel <img')
  await expect(page.locator('.fa-account__welcome img')).toHaveCount(0)
})

test('Profil ist ohne horizontales Scrollen mobil bedienbar', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  const width = await page.locator('.fa-account').evaluate((element) => ({ scroll: element.scrollWidth, client: element.clientWidth }))
  expect(width.scroll).toBeLessThanOrEqual(width.client)
  await expect(page.getByLabel('Anzeigename')).toBeVisible()
})

test('Profil und Corporate Design erfüllen die geprüften Axe-Regeln in hell und dunkel', async ({ page }) => {
  for (const mode of ['light', 'dark']) {
    await page.evaluate((value) => document.documentElement.setAttribute('data-fa-theme', value), mode)
    for (const label of ['Persönliche Angaben', 'Corporate Design']) {
      await page.getByRole('button', { name: label, exact: true }).click()
      const result = await new AxeBuilder({ page }).include('.fa-account').analyze()
      expect(result.violations).toEqual([])
    }
  }
})

test('Webcam wird nur auf Anforderung geöffnet und nach Aufnahme geschlossen', async ({ page, context }) => {
  await context.grantPermissions(['camera'])
  await page.getByRole('button', { name: 'Webcam aktivieren', exact: true }).click()
  await expect.poll(() => page.locator('.fa-account video').evaluate((video: HTMLVideoElement) => video.videoWidth)).toBeGreaterThan(0)
  await page.getByRole('button', { name: 'Foto aufnehmen', exact: true }).click()
  await expect(page.locator('.fa-account video')).toHaveCount(0)
  await expect(page.getByAltText('Profilbild', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Änderungen verwerfen', exact: true }).click()
  await expect(page.getByAltText('Profilbild', { exact: true })).toHaveCount(0)
})
