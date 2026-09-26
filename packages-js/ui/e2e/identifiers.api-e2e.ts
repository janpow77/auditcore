import { expect, test } from '@playwright/test'

const SCREENSHOTS = process.env.FA_SCREENSHOTS

test('Kennung prüfen: Einzelprüfung mit Begründung und Stapelprüfung aus CSV', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text())
  })
  await page.goto('/#/kennung')
  await expect(page.getByTestId('ident-profile')).toHaveValue('strict')
  await page.getByTestId('ident-value').fill('DE89 3704 0044 0532 0130 01')
  await page.getByTestId('ident-check').click()
  await expect(page.getByTestId('ident-result')).toContainText('ungültig')
  await expect(page.getByTestId('ident-result')).toContainText('IBAN-Prüfziffer ist falsch')

  await page.getByTestId('ident-kind').selectOption('vat_id')
  await page.getByTestId('ident-value').fill('136695976')
  await page.getByTestId('ident-country').fill('DE')
  await page.getByTestId('ident-check').click()
  await expect(page.getByTestId('ident-result')).toContainText('DE136695976')
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/kennung-einzeln.png`, fullPage: true })

  const csv = 'Beleg;Art;Kennung\nB-1;IBAN;DE89 3704 0044 0532 0130 00\nB-2;USt-IdNr.;DE136695975\nB-3;LEI;7LTWFZYICNSX8D621K86\n'
  await page.getByTestId('ident-file').setInputFiles({ name: 'kennungen.csv', mimeType: 'text/csv', buffer: Buffer.from(csv) })
  await page.getByTestId('ident-batch-kind').selectOption('')
  await page.getByTestId('ident-col-kind').selectOption('1')
  await page.getByTestId('ident-col-value').selectOption('2')
  await page.getByTestId('ident-col-ref').selectOption('0')
  await page.getByTestId('ident-batch-run').click()
  await expect(page.locator('.fa-ident__summary')).toHaveText('3 Zeilen geprüft: 2 gültig, 1 ungültig, 0 ohne Wert, 0 nicht prüfbar')
  const download = page.waitForEvent('download')
  await page.getByTestId('ident-export').click()
  expect((await download).suggestedFilename()).toBe('kennungspruefung.csv')
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/kennung-stapel.png`, fullPage: true })
  expect(errors).toEqual([])
})
