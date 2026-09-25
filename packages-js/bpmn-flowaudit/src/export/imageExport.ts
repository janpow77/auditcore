/**
 * File output for the image formats, ported from `bildExport.ts` of the
 * audit_designer (`ladeHerunter` → `download`, `dateiname` → `fileName`,
 * `svgNachPng` → `svgToPng`). SVG goes out unchanged; for PNG the SVG is
 * painted onto a canvas at twice the resolution – a screen-size process
 * image is unreadable in print.
 */

export function download(content: Blob, name: string): void {
  const url = URL.createObjectURL(content)
  const link = document.createElement('a')
  link.href = url
  link.download = name
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/** File name without blanks and special characters. */
export function fileName(name: string, extension: string): string {
  const base = (name || 'diagramm').replace(/\s+/g, '_').replace(/[\\/:*?"<>|]/g, '')
  return `${base || 'diagramm'}.${extension}`
}

export function readSvgSize(svg: string): { width: number; height: number } {
  const width = Number(/width="([\d.]+)"/.exec(svg)?.[1] ?? 0)
  const height = Number(/height="([\d.]+)"/.exec(svg)?.[1] ?? 0)
  if (width > 0 && height > 0) return { width, height }
  const parts = /viewBox="([-\d.\s]+)"/.exec(svg)?.[1]?.trim().split(/\s+/).map(Number)
  if (parts?.length === 4 && parts[2] > 0 && parts[3] > 0) return { width: parts[2], height: parts[3] }
  return { width: 1200, height: 800 }
}

async function loadImage(svg: string): Promise<HTMLImageElement> {
  const image = new Image()
  await new Promise<void>((resolve, reject) => {
    image.onload = () => resolve()
    image.onerror = () => reject(new Error('Das Diagramm konnte nicht als Bild geladen werden.'))
    image.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`
  })
  return image
}

/** Paints an SVG onto a canvas with white ground. `scale` 2 ≈ 192 dpi. */
export async function svgToCanvas(svg: string, scale = 2): Promise<HTMLCanvasElement> {
  const size = readSvgSize(svg)
  const image = await loadImage(svg)
  const canvas = document.createElement('canvas')
  canvas.width = Math.max(1, Math.round(size.width * scale))
  canvas.height = Math.max(1, Math.round(size.height * scale))
  const context = canvas.getContext('2d')
  if (!context) throw new Error('Die Zeichenfläche steht nicht zur Verfügung.')
  // White ground: PNG knows transparency, Word prints it grey.
  context.fillStyle = '#ffffff'
  context.fillRect(0, 0, canvas.width, canvas.height)
  context.drawImage(image, 0, 0, canvas.width, canvas.height)
  return canvas
}

function canvasToBlob(canvas: HTMLCanvasElement, type: string, quality?: number): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error('Das Bild konnte nicht erzeugt werden.'))), type, quality)
  })
}

export async function svgToPng(svg: string, scale = 2): Promise<Blob> {
  return canvasToBlob(await svgToCanvas(svg, scale), 'image/png')
}

export async function svgToJpeg(svg: string, scale = 2, quality = 0.92): Promise<{ bytes: Uint8Array; width: number; height: number }> {
  const canvas = await svgToCanvas(svg, scale)
  const blob = await canvasToBlob(canvas, 'image/jpeg', quality)
  return { bytes: new Uint8Array(await blob.arrayBuffer()), width: canvas.width, height: canvas.height }
}
