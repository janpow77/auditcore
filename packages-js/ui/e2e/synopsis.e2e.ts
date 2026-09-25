import { expect, test, type Page } from '@playwright/test'

const SCREENSHOTS = process.env.FA_SCREENSHOTS

async function openSynopsis(page: Page): Promise<string[]> {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text())
  })
  await page.goto('/#/synopse')
  await expect(page.getByRole('heading', { name: 'Synopse / Versionsvergleich', level: 1 })).toBeVisible()
  return errors
}

async function shot(page: Page, name: string): Promise<void> {
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/${name}.png`, fullPage: true })
}

test('Synopse: nebeneinander mit Wortmarkierung, Navigation per Taste', async ({ page }) => {
  const errors = await openSynopsis(page)
  const region = page.getByRole('region', { name: 'Förderrichtlinie Mittelstand – Fassung 2025 und 2026' })
  await expect(region).toBeVisible()
  const first = region.locator('article').first()
  await expect(first.getByRole('heading', { level: 4, name: 'Bisherige Fassung' })).toBeVisible()
  await expect(first.locator('ins')).toContainText('Unternehmen in Hessen.')
  await expect(first.locator('del')).toContainText('Unternehmen.')
  await shot(page, 'synopse-nebeneinander')

  const status = region.getByRole('status')
  await expect(status).toHaveText('8 Änderungen in dieser Ansicht')
  await region.getByRole('button', { name: 'Nächste Änderung' }).click()
  await expect(status).toHaveText('Änderung 1 von 8')
  await page.keyboard.press('n')
  await expect(status).toHaveText('Änderung 2 von 8')
  await expect(page.locator('article[aria-current="true"]')).toBeFocused()
  await page.keyboard.press('p')
  await expect(status).toHaveText('Änderung 1 von 8')
  expect(errors).toEqual([])
})

test('Synopse: Inline-Ansicht, Filter, Suche und Export', async ({ page }) => {
  const errors = await openSynopsis(page)
  await page.getByRole('button', { name: 'Im Text' }).click()
  await expect(page.locator('.fa-synopsis-row__inline').first()).toBeVisible()
  await page.getByRole('checkbox', { name: 'Unverändert' }).check()
  await expect(page.locator('article')).toHaveCount(11)
  await page.getByRole('searchbox', { name: 'Im Vergleich suchen' }).fill('Pauschalsatz')
  await expect(page.locator('article')).toHaveCount(1)
  await shot(page, 'synopse-inline-filter')
  const download = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Markdown' }).click()
  expect((await download).suggestedFilename()).toBe('Förderrichtlinie_Mittelstand_Fassung_2025_und_2026.md')
  await expect(page.getByTestId('event-log')).toContainText('Export markdown')
  expect(errors).toEqual([])
})

test('Synopse: Artikelgesetz mit Änderungsbefehlen und konsolidierter Fassung', async ({ page }) => {
  const errors = await openSynopsis(page)
  await page.getByTestId('sample-article').check()
  await expect(page.getByRole('heading', { level: 4, name: 'Geltende Fassung' }).first()).toBeVisible()
  await expect(page.getByText('Änderungsbefehle erkannt').first()).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Offene Änderungsbefehle' })).toBeVisible()
  await page.getByText('Konsolidierte Arbeitsfassung').click()
  await expect(page.locator('details[open] dd').first()).toBeVisible()
  await shot(page, 'synopse-artikelgesetz')
  expect(errors).toEqual([])
})

test('Synopse: Vorschau bearbeiten, Dunkelmodus und Web Component', async ({ page }) => {
  const errors = await openSynopsis(page)
  await page.getByTestId('sample-checklist').check()
  await page.getByTestId('editable').check()
  await page.getByRole('checkbox', { name: 'In Ausgabe übernehmen' }).first().uncheck()
  await expect(page.getByTestId('event-log')).toContainText('"selected":false')
  await expect(page.getByText('4 von 6 Zeilen für die Ausgabe ausgewählt')).toBeVisible()
  await page.getByTestId('theme-toggle').click()
  await expect(page.locator('html')).toHaveAttribute('data-fa-theme', /dark|light/)
  await shot(page, 'synopse-checkliste-dunkel')
  await page.getByTestId('as-element').check()
  const element = page.locator('flowaudit-synopsis')
  await expect(element.locator('h2')).toHaveText('Prüfcheckliste Vorhabenprüfung v5 und v6')
  expect(await element.evaluate((node) => node.shadowRoot)).toBeNull()
  expect(errors).toEqual([])
})
