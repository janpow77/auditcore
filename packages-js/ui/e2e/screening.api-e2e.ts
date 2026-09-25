import { expect, test, type Page } from '@playwright/test'

const SCREENSHOTS = process.env.FA_SCREENSHOTS

async function openPage(page: Page): Promise<string[]> {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  page.on('console', (message) => {
    // Abgelehnte Vier-Augen-Anfragen (409) meldet der Browser als Konsolenfehler der Ressource.
    if (message.type() === 'error' && !message.text().includes('409')) errors.push(message.text())
  })
  await page.goto('/#/screening')
  return errors
}

test('Screening: Prüflauf öffnen, Treffer vergleichen, verwerfen und Vier-Augen-Prinzip', async ({ page }) => {
  const errors = await openPage(page)
  const review = page.getByTestId('screening-review')
  await expect(review.getByRole('heading', { name: 'Screening-Trefferprüfung' })).toBeVisible()
  await review.getByRole('button', { name: /Vorgang 2026\/0815/ }).click()
  await expect(review.locator('.fa-screening__subject')).toHaveCount(3)
  await expect(review.locator('.fa-screening__cmp')).toContainText('Maximilian Beispielmann')
  await expect(review.locator('.fa-screening__steps')).toBeVisible()
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/screening-1-vergleich.png`, fullPage: true })

  // Ersten Treffer bestätigen: vorgeschriebene Zweitprüfung.
  await review.getByRole('button', { name: 'Treffer bestätigen' }).click()
  await expect(review.getByText('Für diese Entscheidung ist die Zweitprüfung vorgeschrieben.')).toBeVisible()
  await review.locator('[aria-labelledby="fa-screening-decision-title"] textarea').fill('Geburtsdatum und Alias stimmen überein.')
  await review.getByRole('button', { name: 'Entscheidung speichern' }).click()
  await expect(review.locator('#fa-screening-decision-title')).toContainText('wartet auf Zweitprüfung')

  // Dieselbe Person darf nicht zweitprüfen.
  await review.locator('[aria-labelledby="fa-screening-decision-title"] textarea').fill('Selbst geprüft.')
  await review.getByRole('button', { name: 'Zustimmen' }).click()
  await expect(review.getByRole('alert')).toBeVisible()
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/screening-2-zweitpruefung.png`, fullPage: true })

  // Andere Person stimmt zu.
  await page.getByTestId('screening-actor').selectOption('pruefer-b')
  const second = page.getByTestId('screening-review')
  await second.getByRole('button', { name: /Vorgang 2026\/0815/ }).click()
  await second.locator('[aria-labelledby="fa-screening-decision-title"] textarea').fill('Nachvollzogen, Identität belegt.')
  await second.getByRole('button', { name: 'Zustimmen' }).click()
  await expect(second.locator('#fa-screening-decision-title')).toContainText('bestätigt')
  await expect(second.locator('.fa-screening__log')).toContainText('Prüfer B. Muster')
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/screening-3-bestaetigt.png`, fullPage: true })

  await page.getByTestId('theme-toggle').click()
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/screening-4-dunkel.png`, fullPage: true })
  expect(errors).toEqual([])
})
