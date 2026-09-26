import { fileURLToPath } from 'node:url'
import { expect, test } from '@playwright/test'

const SCREENSHOTS = process.env.FA_SCREENSHOTS
const INVENTORY = fileURLToPath(new URL('../../../packages/auditcore_documents/tests/fixtures/batch/bestand.csv', import.meta.url))

test('Bestandsprüfung: CSV einlesen, prüfen, filtern gegen auditcore_documents.web', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text())
  })
  await page.goto('/#/bestand')
  const root = page.getByTestId('batchchecks')
  await expect(root.getByRole('heading', { name: 'Bestand einlesen' })).toBeVisible()
  await root.getByTestId('batchchecks-file').setInputFiles(INVENTORY)
  await expect(root.getByTestId('batchchecks-source')).toHaveText('bestand.csv: 10 Zeile(n)')
  await root.getByTestId('batchchecks-total').fill('48.500,00')
  await root.getByRole('button', { name: 'Bestand prüfen' }).click()
  await expect(root.getByTestId('batchchecks-level')).toHaveText('Blockade')
  await expect(root.locator('[data-testid="batchchecks-rules"] tr[data-rule="C-09"]')).toContainText('1 Befund(e), 2 Beleg(e)')
  await root.getByTestId('batchchecks-filter').selectOption('ERG-01')
  await expect(root.locator('[data-testid="batchchecks-findings"] tbody tr')).toHaveCount(1)
  await expect(root.locator('[data-testid="batchchecks-findings"] tbody tr')).toContainText('RE-2026-0103 bis RE-2026-0105')
  await expect(page.getByText('Ereignis checks-completed:')).toBeVisible()
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/batchchecks-1-ergebnis.png`, fullPage: true })
  expect(errors).toEqual([])
})
