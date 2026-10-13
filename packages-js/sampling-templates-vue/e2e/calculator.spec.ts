import { readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Download, type Page } from '@playwright/test'
import { writeWorkbook } from '../../sampling-templates-core/src/xlsx/writer'

const SHOTS = process.env.SAMPLING_SCREENSHOTS ?? 'e2e-results'
/** Fester Blattbestand, damit die Tests nicht davon abhängen, welche Blätter inzwischen dazugekommen sind. */
const BASE = 'entwurf=0&blaetter=02_Grundgesamtheit,03_MUS_1Z,04_MUS_1Z_S,17_Unterstichprobe'
const shot = (page: Page, name: string) => page.screenshot({ path: join(SHOTS, `${name}.png`), fullPage: true })
const nbsp = (text: string): string => text.replaceAll(String.fromCharCode(160), ' ')

async function chooseSheet03(page: Page, extra = ''): Promise<void> {
  await page.goto(`/?${BASE}${extra}`)
  await page.getByRole('button', { name: /Blatt 03/ }).click()
  await expect(page.getByRole('heading', { name: 'H · Zu prüfende Grundgesamtheit' })).toBeVisible()
}

async function menu(page: Page, item: string | RegExp): Promise<void> {
  await page.getByRole('button', { name: 'Arbeitsstand' }).click()
  await page.getByRole('menuitem', { name: item }).click()
}

async function summary(page: Page): Promise<Record<string, string>> {
  const terms = await page.locator('.fa-st__kv dt').allTextContents()
  const values = await page.locator('.fa-st__kv dd').allTextContents()
  return Object.fromEntries(terms.map((term, index) => [term, nbsp(values[index] ?? '')]))
}

const EXPECTED = { Auswahlintervall: '480.681,82 €', 'Extrapolierter Fehler': '316.422,73 €', Gesamtfehlerquote: '0,652 %', 'Obere Fehlergrenze': '1,086 %' }

async function expectSampleResults(page: Page): Promise<void> {
  await expect(page.locator('[data-result="primary"]')).toHaveText(/^92\s+Einheiten$/)
  expect(await summary(page)).toMatchObject(EXPECTED)
}

async function saved(download: Download): Promise<string> {
  const path = join(SHOTS, download.suggestedFilename())
  await download.saveAs(path)
  return path
}

/** Kein waagerechtes Scrollen der Seite; im Fehlerfall nennt die Meldung die überstehenden Elemente. */
async function noOverflow(page: Page): Promise<void> {
  const offenders = await page.evaluate(() => {
    const width = document.documentElement.clientWidth
    if (document.documentElement.scrollWidth <= width) return []
    return [...document.querySelectorAll('.fa-st *')]
      .filter((element) => element.getBoundingClientRect().right > width + 0.5)
      .slice(0, 8)
      .map((element) => `${element.tagName.toLowerCase()}.${element.className} → ${Math.round(element.getBoundingClientRect().right)} px`)
  })
  expect(offenders).toEqual([])
}

async function accessible(page: Page): Promise<void> {
  const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze()
  expect(result.violations.map((violation) => `${violation.id}: ${violation.nodes.map((node) => node.target.join(' ')).join(' | ')}`)).toEqual([])
}

test('Verfahrensauswahl ist per Tastatur bedienbar und nennt nicht verfügbare Varianten', async ({ page }) => {
  await page.goto(`/?${BASE}`)
  await expect(page.getByRole('heading', { name: 'Welches Stichprobenverfahren wenden Sie an?' })).toBeVisible()
  await shot(page, '01_auswahl_hell')
  await accessible(page)
  const tabs = page.getByRole('tab')
  await tabs.first().focus()
  await page.keyboard.press('ArrowDown')
  await expect(tabs.nth(1)).toBeFocused()
  await expect(tabs.nth(1)).toHaveAttribute('aria-selected', 'true')
  await expect(page.getByRole('button', { name: /Blatt 08/ })).toHaveAttribute('aria-disabled', 'true')
  await page.keyboard.press('End')
  await expect(page.getByRole('tabpanel')).toContainText('Keine gebrauchsfertige Methode der DelVO')
  await page.keyboard.press('Home')
  await page.keyboard.press('Tab')
  await page.keyboard.press('Tab')
  await expect(page.getByRole('button', { name: /Blatt 03/ })).toBeFocused()
  await page.keyboard.press('Enter')
  await expect(page.locator('.fa-st__chip')).toContainText('Blatt 03')
  await expect(page.locator('.fa-st__chip')).toContainText('MUS, 1 Zeitraum')
})

test('Blatt 03 mit Beispielwerten ergibt die Werte des Gestaltungsprototyps', async ({ page }) => {
  await chooseSheet03(page)
  await menu(page, 'Beispielwerte laden')
  await expect(page.locator('[data-notice="sample"]')).toContainText('stammen aus keiner Prüfung')
  await expectSampleResults(page)
  await expect(page.locator('.fa-st__hint-list li')).toHaveCount(7)
  await noOverflow(page)
  await accessible(page)
  await shot(page, '02_rechenblatt_hell')
})

test('Rundlauf Speichern → Neu → Öffnen, Excel-Export → Öffnen, manipulierte Datei', async ({ page }) => {
  await chooseSheet03(page)
  await menu(page, 'Beispielwerte laden')
  await page.getByLabel('Voraussichtliche Standardabweichung der Fehlerquoten (σ_r)').fill('0,24')
  await expect(page.locator('[data-cell="C21"] .fa-st__value')).toHaveText('366')
  await expect(page.locator('[data-status]')).toContainText('geändert')

  const [json] = await Promise.all([page.waitForEvent('download'), menu(page, /Arbeitsstand speichern/)])
  expect(json.suggestedFilename()).toBe('Stichprobe_03_MUS_1Z_2025_2026_Arbeitsstand.json')
  const jsonPath = await saved(json)
  await expect(page.locator('[data-status]')).toContainText('gespeichert')
  const before = await summary(page)

  await menu(page, /Neu/)
  await expect(page.locator('[data-result="primary"]')).toHaveText('noch keine Angaben')
  await page.locator('input[type="file"]').setInputFiles(jsonPath)
  await expect(page.locator('[data-cell="C21"] .fa-st__value')).toHaveText('366')
  expect(await summary(page)).toEqual(before)
  await expect(page.locator('[data-notice]')).toHaveCount(0)

  const [xlsx] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: 'Ergebnis exportieren' }).click()])
  expect(xlsx.suggestedFilename()).toBe('Stichprobe_03_MUS_1Z_2025_2026_Ergebnis.xlsx')
  const xlsxPath = await saved(xlsx)
  await menu(page, /Neu/)
  await page.locator('input[type="file"]').setInputFiles(xlsxPath)
  await expect(page.locator('[data-cell="C21"] .fa-st__value')).toHaveText('366')
  expect(await summary(page)).toEqual(before)
  await expect(page.locator('[data-notice]')).toHaveCount(0)

  const tampered = join(SHOTS, 'manipuliert.json')
  writeFileSync(tampered, readFileSync(jsonPath, 'utf8').replace('"C7": 48500000', '"C7": 58500000'))
  await page.locator('input[type="file"]').setInputFiles(tampered)
  await expect(page.locator('[data-notice="warning"]')).toContainText('Die Prüfsumme stimmt nicht: Die Datei ist außerhalb der Anwendung verändert worden.')
  await shot(page, '05_pruefsummenhinweis')
})

test('zur Laufzeit wird nichts von fremden Hosts geladen und die Content-Security-Policy hält', async ({ page, baseURL }) => {
  const requests: string[] = []
  const problems: string[] = []
  page.on('request', (request) => requests.push(request.url()))
  page.on('console', (message) => message.type() === 'error' && problems.push(message.text()))
  page.on('pageerror', (error) => problems.push(error.message))
  await chooseSheet03(page, '&entwurf=1')
  await menu(page, 'Beispielwerte laden')
  await page.getByLabel('Konfidenzniveau').selectOption('0.95')
  await Promise.all([page.waitForEvent('download'), menu(page, /Arbeitsstand speichern/)])
  await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: 'Ergebnis exportieren' }).click()])
  await expect(page.locator('meta[http-equiv="Content-Security-Policy"]')).toHaveAttribute('content', /default-src 'self'/)
  expect(requests.filter((url) => !url.startsWith(baseURL ?? '') && !url.startsWith('blob:') && !url.startsWith('data:'))).toEqual([])
  expect(requests.length).toBeGreaterThan(2)
  expect(problems).toEqual([])
})

for (const theme of ['light', 'dark'] as const) {
  test(`Darstellung ${theme === 'dark' ? 'dunkel' : 'hell'}: 1280 px und 390 px ohne waagerechtes Scrollen, ohne axe-Verstöße`, async ({ page }) => {
    const name = theme === 'dark' ? 'dunkel' : 'hell'
    await page.emulateMedia({ colorScheme: theme })
    await chooseSheet03(page, `&theme=${theme}`)
    await menu(page, 'Beispielwerte laden')
    await expectSampleResults(page)
    await accessible(page)
    await noOverflow(page)
    if (theme === 'dark') await shot(page, '03_rechenblatt_dunkel')
    await page.setViewportSize({ width: 390, height: 844 })
    await expectSampleResults(page)
    await noOverflow(page)
    await accessible(page)
    await shot(page, `04_rechenblatt_390_${name}`)
    await page.getByRole('button', { name: 'Verfahren wechseln' }).click()
    await noOverflow(page)
    await accessible(page)
    await shot(page, `06_auswahl_390_${name}`)
    await page.setViewportSize({ width: 1280, height: 900 })
    if (theme === 'dark') await shot(page, '01_auswahl_dunkel')
  })
}

test('eigene Tokens einer Anwendung werden durchgereicht', async ({ page }) => {
  await chooseSheet03(page, '&tokens=app&theme=light')
  await menu(page, 'Beispielwerte laden')
  const accent = await page.getByRole('button', { name: 'Ergebnis exportieren' }).evaluate((element) => getComputedStyle(element).backgroundColor)
  expect(accent).toBe('rgb(74, 79, 196)')
  await accessible(page)
  await shot(page, '07_eigene_tokens')
})

test('Kontextfluss: Grundgesamtheit → Wegweiser → Methodenblatt mit vorbelegtem, überschreibbarem BV und N', async ({ page }) => {
  await page.goto(`/?${BASE}`)
  await expect(page.locator('[data-guide]')).toContainText('empfiehlt kein Verfahren')
  await page.getByRole('button', { name: 'Grundgesamtheit' }).click()
  await expect(page.getByRole('heading', { name: 'A · Abdeckung und Bezugszeitraum' })).toBeVisible()
  await page.getByLabel('Anzahl Datensätze mit positivem Wert (> 0)').fill('251')
  await page.getByLabel('Summe der Datensätze mit positivem Wert').fill('17.300.000,00')
  await expect(page.locator('[data-cell="C52"] .fa-st__value')).toHaveText('251')
  await accessible(page)
  await noOverflow(page)
  await shot(page, '08_grundgesamtheit')
  await page.getByRole('button', { name: 'Verfahren', exact: true }).click()
  await expect(page.locator('[data-guide-item="C53"]')).toHaveText('✔ weniger als 300 Einheiten: nichtstatistisches Verfahren zulässig (Art. 79 Abs. 2 VO (EU) 2021/1060)')
  await expect(page.locator('[data-guide-item="C54"]')).toHaveText('Mindestumfang bei nichtstatistischem Verfahren (10 % der Einheiten): 26 (Art. 6 Abs. 2 DelVO.)')
  await expect(page.locator('[data-guide-item="limited-size"]')).toContainText('Kategorie 1 oder 2')
  await accessible(page)
  await shot(page, '09_wegweiser')
  await page.getByRole('button', { name: /Blatt 03/ }).click()
  const bookValue = page.getByLabel('Buchwert der angepassten zu prüfenden Grundgesamtheit (positive Einheiten) (BV)')
  await expect(bookValue).toHaveValue('17.300.000,00')
  await expect(page.locator('[data-cell="C7"] [data-link]')).toHaveText('aus Blatt 02_Grundgesamtheit vorbelegt')
  await expect(page.getByLabel('Umfang der Grundgesamtheit (Anzahl Stichprobeneinheiten) (N)')).toHaveValue('251')
  await bookValue.fill('16.000.000,00')
  await expect(page.locator('[data-cell="C7"] [data-link]')).toHaveText('Vorbelegung überschrieben')
  await expect(page.locator('[data-cell="C16"] .fa-st__value')).toHaveText(/^320\.000,00/)
  await shot(page, '10_verknuepfung_ueberschrieben')
})

test('Schichttabelle: hinzufügen bis zur achten Schicht, eigener Rollbereich, per Tastatur bedienbar', async ({ page }) => {
  await page.goto(`/?${BASE}`)
  await page.getByRole('button', { name: /Blatt 04/ }).click()
  await menu(page, 'Beispielwerte laden')
  const table = page.locator('[data-strata]').first()
  await expect(table.locator('thead th')).toHaveText(['Gesamt', 'Schicht 1', 'Schicht 2', 'Schicht 3'])
  await expect(page.locator('[data-result="primary"]')).toContainText('Einheiten')
  await accessible(page)
  await shot(page, '11_schichttabelle')
  const add = table.getByRole('button', { name: 'Schicht hinzufügen' })
  await add.focus()
  for (let count = 3; count < 8; count += 1) await page.keyboard.press('Enter')
  await expect(table.locator('thead th').last()).toHaveText('Schicht 8')
  await expect(table.locator('[data-strata-note]')).toContainText('Die 8. bis 20. Schicht ist eine Erweiterung der Webfassung')
  await page.getByLabel('Buchwert je Schicht (BV_h) – Schicht 8').fill('1.000.000,00')
  await expect(page.locator('[data-cell="C9"]').first()).toHaveText(/^49\.500\.000,00/)
  await noOverflow(page)
  const scrollable = await table.locator('[role="region"]').evaluate((element) => element.scrollWidth > element.clientWidth)
  expect(scrollable).toBe(true)
  await accessible(page)
  await shot(page, '12_schichttabelle_8_schichten')
  await page.setViewportSize({ width: 390, height: 844 })
  await noOverflow(page)
  await accessible(page)
  await shot(page, '13_schichttabelle_390')
  await table.getByRole('button', { name: 'Letzte Schicht entfernen' }).click()
  await expect(table.locator('thead th').last()).toHaveText('Schicht 7')
  await expect(page.locator('[data-cell="C9"]').first()).toHaveText(/^48\.500\.000,00/)
})

test('Unterstichproben: Liste, Einfügen, Übernahme der Summen in das Methodenblatt', async ({ page }) => {
  await chooseSheet03(page)
  await menu(page, 'Beispielwerte laden')
  await page.getByRole('button', { name: 'Unterstichproben' }).click()
  await expect(page.locator('[data-unit]')).toHaveCount(1)
  await page.getByRole('button', { name: 'Aus Zwischenablage oder CSV einfügen' }).click()
  const dialog = page.getByRole('dialog', { name: 'Stichprobeneinheiten einfügen' })
  await dialog.getByLabel('Eingefügter Text').fill('C5;C6;C10;C11;C12;W5\nV-3;900.000,00;20;50.000,00;500,00;hochwertige Einheit\nV-4;640.000,00;30;61.000,00;915,00;Zufallsschicht')
  await dialog.getByRole('button', { name: 'Einheiten übernehmen' }).click()
  await expect(page.locator('[data-unit]')).toHaveCount(3)
  await expect(page.locator('[data-total="highValueErrors"]')).toHaveText(/^9\.000,00/)
  await expect(page.locator('[data-total="errorRateSum"]')).toHaveText('0,0300')
  await accessible(page)
  await noOverflow(page)
  await shot(page, '14_unterstichproben')
  await page.getByRole('button', { name: 'Einheit 1 bearbeiten' }).click()
  await expect(page.getByLabel('Kennung der Stichprobeneinheit (Vorhaben / Ausgabenerklärung)')).toHaveValue('Beispiel-Vorhaben 17')
  await page.getByRole('button', { name: 'Summen in Blatt 03 übernehmen' }).click()
  await expect(page.locator('[data-flash]')).toHaveText('Übernommen in Blatt 03: C37, C38.')
  await page.getByRole('button', { name: 'Verfahren', exact: true }).click()
  await expect(page.getByLabel('Summe der Fehler in den hochwertigen Einheiten (ΣE_e)')).toHaveValue('9.000,00')
  await expect(page.getByLabel('Summe der Fehlerquoten der Stichprobe der Zufallsschicht (Σ E_i/BV_i)')).toHaveValue('0,03')
  await page.setViewportSize({ width: 390, height: 844 })
  await page.getByRole('button', { name: 'Unterstichproben' }).click()
  await noOverflow(page)
  await shot(page, '15_unterstichproben_390')
})

test('englische Arbeitsübersetzung ist gekennzeichnet; gespeicherte Werte bleiben deutsch', async ({ page }) => {
  await page.goto(`/?${BASE}&sprache=en`)
  await page.getByRole('button', { name: /Sheet 03/ }).click()
  await menu2(page, 'Working file', 'Load example values')
  await expect(page.locator('[data-result="primary"]')).toHaveText(/^92\s+units$/)
  await expect(page.locator('[data-cell="C13"]')).toContainText('✔ medium: value between the corner values')
  await expect(page.locator('[data-translation-note]')).toContainText('Working translation')
  await accessible(page)
  await shot(page, '16_englisch')
  const [json] = await Promise.all([page.waitForEvent('download'), menu2(page, 'Working file', /Save working file/)])
  const content = readFileSync(await saved(json), 'utf8')
  expect(JSON.parse(content).blaetter['03_MUS_1Z'].C9).toBe('mittel')
})

test('fehlende Angaben: benannt bzw. als „mit 0 berechnet“ ausgewiesen', async ({ page }) => {
  await chooseSheet03(page)
  await menu(page, 'Beispielwerte laden')
  await page.getByLabel('Standardabweichung der Fehlerquoten in der Stichprobe der Zufallsschicht (s_r)').fill('')
  await expect(page.locator('[data-cell="C43"] [data-zero-note]')).toContainText('Keine Angabe, daher mit 0 berechnet')
  await expect(page.locator('[data-cell="C52"]')).toContainText('✔ GFQ und obere Fehlergrenze unter der Schwelle')
  await expect(page.locator('[data-hint="web"] .fa-badge--warning')).toContainText('Keine Angabe, daher mit 0 berechnet')
  await page.getByLabel('Voraussichtliche Standardabweichung der Fehlerquoten (σ_r)').fill('')
  await expect(page.locator('[data-cell="C27"] [data-missing-note]')).toHaveText('Es fehlt: Voraussichtliche Standardabweichung der Fehlerquoten (σ_r) (C20)')
  await accessible(page)
  await noOverflow(page)
  await shot(page, '17_fehlende_angaben')
})

test('ausgefüllte Vorlage: Vorschau nennt Umdeutungen und Abweichungen, Übernahme erst danach; unlesbare Datei wird gemeldet', async ({ page }) => {
  const values: Record<number, number | string> = { 7: 48500000, 8: 420, 9: 'Mittel', 10: 0.7, 11: 'Einseitig', 14: 0.02, 17: 0.007, 20: '0,12', 22: 2, 23: 'NEIN', 24: 'ja', 27: 92, 38: 'k. A.' }
  const rows = Array.from({ length: 40 }, (_, index) => [null, null, values[index + 1] === undefined ? null : { value: values[index + 1]! }])
  const template = join(SHOTS, 'vorlage_schreibweise.xlsx')
  writeFileSync(template, writeWorkbook([{ name: '03_MUS_1Z', rows }]))
  await chooseSheet03(page)
  await page.locator('input[type="file"]').setInputFiles(template)
  const dialog = page.getByRole('dialog', { name: 'Excel-Vorlage übernehmen' })
  await expect(dialog).toContainText('werden 11 Eingaben übernommen')
  await expect(dialog.locator('[data-import-issues] tbody tr')).toHaveCount(6)
  await expect(dialog.locator('[data-import-issues]')).toContainText('Schreibweise an die Auswahlliste angepasst')
  await expect(dialog.locator('[data-import-issues]')).toContainText('keine lesbare Zahl')
  await expect(dialog.locator('[data-import-differences] tbody tr')).toHaveCount(1)
  await accessible(page)
  await shot(page, '18_importvorschau')
  await dialog.getByRole('button', { name: 'Eingaben übernehmen' }).click()
  await expect(page.locator('[data-cell="C27"] .fa-st__value')).toHaveText('30')
  await expect(page.locator('[data-cell="C12"] .fa-st__value')).toHaveText('0,524')
  const broken = join(SHOTS, 'kaputt.xlsx')
  writeFileSync(broken, 'kein Archiv')
  await page.locator('input[type="file"]').setInputFiles(broken)
  await page.getByRole('button', { name: 'Änderungen verwerfen' }).click()
  await expect(page.locator('[data-notice="danger"]')).toContainText('konnte nicht gelesen werden')
})

async function menu2(page: Page, name: string, item: string | RegExp): Promise<void> {
  await page.getByRole('button', { name }).click()
  await page.getByRole('menuitem', { name: item }).click()
}

/**
 * Einbindung in eine Anwendung mit eigenen Tokens, geprüft mit den echten Dateien
 * der Anwendung: `SAMPLING_APP_TOKENS` (Tokens der Anwendung) und
 * `SAMPLING_APP_BRIDGE` (Zuordnung zu `--fa-*`). Ohne die Variablen entfällt der Test.
 */
const APP_TOKENS = process.env.SAMPLING_APP_TOKENS
const APP_BRIDGE = process.env.SAMPLING_APP_BRIDGE

for (const theme of ['light', 'dark'] as const) {
  test(`Tokens der Anwendung über die Zuordnungsdatei (${theme})`, async ({ page }) => {
    test.skip(!APP_TOKENS || !APP_BRIDGE, 'SAMPLING_APP_TOKENS und SAMPLING_APP_BRIDGE nicht gesetzt')
    await page.route('**/app-styles/*.css', (route) =>
      route.fulfill({ contentType: 'text/css', body: readFileSync(route.request().url().endsWith('tokens.css') ? (APP_TOKENS as string) : (APP_BRIDGE as string), 'utf8') }),
    )
    await chooseSheet03(page, `&theme=${theme}`)
    await page.evaluate((mode) => (document.documentElement.dataset.theme = mode), theme)
    await page.addStyleTag({ url: '/app-styles/tokens.css' })
    await page.addStyleTag({ url: '/app-styles/bridge.css' })
    await menu(page, 'Beispielwerte laden')
    await expectSampleResults(page)
    const colors = await page.getByRole('button', { name: 'Ergebnis exportieren' }).evaluate((element) => {
      const root = getComputedStyle(document.documentElement)
      return { button: getComputedStyle(element).backgroundColor, text: getComputedStyle(document.querySelector('.fa-st') as Element).color, expectedText: root.getPropertyValue('--eco-text').trim() }
    })
    expect(colors.button).toBe(theme === 'light' ? 'rgb(74, 79, 196)' : 'rgb(124, 133, 240)')
    expect(colors.text).toBe(theme === 'light' ? 'rgb(26, 26, 46)' : 'rgb(236, 236, 246)')
    await accessible(page)
    await noOverflow(page)
    await shot(page, `19_anwendungstokens_${theme}`)
    await page.locator('[data-cell="C8"] input').fill('1300')
    await menu(page, /Neu/)
    await expect(page.getByRole('dialog')).toBeVisible()
    await accessible(page)
    await shot(page, `20_anwendungstokens_dialog_${theme}`)
  })
}
