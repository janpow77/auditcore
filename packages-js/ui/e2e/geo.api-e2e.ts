import { expect, test, type Page } from '@playwright/test'

const SCREENSHOTS = process.env.FA_SCREENSHOTS

async function openGeo(page: Page): Promise<string[]> {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text())
  })
  await page.goto('/#/geo-karte')
  await expect(page.getByTestId('geo-earth-model')).toHaveValue('kugel.r1_6371008_8m')
  await expect(page.locator('.fa-geo__point')).toHaveCount(24)
  return errors
}

async function setReference(page: Page, lat: string, lon: string): Promise<void> {
  await page.getByTestId('geo-lat').fill(lat)
  await page.getByTestId('geo-lon').fill(lon)
  await page.getByTestId('geo-apply').click()
}

test('Geo: Karte mit synthetischen Kacheln, Kartenklick, UTM und Umkreissuche', async ({ page }) => {
  const errors = await openGeo(page)
  await expect(page.getByTestId('geo-attribution')).toContainText('Synthetische Demokacheln')
  await expect(page.locator('.leaflet-control-attribution')).toContainText('Synthetische Demokacheln')
  await expect(page.locator('.leaflet-tile-loaded').first()).toBeVisible()
  await expect(page.locator('path.fa-geo__area')).toHaveCount(2)

  await page.getByTestId('geo-map').click({ position: { x: 200, y: 160 } })
  await expect(page.getByTestId('geo-utm')).toContainText('Zone 32N')
  await setReference(page, '50,33', '9,01')
  await expect(page.getByTestId('geo-reference')).toContainText('50,330000, 9,010000')
  await expect(page.getByTestId('geo-utm')).toContainText('EPSG:25832')

  await page.getByTestId('geo-radius').fill('8000')
  await page.getByTestId('geo-radius-run').click()
  const result = page.getByTestId('geo-radius-result')
  await expect(result).toContainText('von 24 Punkten im Umkreis von 8,00 km')
  const distances = await result.locator('tbody td.fa-geo__num').allInnerTexts()
  expect(distances.length).toBeGreaterThan(0)
  await expect(page.locator('path.fa-geo__point--hit')).toHaveCount(distances.length)
  await expect(page.locator('path.fa-geo__radius')).toHaveCount(1)
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/geo-umkreis.png`, fullPage: true })
  expect(errors).toEqual([])
})

test('Geo: Punkt in Fläche mit Randfall, Loch und Toleranz', async ({ page }) => {
  const errors = await openGeo(page)
  await page.getByTestId('geo-locate-area').selectOption('demo-rechteck')
  await setReference(page, '50,3', '8,97')
  await page.getByTestId('geo-locate-run').click()
  await expect(page.getByTestId('geo-position')).toHaveText('auf dem Rand')
  await expect(page.getByTestId('geo-boundary-case')).toContainText('exakt auf dem Rand')
  await expect(page.getByTestId('geo-locate-result')).toContainText('Ergebnis: in der Fläche')
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/geo-randfall.png`, fullPage: true })

  await page.getByTestId('geo-boundary-inside').uncheck()
  await page.getByTestId('geo-locate-run').click()
  await expect(page.getByTestId('geo-locate-result')).toContainText('Ergebnis: nicht in der Fläche')

  await setReference(page, '50,315', '8,975')
  await page.getByTestId('geo-locate-run').click()
  await expect(page.getByTestId('geo-position')).toHaveText('außen')
  await expect(page.getByTestId('geo-locate-result')).toContainText('Abstand zum Rand')

  await setReference(page, '50,30004', '8,97')
  await page.getByTestId('geo-tolerance').fill('10')
  await page.getByTestId('geo-boundary-inside').check()
  await page.getByTestId('geo-locate-run').click()
  await expect(page.getByTestId('geo-boundary-case')).toContainText('innerhalb der Toleranz von 10 m')
  expect(errors).toEqual([])
})

test('Geo: Douglas-Peucker mit Toleranzregler und GeoPackage aus Datei und Serverquelle', async ({ page }) => {
  const errors = await openGeo(page)
  await page.getByTestId('geo-simplify-area').selectOption('demo-auenlandschaft')
  await page.getByTestId('geo-simplify-run').click()
  await expect(page.getByTestId('geo-simplify-result')).toContainText('241 →')
  const slider = page.getByTestId('geo-simplify-tolerance')
  await slider.focus()
  await page.keyboard.press('ArrowRight')
  await page.keyboard.press('ArrowRight')
  await page.getByTestId('geo-simplify-run').click()
  await expect(slider).toHaveAttribute('aria-valuetext', '50 m')
  await expect(page.locator('path.fa-geo__simplified')).toHaveCount(1)
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/geo-vereinfachung.png`, fullPage: true })

  const file = await page.request.get('/api/geo-demo/schutzgebiete-demo.gpkg')
  expect(file.ok()).toBe(true)
  await page.getByTestId('geo-gpkg-file').setInputFiles({ name: 'schutzgebiete-demo.gpkg', mimeType: 'application/geopackage+sqlite3', buffer: await file.body() })
  await expect(page.getByTestId('geo-gpkg-result')).toContainText('2 Flächen aus Tabelle „schutzgebiete“ (srs_id 4326)')
  await expect(page.locator('path.fa-geo__area')).toHaveCount(4)

  await page.getByTestId('geo-gpkg-source').selectOption('landschaftsschutz-demo')
  await page.getByTestId('geo-gpkg-load').click()
  await expect(page.getByTestId('geo-gpkg-result')).toContainText('srs_id 25832')
  await expect(page.getByTestId('geo-gpkg-result')).toContainText('aus UTM umgerechnet')
  await expect(page.locator('path.fa-geo__area')).toHaveCount(5)
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/geo-geopackage.png`, fullPage: true })

  await page.emulateMedia({ colorScheme: 'dark' })
  if (SCREENSHOTS) await page.screenshot({ path: `${SCREENSHOTS}/geo-dunkel.png`, fullPage: true })
  expect(errors).toEqual([])
})
