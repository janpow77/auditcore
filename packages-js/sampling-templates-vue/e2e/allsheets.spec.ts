import { join } from 'node:path'
import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'

/**
 * Voller Blattbestand im Browser: je Blattart ein Verfahren mit Beispielwerten,
 * hell und dunkel, 1280 px und 390 px, ohne axe-Verstöße und ohne waagerechtes
 * Scrollen der Seite; dazu Gesamtfehlerquote, Bericht mit Druckansicht,
 * Datentabelle X1a und die Schichttabelle der Altvorlage X3.
 */
const SHOTS = process.env.SAMPLING_SCREENSHOTS ?? 'e2e-results'
const shot = (page: Page, name: string) => page.screenshot({ path: join(SHOTS, `${name}.png`), fullPage: true })

async function accessible(page: Page): Promise<void> {
  const result = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze()
  expect(result.violations.map((violation) => `${violation.id}: ${violation.nodes.map((node) => node.target.join(' ')).join(' | ')}`)).toEqual([])
}

async function noOverflow(page: Page): Promise<void> {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  expect(overflow).toBeLessThanOrEqual(0)
}

/** Verfahren wählen: die Familie suchen, die die Kachel des Blatts zeigt. */
async function choose(page: Page, sheet: string, theme: string): Promise<void> {
  await page.goto(`/?entwurf=0&theme=${theme}`)
  const tabs = page.getByRole('tab')
  const tile = page.locator(`[data-sheet="${sheet}"]`)
  for (let index = 0; index < (await tabs.count()); index += 1) {
    await tabs.nth(index).click()
    if (await tile.count()) break
  }
  await tile.click()
  await expect(page.locator(`[data-sheet-view="${sheet}"]`)).toBeVisible()
}

async function loadSample(page: Page): Promise<void> {
  await page.getByRole('button', { name: 'Arbeitsstand' }).click()
  await page.getByRole('menuitem', { name: 'Beispielwerte laden' }).click()
  await expect(page.locator('[data-result="primary"]')).toContainText(/\d/)
}

const KINDS: readonly { sheet: string; name: string }[] = [
  { sheet: '06_MUS_2Z_S', name: 'mus_2z_geschichtet' },
  { sheet: '12_SRS_3Z', name: 'srs_3z' },
  { sheet: '11_SRS_2Z_S', name: 'srs_2z_geschichtet' },
  { sheet: '16_NS_PPS_S', name: 'nichtstatistisch_pps_geschichtet' },
  { sheet: 'X3_DiffSch_S_2017', name: 'altvorlage_x3' },
]

for (const theme of ['light', 'dark'] as const) {
  for (const kind of KINDS) {
    test(`${kind.sheet} (${theme}): Beispielwerte, 1280 px und 390 px, axe`, async ({ page }) => {
      await choose(page, kind.sheet, theme)
      await expect(page.locator('[data-result="primary"]')).toHaveText('noch keine Angaben')
      await loadSample(page)
      await accessible(page)
      await noOverflow(page)
      await shot(page, `30_${kind.name}_${theme}`)
      await page.setViewportSize({ width: 390, height: 844 })
      await noOverflow(page)
      await accessible(page)
      await shot(page, `30_${kind.name}_390_${theme}`)
    })
  }

  test(`Gesamtfehlerquote und Bericht (${theme}): Übernahme aus dem Verfahren, Druckansicht auf einer Seite`, async ({ page }) => {
    await choose(page, '03_MUS_1Z', theme)
    await loadSample(page)
    await page.getByRole('button', { name: 'Grundgesamtheit' }).click()
    await loadSampleFor(page)
    // Beispielwerte laden lässt den gewählten Arbeitsschritt stehen.
    await expect(page.locator('[data-sheet-view="02_Grundgesamtheit"]')).toBeVisible()
    await page.getByRole('button', { name: 'Gesamtfehlerquote' }).click()
    await expect(page.locator('[data-sheet-view="18_GFQ_AnhIII"]')).toBeVisible()
    await expect(page.locator('[data-cell="C4"]')).toContainText('03_MUS_1Z')
    await expect(page.locator('[data-cell="C6"]')).toContainText('316.422,73')
    await accessible(page)
    await noOverflow(page)
    await shot(page, `31_gesamtfehlerquote_${theme}`)
    await page.getByRole('button', { name: 'Bericht' }).click()
    await expect(page.locator('.fa-st__report-page')).toBeVisible()
    await expect(page.locator('.fa-st__report')).toContainText('ersetzt nicht die fachliche Würdigung der Prüfbehörde')
    await expect(page.locator('.fa-st__report')).toContainText('Fassung 4, Stand Oktober 2026')
    await accessible(page)
    await noOverflow(page)
    await shot(page, `32_bericht_${theme}`)
    await page.setViewportSize({ width: 390, height: 844 })
    await noOverflow(page)
    await accessible(page)
    await shot(page, `32_bericht_390_${theme}`)
    // Druck: nur die Berichtsseite, Bedienelemente und Steuerfelder ausgeblendet.
    await page.setViewportSize({ width: 1280, height: 900 })
    await page.emulateMedia({ media: 'print' })
    await expect(page.locator('.fa-st__report-page')).toBeVisible()
    await expect(page.locator('[data-action="print"]')).toBeHidden()
    await expect(page.locator('.fa-st__bar')).toBeHidden()
    await expect(page.locator('.fa-st__report-controls')).toBeHidden()
    // Kopf- und Fußzeile nennen die (erfundenen) Angaben der Beispielwerte, keine feste Behörde.
    await expect(page.locator('[data-report-subtitle]')).toContainText('Beispielprogramm EFRE Musterland 2021–2027 · CCI')
    await expect(page.locator('[data-report-footer]')).toHaveText('Prüfbehörde Musterland (Beispiel), Referat Beispiel, Musterstadt')
    // Leere Freitexte: kein Platzhalter in eckigen Klammern im Druck.
    await expect(page.locator('[data-cell="A9"] textarea')).toBeHidden()
    expect(await page.locator('[data-cell="A9"] .fa-st__report-print').innerText()).toBe('')
    // Die Seitengröße hängt an einer benannten Seite; eine unbenannte @page-Regel gibt es nicht.
    const pageRules = await page.evaluate(() => [...document.styleSheets].flatMap((sheet) => [...sheet.cssRules]).flatMap((rule) => (rule instanceof CSSMediaRule ? [...rule.cssRules] : [rule])).filter((rule) => rule instanceof CSSPageRule).map((rule) => (rule as CSSPageRule).selectorText))
    expect(pageRules).toEqual(['fa-st-report'])
    const pdf = await page.pdf({ format: 'A4', preferCSSPageSize: true }).catch(() => null)
    if (pdf) expect((pdf.toString('latin1').match(/\/Type\s*\/Page[^s]/g) ?? []).length).toBe(1)
    await shot(page, `33_bericht_druck_${theme}`)
  })
}

/** Beispielwerte des gerade angezeigten Arbeitsschritts laden (ohne Prüfung der Hauptgröße eines Verfahrens). */
async function loadSampleFor(page: Page): Promise<void> {
  await page.getByRole('button', { name: 'Arbeitsstand' }).click()
  await page.getByRole('menuitem', { name: 'Beispielwerte laden' }).click()
}

test('fehlt s_r, steht „Keine Angabe, daher mit 0 berechnet“ auch im Bericht', async ({ page }) => {
  await choose(page, '03_MUS_1Z', 'light')
  await loadSample(page)
  await page.locator('[data-cell="C39"] input').fill('')
  await page.locator('[data-cell="C39"] input').blur()
  await page.getByRole('button', { name: 'Bericht' }).click()
  await expect(page.locator('.fa-st__report')).toContainText('Keine Angabe, daher mit 0 berechnet')
  await shot(page, '34_bericht_mit_0_berechnet')
})

test('Datentabelle X1a: als Kachel und aus dem Verfahren X1 heraus, per Tastatur erreichbar', async ({ page }) => {
  await choose(page, 'X1_KonsMUS_2017', 'light')
  await page.locator('[data-action="table-X1a_RF_2017"]').click()
  const dialog = page.getByRole('dialog')
  await expect(dialog).toContainText('Zuverlässigkeitsfaktoren')
  await expect(dialog.locator('tbody tr')).toHaveCount(51)
  await accessible(page)
  await shot(page, '35_datentabelle_x1a')
  await page.setViewportSize({ width: 390, height: 844 })
  await noOverflow(page)
  await shot(page, '35_datentabelle_x1a_390')
  await page.keyboard.press('Escape')
  await expect(dialog).toBeHidden()
})

test('Altvorlage X3: „Letzte Schicht entfernen“ lässt die Eingaben der übrigen Schichten stehen', async ({ page }) => {
  await choose(page, 'X3_DiffSch_S_2017', 'light')
  await loadSample(page)
  const first = await page.locator('[data-cell="E6"] input').inputValue()
  const second = await page.locator('[data-cell="F6"] input').inputValue()
  expect(first).not.toBe('')
  await page.locator('[data-action="strata-remove"]').first().click()
  await page.locator('[data-action="discard"]').click()
  await expect(page.locator('[data-cell="G6"]')).toHaveCount(0)
  expect(await page.locator('[data-cell="E6"] input').inputValue()).toBe(first)
  expect(await page.locator('[data-cell="F6"] input').inputValue()).toBe(second)
  await shot(page, '36_x3_schicht_entfernt')
})

test('alle Verfahren sind wählbar; nur X1a ist eine Datentabelle', async ({ page }) => {
  await page.goto('/?entwurf=0')
  const tabs = page.getByRole('tab')
  let tiles = 0
  for (let index = 0; index < (await tabs.count()); index += 1) {
    await tabs.nth(index).click()
    await expect(page.locator('.fa-st__variants')).not.toContainText('noch nicht verfügbar')
    tiles += await page.locator('.fa-st__variants [data-sheet]').count()
  }
  expect(tiles).toBe(19)
  await expect(page.locator('[data-step-follows]')).toHaveCount(0)
})

test('Bericht ohne Angaben zu Programm und Prüfbehörde: Platzhalter am Bildschirm, im Druck leer', async ({ page }) => {
  await choose(page, '03_MUS_1Z', 'light')
  await page.getByRole('button', { name: 'Bericht' }).click()
  await expect(page.locator('[data-report-programme-missing]')).toBeVisible()
  await expect(page.locator('[data-report-authority-missing]')).toContainText('Prüfbehörde')
  await accessible(page)
  await shot(page, '37_bericht_ohne_angaben')
  await page.emulateMedia({ media: 'print' })
  await expect(page.locator('[data-report-programme-missing]')).toBeHidden()
  await expect(page.locator('[data-report-authority-missing]')).toBeHidden()
  expect((await page.locator('[data-report-footer]').innerText()).trim()).toBe('')
  await shot(page, '37_bericht_ohne_angaben_druck')
  await page.emulateMedia({ media: 'screen' })
  await page.locator('[data-cell="W5"] input').fill('Prüfbehörde Musterland')
  await page.locator('[data-cell="W5"] input').blur()
  await expect(page.locator('[data-report-footer]')).toHaveText('Prüfbehörde Musterland')
})

test('englisch: Kopf- und Fußzeile des Berichts folgen der Sprache', async ({ page }) => {
  await page.goto('/?entwurf=0&sprache=en')
  await page.locator('[data-sheet="03_MUS_1Z"]').click()
  await page.getByRole('button', { name: 'Working file' }).click()
  await page.getByRole('menuitem').filter({ hasText: 'Load example values' }).click()
  await page.locator('[data-step="report"]').click()
  await expect(page.locator('[data-report-subtitle]')).toContainText('Accounting year')
  await expect(page.locator('[data-report-subtitle]')).toContainText('preliminary')
  await expect(page.locator('[data-report-subtitle]')).not.toContainText('Geschäftsjahr')
  await shot(page, '38_bericht_englisch')
})
