import { fileURLToPath } from 'node:url'
import { expect, test } from '@playwright/test'

const SCREENSHOTS = process.env.FA_SCREENSHOTS
const SYNTHETIC = fileURLToPath(new URL('../../../packages/auditcore_documents/tests/fixtures/synthetic/', import.meta.url))

test('Dokumentvergleiche: hochladen, öffnen, importieren und löschen gegen auditcore_documents.web', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  page.on('console', (message) => {
    // Abgewiesene Uploads (415/422) meldet der Browser als Konsolenfehler der Ressource.
    if (message.type() === 'error' && !/41[35]|422/.test(message.text())) errors.push(message.text())
  })
  await page.goto('/#/dokumentvergleiche')
  const root = page.getByTestId('comparisons')
  await expect(root.getByRole('heading', { name: 'Dokumentvergleiche' })).toBeVisible()
  await expect(root.locator('.fa-comparisons-list__item')).toHaveCount(3)
  await expect(root).toContainText('DOCX, DOCM oder PDF, höchstens 5 MiB')

  await root.getByRole('button', { name: 'Vergleichen' }).click()
  await expect(root.locator('.fa-comparisons-form__problems')).toContainText('Die bisherige Fassung fehlt.')

  await root.getByTestId('comparisons-oldFile').setInputFiles(`${SYNTHETIC}tx_verschoben_alt.docx`)
  await root.getByTestId('comparisons-newFile').setInputFiles(`${SYNTHETIC}tx_verschoben_neu.docx`)
  await root.getByLabel('Titel (optional)').fill('Verschobene Absätze')
  await root.getByRole('checkbox', { name: 'Unverändert' }).check()
  await root.getByRole('button', { name: 'Vergleichen' }).click()
  await expect(root.getByRole('status')).toHaveText('„Verschobene Absätze“ wurde angelegt.')
  await expect(root.locator('.fa-comparisons-list__item').first()).toContainText('tx_verschoben_alt.docx → tx_verschoben_neu.docx')
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/documents-1-liste.png`, fullPage: true })

  await root.getByRole('button', { name: '„Verschobene Absätze“ öffnen' }).click()
  await expect(root.locator('.fa-synopsis')).toBeVisible()
  await expect(root.locator('.fa-synopsis-header__title')).toHaveText('Verschobene Absätze')
  await expect(page.getByTestId('comparisons-event')).toContainText('comparison-open')
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/documents-2-synopse.png`, fullPage: true })
  const exported = await page.request.get(`/api/synopsis/comparisons/${await firstId(root)}/export?format=json`)
  expect(exported.ok()).toBe(true)
  const result = await exported.text()
  await root.getByRole('button', { name: 'Zurück zur Übersicht' }).click()

  await root.getByTestId('comparisons-import').setInputFiles({ name: 'ergebnis.json', mimeType: 'application/json', buffer: Buffer.from(result) })
  await expect(root.getByRole('status')).toContainText('wurde importiert.')
  await expect(root.locator('.fa-comparisons-list__item')).toHaveCount(5)

  await root.getByRole('searchbox', { name: 'Vergleiche durchsuchen' }).fill('al_befehle')
  await expect(root.locator('.fa-comparisons-list__item')).toHaveCount(1)
  await root.getByRole('button', { name: /löschen$/ }).click()
  await page.getByRole('dialog', { name: 'Vergleich löschen?' }).getByRole('button', { name: 'Löschen' }).click()
  await expect(root.getByRole('status')).toContainText('wurde gelöscht.')
  await expect(root).toContainText('Kein Vergleich passt zur Suche.')

  await root.getByRole('searchbox', { name: 'Vergleiche durchsuchen' }).fill('')
  await root.getByTestId('comparisons-oldFile').setInputFiles({ name: 'notiz.docx', mimeType: 'application/octet-stream', buffer: Buffer.from('kein docx') })
  await root.getByTestId('comparisons-newFile').setInputFiles(`${SYNTHETIC}tx_block_neu.docx`)
  await root.getByRole('button', { name: 'Vergleichen' }).click()
  await expect(root.getByRole('alert')).toBeVisible()
  expect(errors).toEqual([])
})

async function firstId(root: import('@playwright/test').Locator): Promise<string> {
  return (await root.page().getByTestId('comparisons-event').textContent())?.match(/([0-9a-f]{32})/)?.[1] ?? ''
}
