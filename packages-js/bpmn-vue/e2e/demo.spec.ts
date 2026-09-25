import { expect, test, type Page } from '@playwright/test'

const shot = (page: Page, name: string) => page.screenshot({ path: `e2e-results/${name}.png` })

async function openDiagram(page: Page, name: string): Promise<void> {
  await page.goto('/')
  await page.getByRole('tree').getByText(name).first().dblclick()
  await expect(page.locator('.fa-editor .djs-container')).toBeVisible()
}

test('collection with group overview', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Diagrammsammlung' })).toBeVisible()
  await expect(page.locator('.fa-overview')).toContainText('Abdeckung der Kernanforderungen')
  await shot(page, '01-sammlung')
})

test('editor with properties of a task', async ({ page }) => {
  await openDiagram(page, 'Bewilligung und Auszahlung')
  await page.locator('[data-element-id="Task_Bewilligen"]').click()
  await expect(page.getByRole('tab', { name: 'Allgemein' })).toBeVisible()
  await expect(page.locator('.fa-tab-general input').first()).not.toHaveValue('')
  await shot(page, '02-editor-eigenschaften')
  await page.getByRole('tab', { name: 'Rechtsgrundlagen' }).click()
  await expect(page.locator('.fa-legal')).toBeVisible()
  await shot(page, '03-rechtsgrundlagen')
  await page.getByRole('tab', { name: 'Kontrolle & Risiko' }).click()
  await shot(page, '04-kontrolle-risiko')
})

test('issues, diagram info and export dialog', async ({ page }) => {
  await openDiagram(page, 'Anreicherung aus')
  await page.locator('.fa-statusbar__issues').click()
  await expect(page.locator('.fa-issues')).toBeVisible()
  await shot(page, '05-hinweise')
  await page.keyboard.press('Control+f')
  await expect(page.getByRole('dialog')).toBeVisible()
  await page.keyboard.press('Escape')
  await page.locator('.fa-toolbar [aria-label="Diagramm-Infos"]').click()
  await expect(page.getByRole('dialog')).toContainText('Kopfzeile')
  await shot(page, '06-diagramm-infos')
})

test('walk-through test and English UI', async ({ page }) => {
  await page.goto('/?locale=en')
  await expect(page.getByRole('heading', { name: 'Diagram collection' })).toBeVisible()
  await page.getByRole('tree').getByText('Bewilligung und Auszahlung').first().dblclick()
  await expect(page.locator('.fa-editor .djs-container')).toBeVisible()
  await page.getByRole('tab', { name: 'Walk-through test' }).click()
  await expect(page.locator('.fa-walk')).toBeVisible()
  await shot(page, '07-durchlauftest-en')
})
