import { expect, test, type Page } from '@playwright/test'

const SCREENSHOTS = process.env.FA_SCREENSHOTS

async function openPage(page: Page, id: string): Promise<string[]> {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text())
  })
  await page.goto(`/#/${id}`)
  return errors
}

test('Stichprobe: Umfang mit Herleitung, reproduzierbare Auswahl und CSV-Export', async ({ page }) => {
  const errors = await openPage(page, 'stichprobe')
  await expect(page.getByTestId('sampling-method')).toHaveValue('portal.mus_poisson')
  await page.getByTestId('sampling-population_value').fill('475.478,94')
  await page.getByTestId('sampling-materiality').fill('50.000')
  await page.getByTestId('sampling-expected_error_rate').fill('0,5')
  await page.getByTestId('sampling-confidence').selectOption('0.95')
  await page.getByTestId('sampling-calculate').click()
  await expect(page.getByTestId('sampling-size')).toHaveText('n = 30')
  await expect(page.getByRole('table', { name: 'Herleitung' })).toContainText('Präzision')
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/stichprobe-umfang.png`, fullPage: true })

  await page.getByTestId('sampling-allocation').selectOption('proportional')
  await page.getByTestId('sampling-seed').fill('20260925')
  await page.getByTestId('sampling-draw').click()
  await expect(page.getByTestId('sampling-seed-used')).toContainText('Seed 20260925')
  const first = await page.getByTestId('sampling-rows').locator('tbody').innerText()
  await expect(page.getByTestId('sampling-strata')).toContainText('Los 2 – Bau')
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/stichprobe-auswahl.png`, fullPage: true })

  await page.getByTestId('sampling-draw').click()
  await expect(page.getByTestId('sampling-seed-used')).toContainText('Seed 20260925')
  expect(await page.getByTestId('sampling-rows').locator('tbody').innerText()).toBe(first)

  const download = page.waitForEvent('download')
  await page.getByTestId('sampling-export-csv').click()
  expect((await download).suggestedFilename()).toBe('stichprobe-mus-seed-20260925.csv')

  await page.getByTestId('sampling-redraw').click()
  await expect(page.getByTestId('sampling-seed-used')).toContainText('vom Server erzeugt')
  expect(errors).toEqual([])
})

test('Benford: Kennzahlen, Stufe und hervorgehobene Ziffern im eigenen SVG', async ({ page }) => {
  const errors = await openPage(page, 'benford')
  await expect(page.getByTestId('benford-count')).toContainText('1.500 Werte')
  await page.getByTestId('benford-analyse').click()
  await expect(page.getByTestId('benford-level')).toBeVisible()
  await expect(page.getByTestId('benford-exceeding')).toContainText('4')
  await expect(page.locator('.fa-benford__bar--exceeds[data-digit="4"]')).toHaveCount(1)
  await expect(page.getByRole('img', { name: /Erste Ziffer/ })).toBeVisible()
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/benford-erste-ziffer.png`, fullPage: true })

  await page.getByTestId('benford-test').selectOption('first_two')
  await page.getByTestId('benford-analyse').click()
  await expect(page.getByRole('alert')).toContainText('Regel für Werte')
  await page.getByTestId('benford-short-exclude').check()
  await page.getByTestId('benford-analyse').click()
  await expect(page.locator('.fa-benford__bar')).toHaveCount(90)
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/benford-erste-zwei-ziffern.png`, fullPage: true })

  await page.getByTestId('theme-toggle').click()
  await page.getByTestId('benford-test').selectOption('second')
  await page.getByTestId('benford-analyse').click()
  await expect(page.locator('.fa-benford__bar')).toHaveCount(10)
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/benford-zweite-ziffer-dunkel.png`, fullPage: true })
  expect(errors).toEqual([])
})
