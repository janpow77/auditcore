import { expect, test } from '@playwright/test'

const SCREENSHOTS = process.env.FA_SCREENSHOTS

test('Hochrechnung: MUS-Standardansatz, TER mit Obergrenze, RER getrennt, CSV-Export', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text())
  })
  await page.goto('/#/hochrechnung')
  await expect(page.getByTestId('extrapolation-units').locator('tbody tr')).toHaveCount(5)
  await page.getByTestId('extrapolation-method').selectOption('mus.standard')
  await page.getByTestId('extrapolation-confidence').selectOption('0.9')
  await page.getByTestId('extrapolation-evaluate').click()
  await expect(page.getByTestId('extrapolation-conclusion')).toHaveText('Nicht schlüssig – weitere Prüfungshandlungen')
  await expect(page.getByTestId('extrapolation-metrics')).toContainText('1,60 %')
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/hochrechnung-ter.png`, fullPage: true })

  await page.getByTestId('extrapolation-rer-corrections').fill('5.000')
  await page.getByTestId('extrapolation-residual').click()
  await expect(page.getByTestId('extrapolation-rer')).toContainText('Restfehlerquote (RER)')
  await expect(page.getByTestId('extrapolation-rer-rows').locator('tbody tr')).toHaveCount(12)
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/hochrechnung-rer.png`, fullPage: true })

  const download = page.waitForEvent('download')
  await page.getByTestId('extrapolation-export-csv').click()
  expect((await download).suggestedFilename()).toMatch(/^hochrechnung-mus\.standard-[0-9a-f]{12}\.csv$/)
  expect(errors).toEqual([])
})
