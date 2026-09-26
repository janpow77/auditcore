import { fileURLToPath } from 'node:url'
import { expect, test } from '@playwright/test'

const SCREENSHOTS = process.env.FA_SCREENSHOTS
const DONUT = fileURLToPath(new URL('../../../packages/auditcore_documents/tests/fixtures/donut/', import.meta.url))

test('Belegerkennung: hochladen, Donut-Profil, Konfidenz und Befunde gegen auditcore_documents.web', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text())
  })
  await page.goto('/#/belegerkennung')
  const root = page.getByTestId('extraction')
  await expect(root.getByRole('heading', { name: 'Dokument hochladen' })).toBeVisible()
  await expect(root).toContainText('höchstens 5 MiB')

  await root.getByRole('button', { name: 'Erkennen' }).click()
  await expect(root.getByRole('alert')).toHaveText('Bitte eine Datei auswählen.')

  await root.getByTestId('extraction-file').setInputFiles(`${DONUT}train-000032.png`)
  await root.getByRole('button', { name: 'Erkennen' }).click()
  await expect(root.getByTestId('extraction-status')).toHaveText('Ohne Auffälligkeiten')
  await expect(root.locator('[data-field="invoice_number"]')).toContainText('RG-2025-0028')
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/extraction-1-empfohlen.png`, fullPage: true })

  await root.getByTestId('extraction-file').setInputFiles(`${DONUT}train-000003.png`)
  await root.getByTestId('extraction-profile').selectOption('auditcore.pipeline.donut')
  await expect(root.getByTestId('extraction-experimental')).toBeVisible()
  await root.getByRole('button', { name: 'Erkennen' }).click()
  await expect(root.getByTestId('extraction-status')).toHaveText('Prüfung erforderlich')
  await expect(root.locator('[data-field="total"]')).toContainText('verworfen (Plausibilität)')
  await expect(root.locator('[data-testid="extraction-findings"] tbody tr').first()).toContainText('Plausibilität der Donut-Werte')
  await expect(page.getByText('Ereignis extraction-completed: review_needed')).toBeVisible()
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/extraction-2-donut.png`, fullPage: true })
  expect(errors).toEqual([])
})
