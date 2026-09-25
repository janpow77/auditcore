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

test('Basisseite: Dialog öffnet modal, hält den Fokus und schließt mit Escape', async ({ page }) => {
  const errors = await openPage(page, 'basis')
  await expect(page.getByRole('heading', { name: 'Basiskomponenten' })).toBeVisible()
  await page.getByTestId('open-dialog').click()
  const dialog = page.getByRole('dialog', { name: 'Board-Einstellungen' })
  await expect(dialog).toBeVisible()
  await expect(page.getByRole('button', { name: 'Schließen' })).toBeFocused()
  await page.keyboard.press('Shift+Tab')
  await expect(dialog.getByRole('button', { name: 'Übernehmen' })).toBeFocused()
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/ui-dialog.png` })
  await page.keyboard.press('Escape')
  await expect(dialog).toBeHidden()
  await expect(page.getByTestId('open-dialog')).toBeFocused()
  expect(errors).toEqual([])
})

test('Tabelle: Sortierung per Tastatur, aria-sort und Sprachwechsel', async ({ page }) => {
  const errors = await openPage(page, 'tabelle')
  const header = page.getByRole('columnheader', { name: /Vorhaben/ })
  await page.getByRole('button', { name: 'Nach Vorhaben sortieren' }).focus()
  await page.keyboard.press('Enter')
  await expect(header).toHaveAttribute('aria-sort', 'ascending')
  await expect(page.locator('tbody tr').first()).toContainText('Breitbandausbau')
  await page.locator('tbody tr').nth(1).press('Enter')
  await expect(page.getByText('Ausgewählt: Energieeffizienz Mittelstand')).toBeVisible()
  await page.getByTestId('locale-toggle').click()
  await expect(page.getByRole('button', { name: 'Sort by Vorhaben' })).toBeVisible()
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/ui-tabelle.png` })
  expect(errors).toEqual([])
})

test('Dunkelmodus schaltet die Designtoken um', async ({ page }) => {
  const errors = await openPage(page, 'basis')
  const background = () => page.evaluate(() => getComputedStyle(document.body).backgroundColor)
  const light = await background()
  await page.getByTestId('theme-toggle').click()
  await expect(page.locator('html')).toHaveAttribute('data-fa-theme', /dark|light/)
  await page.waitForTimeout(400)
  const toggled = await background()
  expect(toggled).not.toBe(light)
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/ui-basis-dunkel.png` })
  expect(errors).toEqual([])
})

test('Web Component flowaudit-table rendert im Light DOM und sendet Ereignisse', async ({ page }) => {
  const errors = await openPage(page, 'web-components')
  const element = page.locator('flowaudit-table')
  await expect(element.locator('td').first()).toHaveText('Systemprüfung S03')
  expect(await element.evaluate((node) => node.shadowRoot)).toBeNull()
  await element.locator('tbody tr').nth(1).click()
  await expect(page.getByText('Ereignis row-click: Vorhabenprüfung VP-19')).toBeVisible()
  expect(errors).toEqual([])
})
