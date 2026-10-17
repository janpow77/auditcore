/**
 * Befunde der Abnahme des Einbaus: Berichtsdruck auf einer Seite (auch im
 * installierten Chrome), Menü und Bericht bei 390 px, Fokus nach der Blattwahl,
 * Stand „geändert“ nur bei echten Änderungen.
 */
import { writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { chromium, expect, test, type Browser, type Page } from '@playwright/test'
import { locateVariant, pick } from './pick'

const ALL = '/?entwurf=0'
const CHANGE_METHOD = 'Verfahren wechseln'
const pagesOf = (pdf: Buffer): number => Number(/\/Count (\d+)/.exec(pdf.toString('latin1'))?.[1] ?? Number.NaN)

async function openReport(page: Page, sample: boolean, base = ''): Promise<void> {
  await page.goto(`${base}${ALL}`)
  await pick(page, '03_MUS_1Z')
  if (sample) {
    await page.getByRole('button', { name: 'Arbeitsstand' }).click()
    await page.getByRole('menuitem', { name: 'Beispielwerte laden' }).click()
  }
  await page.getByRole('button', { name: 'Bericht' }).click()
  await expect(page.locator('.fa-st__report-page')).toBeVisible()
}

/** Seitenzahlen des Berichtsdrucks: leeres Formular, Beispielwerte, lange Freitexte. */
async function printedPages(page: Page, base = ''): Promise<{ empty: number; sample: number; background: number; long: number }> {
  await openReport(page, false, base)
  const empty = pagesOf(await page.pdf({ format: 'A4', preferCSSPageSize: true }))
  await openReport(page, true, base)
  const sample = pagesOf(await page.pdf({ format: 'A4', preferCSSPageSize: true }))
  const background = pagesOf(await page.pdf({ format: 'A4', preferCSSPageSize: true, printBackground: true }))
  // Lange Freitexte: Der Bericht läuft auf eine zweite Seite über, die Tabellen bleiben je für sich zusammen.
  const text = Array.from({ length: 60 }, (_, index) => `Zeile ${index + 1} der Erläuterung zu den geprüften Vorhaben.`).join('\n')
  for (const area of await page.locator('.fa-st__report-page textarea').all()) await area.fill(text)
  const longPdf = await page.pdf({ format: 'A4', preferCSSPageSize: true, printBackground: true })
  if (process.env.SAMPLING_SCREENSHOTS) writeFileSync(join(process.env.SAMPLING_SCREENSHOTS, `bericht_lang_${base ? 'chrome' : 'chromium'}.pdf`), longPdf)
  const long = pagesOf(longPdf)
  return { empty, sample, background, long }
}

test('Berichtsdruck: leeres Formular und Beispielwerte auf einer A4-Seite, lange Texte laufen sauber über', async ({ page }) => {
  const pages = await printedPages(page)
  expect(pages).toMatchObject({ empty: 1, sample: 1, background: 1 })
  expect(pages.long).toBeGreaterThan(1)
  // Kopf- und Summenzeile sind im Druck gewöhnliche Zeilengruppen, jede Tabelle bleibt zusammen; der Hintergrund des Blatts ist weiß.
  await openReport(page, true)
  await page.emulateMedia({ media: 'print' })
  const styles = await page.evaluate(() => {
    const style = (selector: string, property: string): string => getComputedStyle(document.querySelector(selector) as Element).getPropertyValue(property)
    return { head: style('.fa-st__report-table thead', 'display'), foot: style('.fa-st__report-table tfoot', 'display'), table: style('.fa-st__report-table', 'break-inside'), html: style('html', 'background-color'), body: style('body', 'background-color'), page: style('.fa-st__report-page', 'background-color') }
  })
  expect(styles).toEqual({ head: 'table-row-group', foot: 'table-row-group', table: 'avoid', html: 'rgb(255, 255, 255)', body: 'rgb(255, 255, 255)', page: 'rgb(255, 255, 255)' })
})

test('Berichtsdruck im installierten Chrome: ebenfalls eine Seite (dort schob die Summenzeile früher auf Seite 2)', async ({ baseURL }) => {
  let browser: Browser | null = null
  try {
    browser = await chromium.launch({ channel: 'chrome' })
  } catch {
    test.skip(true, 'Google Chrome ist auf diesem Rechner nicht installiert')
  }
  if (!browser) return
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, locale: 'de-DE' })
    const pages = await printedPages(page, baseURL ?? '')
    expect(pages).toMatchObject({ empty: 1, sample: 1, background: 1 })
    expect(pages.long).toBeGreaterThan(1)
  } finally {
    await browser.close()
  }
})

test('390 px: Das Menü „Arbeitsstand“ bleibt im Bild, die Kopfzeile ist verdichtet', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto(ALL)
  await pick(page, '03_MUS_1Z')
  await page.getByRole('button', { name: 'Arbeitsstand' }).click()
  const box = await page.getByRole('menu').boundingBox()
  expect(box).not.toBeNull()
  expect(box!.x).toBeGreaterThanOrEqual(0)
  expect(box!.x + box!.width).toBeLessThanOrEqual(390)
  for (const item of await page.getByRole('menuitem').all()) await expect(item).toBeInViewport()
  if (process.env.SAMPLING_SCREENSHOTS) await page.screenshot({ path: join(process.env.SAMPLING_SCREENSHOTS, '41_menue_390.png') })
  await page.keyboard.press('Escape')
  const bar = await page.locator('.fa-st__bar').evaluate((element) => ({ height: element.getBoundingClientRect().height, position: getComputedStyle(element).position }))
  expect(bar.position).toBe('static')
  expect(bar.height).toBeLessThan(170)
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true)
})

test('390 px: Bericht am Bildschirm – Tabellen mit Mindestbreite in eigenem, per Tastatur erreichbarem Rollrahmen', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await openReport(page, true)
  // Die Seite selbst rollt nicht waagerecht.
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true)
  if (process.env.SAMPLING_SCREENSHOTS) await page.screenshot({ path: join(process.env.SAMPLING_SCREENSHOTS, '40_bericht_390.png'), fullPage: true })
  const frames = page.locator('[data-report-scroll]')
  expect(await frames.count()).toBeGreaterThanOrEqual(4)
  // Die Kennzahlentabellen passen ohne Rollen: Ihre Werte stehen im Bild.
  for (const value of await page.locator('.fa-st__report-table--figures td.fa-st__report-num').all()) expect((await value.boundingBox())!.x + (await value.boundingBox())!.width).toBeLessThanOrEqual(390)
  const measured = await frames.evaluateAll((elements) =>
    elements.map((element) => {
      const heads = [...element.querySelectorAll('thead th')].map((cell) => cell.getBoundingClientRect().height)
      const inputs = [...element.querySelectorAll('input')].map((input) => input.getBoundingClientRect().width)
      return { scrolls: element.scrollWidth > element.clientWidth, role: element.getAttribute('role'), tabindex: element.getAttribute('tabindex'), label: element.getAttribute('aria-label'), head: Math.max(0, ...heads), input: Math.min(Number.POSITIVE_INFINITY, ...inputs) }
    }),
  )
  for (const frame of measured) {
    expect(frame).toMatchObject({ role: 'region', tabindex: '0' })
    expect(frame.label).not.toBe('')
    // Spaltenköpfe stehen in einer Zeile, nicht buchstabenweise untereinander; Eingabefelder sind bedienbar breit.
    expect(frame.head).toBeLessThan(40)
    expect(frame.input).toBeGreaterThanOrEqual(80)
  }
  // Die Tabelle der Vorhabenprüfungen ist breiter als das Fenster: Ihr Rahmen rollt, auch mit den Pfeiltasten.
  const wide = frames.nth(measured.findIndex((frame) => frame.scrolls))
  await wide.focus()
  await expect(wide).toBeFocused()
  await page.keyboard.press('ArrowRight')
  await page.keyboard.press('ArrowRight')
  await expect.poll(() => wide.evaluate((element) => element.scrollLeft)).toBeGreaterThan(0)
  // Kein Wort wird mitten im Wort gebrochen: Die Zeilenbeschriftungen der ersten Tabelle bleiben wortweise umbrochen.
  const wrap = await page.locator('.fa-st__report-table tbody th').first().evaluate((element) => getComputedStyle(element).overflowWrap)
  expect(wrap).toBe('break-word')
})

test('Blattwahl per Tastatur setzt den Fokus auf das Blatt; die Wahl eines anderen Blatts und der Excel-Export sind keine ungesicherte Änderung', async ({ page }) => {
  await page.goto(ALL)
  await (await locateVariant(page, '03_MUS_1Z')).focus()
  await page.keyboard.press('Enter')
  await expect(page.locator('[data-sheet-view="03_MUS_1Z"]')).toBeFocused()
  await page.getByRole('button', { name: 'Arbeitsstand' }).click()
  await page.getByRole('menuitem', { name: 'Beispielwerte laden' }).click()
  await expect(page.locator('[data-status]')).not.toContainText('geändert')
  // Anderes Blatt wählen: keine Änderung, solange nichts eingegeben ist.
  await page.getByRole('button', { name: CHANGE_METHOD }).click()
  await pick(page, '08_SRS_1Z')
  await expect(page.locator('[data-sheet-view="08_SRS_1Z"]')).toBeVisible()
  await expect(page.locator('[data-status]')).not.toContainText('geändert')
  // Eine Eingabe ist eine Änderung; nach dem Export (er trägt den Arbeitsstand) gilt der Stand als gesichert.
  await page.locator('[data-cell="C22"] input').fill('1')
  await expect(page.locator('[data-status]')).toContainText('geändert')
  const download = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Ergebnis exportieren' }).click()
  expect((await download).suggestedFilename()).toMatch(/\.xlsx$/)
  await expect(page.locator('[data-status]')).toContainText('gespeichert')
})
