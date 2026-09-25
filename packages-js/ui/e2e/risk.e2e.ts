import { expect, test, type Page } from '@playwright/test'

const SCREENSHOTS = process.env.FA_SCREENSHOTS

async function openRisk(page: Page): Promise<string[]> {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text())
  })
  await page.setViewportSize({ width: 1440, height: 1100 })
  await page.goto('/#/risiko-merkmale')
  await expect(page.getByRole('heading', { name: 'Red Flags der Belegliste' })).toBeVisible()
  return errors
}

test('Risiko-Merkmale: Verteilung mit unbestimmten Belegen, Karte per Tastatur', async ({ page }) => {
  const errors = await openRisk(page)
  await expect(page.getByTestId('risk-profile')).toContainText('riskanalysis.year_bound')
  await expect(page.getByText('Nettobetrag fehlt in der Quelle (3)')).toBeVisible()
  await expect(page.locator('.fa-risk-table tbody tr')).toHaveCount(10)
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/risk-uebersicht.png`, fullPage: true })

  const row = page.locator('.fa-risk-table tbody tr', { hasText: 'B-012' })
  await row.focus()
  await page.keyboard.press('Enter')
  const detail = page.getByTestId('risk-detail')
  await expect(detail.getByRole('heading', { name: 'Datensatz B-012' })).toBeVisible()
  const undetermined = detail.locator('.fa-risk-card--undetermined[data-code="RF08"]')
  await expect(undetermined).toContainText('Nettobetrag fehlt in der Quelle')
  await expect(undetermined.getByRole('row', { name: /nettobetrag/ })).toContainText('leer')
  await expect(undetermined).toContainText('Betrag größer als')
  await expect(page.getByText('Ereignis record-select: Datensatz 12')).toBeVisible()
  if (SCREENSHOTS) await detail.screenshot({ path: `${SCREENSHOTS}/risk-karte-unbestimmt.png` })
  expect(errors).toEqual([])
})

test('Risiko-Merkmale: Filter nach Code und Zustand, Profilansicht', async ({ page }) => {
  const errors = await openRisk(page)
  await page.getByLabel('Merkmal', { exact: true }).selectOption('RF02')
  await page.getByLabel('Zustand').selectOption('undetermined')
  await expect(page.locator('.fa-risk-table tbody tr')).toHaveCount(3)
  await expect(page.getByText('3 von 12 Datensätzen')).toBeVisible()
  await page.getByText('Profil und Eingabefelder').click()
  const fields = page.getByRole('table', { name: 'Eingabefelder' })
  await expect(fields.getByRole('row', { name: /nettobetrag/ })).toContainText('Nettobetrag fehlt in der Quelle')
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/risk-filter-profil.png`, fullPage: true })
  expect(errors).toEqual([])
})

test('Risiko-Merkmale: übersprungene Regeln (FlowStat) im Dunkelmodus', async ({ page }) => {
  const errors = await openRisk(page)
  await page.getByTestId('sample-flowstat').check()
  await expect(page.getByText('5 Regeln übersprungen')).toBeVisible()
  await expect(page.getByText('Spalten fehlen: zahlungsdatum').first()).toBeVisible()
  await expect(page.getByText('Befunde über alle Datensätze')).toBeVisible()
  await page.getByTestId('theme-toggle').click()
  await page.waitForTimeout(300)
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/risk-flowstat-dunkel.png`, fullPage: true })
  expect(errors).toEqual([])
})
