import { expect, test } from '@playwright/test'

const SCREENSHOTS = process.env.FA_SCREENSHOTS

test('Tabellenexport: Formatprofil, Vorschau mit Spaltenformaten, XLSX-Download', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text())
  })
  await page.goto('/#/tabellenexport')
  await expect(page.getByTestId('report-profile')).toHaveValue('flowlib-legacy-v1')
  await expect(page.getByTestId('report-tables')).toHaveText('2 Tabelle(n), 32 Zeilen')
  await page.getByTestId('report-preview').click()
  const formats = page.getByTestId('report-sheet-0').getByRole('table', { name: 'Spaltenformate' })
  await expect(formats).toContainText('#,##0.00 "EUR"')
  await expect(formats).toContainText('DD.MM.YYYY')
  await expect(page.getByTestId('report-sheet-0')).toContainText('Vorschau zeigt 20 von 30 Zeilen.')
  await expect(page.getByTestId('report-sheet-1')).toContainText('=SUMME(A1:A3) bleibt Text')
  await expect(page.getByTestId('report-workbook')).toContainText('Probelauf: Vorhabenliste.xlsx')
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/tabellenexport-vorschau.png`, fullPage: true })

  await page.getByTestId('report-profile').selectOption('plain-v1')
  await expect(page.getByTestId('report-stale')).toBeVisible()
  await page.getByTestId('report-filename').fill('Prüfliste 2026')
  const download = page.waitForEvent('download')
  await page.getByTestId('report-export').click()
  expect((await download).suggestedFilename()).toBe('Prüfliste 2026.xlsx')
  await expect(page.getByTestId('report-status')).toHaveText('Exportiert: Prüfliste 2026.xlsx')
  expect(errors).toEqual([])
})
