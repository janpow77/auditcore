import { expect, test } from '@playwright/test'

const SCREENSHOTS = process.env.FA_SCREENSHOTS

test('Berichtsvorlagen: Datenvertrag, Vorschau mit Textbausteinen, DOCX- und PDF-Download', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  // Die Vorschau steht in einem iframe mit sandbox="" (keine Skripte). Chromium meldet dort
  // abgewiesene Skripte der Testumgebung; genau das ist die gewollte Abschottung.
  const sandboxed = /^Blocked script execution in 'about:srcdoc' because the document's frame is sandboxed/
  page.on('console', (message) => {
    if (message.type() === 'error' && !sandboxed.test(message.text())) errors.push(message.text())
  })
  await page.goto('/#/berichtsvorlagen')
  await expect(page.getByTestId('template-select')).toHaveValue('pruefbericht')
  await expect(page.getByTestId('template-version')).toContainText('Version 1.0.0')
  await page.getByTestId('template-contract').locator('summary').click()
  await expect(page.getByTestId('template-contract')).toContainText('Art. 74 VO (EU) 2021/1060')
  await page.getByTestId('template-preview-button').click()
  const preview = page.getByTestId('template-preview')
  await expect(preview).toContainText('Daten erfüllen den Datenvertrag.')
  await expect(preview).toContainText('Verwendete Textbausteine: rechtsgrundlage, verwaltungsueberpruefung')
  // Abgeschottetes iframe ohne Skripte: Inhalt über srcdoc prüfen (Playwright darf dort nichts ausführen).
  const frame = page.locator('iframe[title="Vorschau des Berichts"]')
  await expect(frame).toHaveAttribute('sandbox', '')
  await expect(frame).toHaveAttribute('srcdoc', /<h3>Feststellung 2: Rechnung außerhalb des Förderzeitraums<\/h3>/)

  const docx = page.waitForEvent('download')
  await page.getByTestId('template-render').click()
  expect((await docx).suggestedFilename()).toBe('Prüfbericht.docx')
  await page.getByTestId('template-format').selectOption('pdf')
  const pdf = page.waitForEvent('download')
  await page.getByTestId('template-render').click()
  expect((await pdf).suggestedFilename()).toBe('Prüfbericht.pdf')
  await expect(page.getByTestId('template-status')).toHaveText('Erzeugt: Prüfbericht.pdf')
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/berichtsvorlagen-vorschau.png`, fullPage: true })
  expect(errors).toEqual([])
})
