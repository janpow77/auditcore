/**
 * Bildparität: jedes Szenario wird mit Vue und React gerendert und beide
 * Aufnahmen gegen dieselbe Baseline (baselines/) verglichen. Weicht eine
 * Fassung ab, schlägt ihr Test fehl. Barrierefreiheit: axe (Tag @axe).
 */
import AxeBuilder from '@axe-core/playwright'
import { expect, test } from '@playwright/test'
import { szenarien } from './szenarien'

for (const szenario of szenarien) {
  for (const fw of ['vue', 'react'] as const) {
    test(`${szenario.id} (${fw})`, async ({ page }) => {
      await page.goto(`/?fw=${fw}&fall=${szenario.id}`)
      await page.locator('body[data-bereit="1"]').waitFor()
      await page.evaluate(() => document.fonts.ready)
      await expect(page.locator('#buehne')).toHaveScreenshot(`${szenario.id}.png`)
    })

    test(`${szenario.id} (${fw}) barrierefrei @axe`, async ({ page }) => {
      await page.goto(`/?fw=${fw}&fall=${szenario.id}`)
      await page.locator('body[data-bereit="1"]').waitFor()
      const ergebnis = await new AxeBuilder({ page }).include('#buehne').analyze()
      expect(ergebnis.violations.map((v) => `${v.id}: ${v.help}`)).toEqual([])
    })
  }
}
