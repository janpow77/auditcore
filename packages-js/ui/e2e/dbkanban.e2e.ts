import { expect, test, type Page } from '@playwright/test'

const SHOTS = process.env.FA_SCREENSHOTS

async function open(page: Page): Promise<string[]> {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text())
  })
  await page.goto('/#/datenbank-kanban')
  await expect(page.getByRole('heading', { name: 'Kanban-Ansicht' })).toBeVisible()
  return errors
}

const cards = (page: Page, column: string) => page.locator(`[data-column="${column}"] .fa-db-kanban-card`)

test('Datenbankansicht: Ziehen, Tastatur, Gruppierung, Anlegen und Nur-Lesen', async ({ page }) => {
  const errors = await open(page)
  await expect(page.locator('.fa-db-kanban-column')).toHaveCount(5)
  await expect(cards(page, '')).toHaveText([/Strukturwandel Revier/])
  if (SHOTS) await page.screenshot({ path: `${SHOTS}/dbkanban-1-status.png`, fullPage: true })

  await page.locator('[data-card-id="v1"]').dragTo(page.locator('[data-column="in Prüfung"]'))
  await expect(cards(page, 'in Prüfung')).toHaveCount(2)
  await expect(page.getByRole('status')).toHaveText('„Breitbandausbau Nord“ nach „in Prüfung“ verschoben.')
  await expect(page.getByTestId('dbk-event')).toContainText('"value":"in Prüfung"')

  await page.locator('[data-card-id="v4"]').focus()
  await page.keyboard.press('Control+ArrowRight')
  await expect(cards(page, 'offen')).toHaveText([/Strukturwandel Revier/])
  await expect(page.locator('[data-card-id="v4"]')).toBeFocused()
  await expect(page.locator('[data-column=""]')).toHaveCount(0)

  await page.getByRole('button', { name: 'Eintrag in „Feststellungen“ hinzufügen' }).click()
  await expect(cards(page, 'Feststellungen')).toHaveCount(2)

  await page.getByLabel('Gruppieren nach').selectOption({ label: 'Fonds' })
  await expect(page.getByTestId('dbk-group')).toHaveText('Gruppierung: fonds')
  await expect(page.locator('.fa-db-kanban-column__name')).toHaveText(['Ohne Wert', 'EFRE', 'ESF+', 'JTF'])
  await page.getByRole('searchbox', { name: 'Einträge durchsuchen' }).fill('efre')
  await expect(page.locator('.fa-db-kanban-card')).toHaveCount(3)
  if (SHOTS) await page.screenshot({ path: `${SHOTS}/dbkanban-2-fonds.png`, fullPage: true })

  await page.getByTestId('dbk-editable').uncheck()
  await expect(page.getByText('Nur Lesezugriff')).toBeVisible()
  await expect(page.locator('[draggable="true"]')).toHaveCount(0)
  expect(errors).toEqual([])
})
