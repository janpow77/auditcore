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
  await expect(page.locator('.fa-folder-card').first()).toBeVisible()
  await expect(page.locator('.fa-overview__ka-cell')).toHaveCount(0)
  await expect(page.locator('details.fa-overview__hints')).not.toHaveAttribute('open', '')
  await shot(page, '01-sammlung')
  await page.locator('details.fa-overview__hints > summary').click()
  await expect(page.locator('.fa-overview__hints')).toContainText('Rechtsgrundlagen-Abdeckung')
  await shot(page, '01b-pruefhinweise')
})

test('folders can be renamed on the card and in the tree', async ({ page }) => {
  await page.goto('/')
  const card = page.locator('.fa-folder-card').filter({ has: page.locator('.fa-inline-name') }).first()
  const oldName = (await card.locator('.fa-inline-name').textContent())!.trim()
  await card.locator('.fa-inline-name').click()
  await page.locator('.fa-inline-name__field').fill('  Umbenannt im Test  ')
  await page.locator('.fa-inline-name__field').press('Enter')
  await expect(page.getByRole('tree')).toContainText('Umbenannt im Test')
  const label = page.locator('.fa-tree__row--folder .fa-tree__label', { hasText: 'Umbenannt im Test' })
  await label.dblclick()
  const dialog = page.getByRole('dialog', { name: 'Ordner umbenennen' })
  await expect(dialog.getByRole('textbox')).toHaveValue('Umbenannt im Test')
  await dialog.getByRole('textbox').fill(oldName)
  await dialog.getByRole('button', { name: 'Übernehmen' }).click()
  // Der Doppelklick wählt den Ordner zugleich aus: Die Übersicht zeigt ihn selbst.
  await expect(page.locator('.fa-overview > h2')).toHaveText(oldName)
  await expect(page.getByRole('tree')).not.toContainText('Umbenannt im Test')
  await shot(page, '01c-ordner-umbenannt')
})

test('palette views, role tiles and a selected sequence flow', async ({ page }) => {
  await page.evaluate(() => localStorage.clear()).catch(() => undefined)
  await openDiagram(page, 'Bewilligung und Auszahlung')
  const palette = page.locator('.fa-palette')
  for (const [option, file] of [['Große Kacheln', '08-palette-kacheln'], ['Liste', '09-palette-liste']] as const) {
    await palette.locator('.fa-palette__head button').click()
    await page.getByRole('menuitemradio', { name: option }).click()
    await shot(page, file)
  }
  await expect(palette).toContainText('Stelle mit Rechnungsführungsfunktion')
  const paletteBox = await palette.boundingBox()
  const canvasBox = await page.locator('.fa-editor .djs-container').boundingBox()
  expect(paletteBox!.x + paletteBox!.width).toBeLessThanOrEqual(canvasBox!.x + 1)
  await page.reload()
  await expect(page.locator('.fa-palette--list')).toHaveCount(1, { timeout: 15_000 }).catch(async () => {
    await openDiagram(page, 'Bewilligung und Auszahlung')
    await expect(page.locator('.fa-palette--list')).toHaveCount(1)
  })

  const pool = page.locator('.djs-shape[data-element-id^="Participant"], .djs-shape[data-element-id^="Lane"]').first()
  if (await pool.count()) {
    const box = await pool.boundingBox()
    await page.mouse.click(box!.x + 12, box!.y + 12)
    await page.getByRole('tab', { name: 'Rolle' }).click()
    await page.locator('.fa-side').evaluate((side) => ((side as HTMLElement).style.width = '320px'))
    const overlaps = await page.locator('.fa-role-option').evaluateAll((tiles) =>
      tiles.some((tile) => Array.from(tile.children).some((child) => child.getBoundingClientRect().right > tile.getBoundingClientRect().right + 0.5)),
    )
    expect(overlaps).toBe(false)
    await shot(page, '10-rollenkacheln-schmal')
  }

  // Approved diagrams are read-only (no bendpoints); use an editable one.
  await openDiagram(page, 'Altbestand')
  const flows = page.locator('.djs-connection[data-element-id]')
  const ids = await flows.evaluateAll((nodes) => nodes.map((node) => [node.getAttribute('data-element-id'), node.querySelectorAll('.djs-visual path').length, (node.querySelector('.djs-visual path')?.getAttribute('d') ?? '').split(/[LM]/).length]))
  const bent = ids.find(([id, , points]) => String(id).includes('Flow') && Number(points) > 3) ?? ids.find(([id]) => String(id).includes('Flow'))
  const flow = page.locator(`.djs-connection[data-element-id="${bent![0]}"]`)
  const point = await flow.locator('.djs-visual path').first().evaluate((path) => {
    const line = path as SVGPathElement
    const at = line.getPointAtLength(line.getTotalLength() / 2)
    const matrix = line.getScreenCTM()!
    return { x: at.x * matrix.a + at.y * matrix.c + matrix.e, y: at.x * matrix.b + at.y * matrix.d + matrix.f }
  })
  await page.mouse.click(point.x, point.y)
  await expect(page.locator('.djs-bendpoints.selected')).toHaveCount(1)
  const fills = await page.locator('.djs-bendpoints.selected .djs-bendpoint .djs-visual').evaluateAll((nodes) => nodes.map((node) => getComputedStyle(node).fill))
  expect(fills.length).toBeGreaterThan(0)
  expect(fills).not.toContain('rgb(0, 0, 0)')
  await page.mouse.move(2, 2)
  const dragger = await page.locator('.djs-bendpoints.selected .djs-segment-dragger .djs-visual').evaluateAll((nodes) => nodes.map((node) => getComputedStyle(node).display))
  expect(dragger.every((display) => display === 'none')).toBe(true)
  const area = await flow.boundingBox()
  const clip = { x: Math.max(0, area!.x - 40), y: Math.max(0, area!.y - 40), width: area!.width + 80, height: area!.height + 80 }
  await page.screenshot({ path: 'e2e-results/11-linie-ausgewaehlt.png', clip })
  await page.evaluate(() => document.querySelector('.fa-editor')?.setAttribute('data-fa-theme', 'dark'))
  await page.screenshot({ path: 'e2e-results/12-linie-ausgewaehlt-dunkel.png', clip })
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
