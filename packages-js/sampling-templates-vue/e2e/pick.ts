/**
 * Verfahrensauswahl im Browser: Methode (Reiter), Zeiträume und Schichtung so
 * einstellen, dass das gesuchte Verfahren erscheint. `variants` sammelt alle so
 * erreichbaren Verfahren und Altvorlagen.
 */
import type { Locator, Page } from '@playwright/test'

/** Alle Filterstellungen der aktuell gewählten Methode durchgehen; `visit` endet mit `true`, sobald gefunden. */
async function eachFilter(page: Page, visit: () => Promise<boolean>): Promise<boolean> {
  if (await visit()) return true
  const periods = page.locator('[data-periods]')
  const strata = page.locator('[data-stratified]')
  const periodCount = Math.max(1, await periods.count())
  for (let period = 0; period < periodCount; period += 1) {
    if (await periods.count()) await periods.nth(period).click()
    for (let stratum = 0; stratum < (await strata.count()); stratum += 1) {
      await strata.nth(stratum).click()
      if (await visit()) return true
    }
  }
  return false
}

/** Stellt die Auswahl auf das Verfahren ein und liefert dessen Schaltfläche („Verfahren verwenden“ bzw. Listeneintrag). */
export async function locateVariant(page: Page, sheet: string): Promise<Locator> {
  const tabs = page.getByRole('tab')
  const target = page.locator(`[data-sheet="${sheet}"]`)
  for (let index = 0; index < (await tabs.count()); index += 1) {
    await tabs.nth(index).click()
    if (await eachFilter(page, async () => (await target.count()) > 0)) return target
  }
  throw new Error(`Verfahren ${sheet} ist in der Auswahl nicht erreichbar`)
}

export async function pick(page: Page, sheet: string): Promise<void> {
  await (await locateVariant(page, sheet)).click()
}

/** Alle in der Auswahl erreichbaren Verfahren mit ihrem Zustand `aria-disabled`. */
export async function variants(page: Page): Promise<Map<string, string | null>> {
  const found = new Map<string, string | null>()
  const tabs = page.getByRole('tab')
  for (let index = 0; index < (await tabs.count()); index += 1) {
    await tabs.nth(index).click()
    await eachFilter(page, async () => {
      for (const button of await page.locator('.fa-st__variants [data-sheet]').all()) found.set((await button.getAttribute('data-sheet')) ?? '', await button.getAttribute('aria-disabled'))
      return false
    })
  }
  return found
}
