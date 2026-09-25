/**
 * Minimal PDF writer: one page per call with a JPEG image fitted into a
 * DIN page (portrait or landscape, with margin). Enough for printing a
 * process diagram without a server – the audit_designer's server PDF
 * export was never implemented (HTTP 501).
 */

import { PX_PER_MM, type Orientation } from '../layout/pageFormats'

export interface PdfImage {
  bytes: Uint8Array
  /** Pixel size of the JPEG. */
  width: number
  height: number
}

export interface PdfOptions {
  format?: 'a4' | 'a3'
  orientation?: Orientation | 'auto'
  marginMm?: number
  title?: string
}

const PT_PER_MM = 72 / 25.4
const SIZES_MM: Record<'a4' | 'a3', [number, number]> = { a4: [210, 297], a3: [297, 420] }

function pageSizePt(options: PdfOptions, image: PdfImage): [number, number] {
  const [w, h] = SIZES_MM[options.format ?? 'a4']
  const landscape = options.orientation === 'quer' || (options.orientation !== 'hoch' && image.width > image.height)
  return landscape ? [h * PT_PER_MM, w * PT_PER_MM] : [w * PT_PER_MM, h * PT_PER_MM]
}

/** Escapes text for a PDF string literal (Latin-1 range only; others become „?“). */
export function pdfString(text: string): string {
  const latin1 = Array.from(text, (ch) => (ch.charCodeAt(0) < 256 ? ch : '?')).join('')
  return `(${latin1.replace(/[\\()]/g, (m) => `\\${m}`)})`
}

class PdfBuilder {
  private readonly chunks: Uint8Array[] = []
  private readonly offsets: number[] = []
  private length = 0

  private push(bytes: Uint8Array): void {
    this.chunks.push(bytes)
    this.length += bytes.length
  }

  text(value: string): void {
    // Latin-1 bytes; object syntax is ASCII, string literals are escaped.
    this.push(Uint8Array.from(value, (ch) => ch.charCodeAt(0) & 0xff))
  }

  object(id: number, body: string, stream?: Uint8Array): void {
    this.offsets[id] = this.length
    this.text(`${id} 0 obj\n${body}\n`)
    if (stream) {
      this.text('stream\n')
      this.push(stream)
      this.text('\nendstream\n')
    }
    this.text('endobj\n')
  }

  finish(rootId: number): Uint8Array {
    const xref = this.length
    const count = this.offsets.length
    let table = `xref\n0 ${count}\n0000000000 65535 f \n`
    for (let id = 1; id < count; id += 1) table += `${String(this.offsets[id] ?? 0).padStart(10, '0')} 00000 n \n`
    this.text(`${table}trailer\n<< /Size ${count} /Root ${rootId} 0 R >>\nstartxref\n${xref}\n%%EOF\n`)
    const result = new Uint8Array(this.length)
    let position = 0
    for (const chunk of this.chunks) {
      result.set(chunk, position)
      position += chunk.length
    }
    return result
  }
}

/** Builds a one-page PDF with the image centred and fitted into the margins. */
export function imageToPdf(image: PdfImage, options: PdfOptions = {}): Uint8Array {
  const [pageW, pageH] = pageSizePt(options, image)
  const margin = (options.marginMm ?? 10) * PT_PER_MM
  const titleSpace = options.title ? 24 : 0
  const scale = Math.min((pageW - 2 * margin) / image.width, (pageH - 2 * margin - titleSpace) / image.height)
  const drawW = image.width * scale
  const drawH = image.height * scale
  const x = (pageW - drawW) / 2
  const y = margin + (pageH - 2 * margin - titleSpace - drawH) / 2
  const title = options.title ? `BT /F1 12 Tf ${margin.toFixed(2)} ${(pageH - margin - 12).toFixed(2)} Td ${pdfString(options.title)} Tj ET\n` : ''
  const content = `${title}q ${drawW.toFixed(2)} 0 0 ${drawH.toFixed(2)} ${x.toFixed(2)} ${y.toFixed(2)} cm /Im1 Do Q`
  const pdf = new PdfBuilder()
  pdf.text('%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
  pdf.object(1, '<< /Type /Catalog /Pages 2 0 R >>')
  pdf.object(2, '<< /Type /Pages /Kids [3 0 R] /Count 1 >>')
  pdf.object(
    3,
    `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${pageW.toFixed(2)} ${pageH.toFixed(2)}] /Resources << /XObject << /Im1 4 0 R >> /Font << /F1 6 0 R >> >> /Contents 5 0 R >>`,
  )
  pdf.object(4, `<< /Type /XObject /Subtype /Image /Width ${image.width} /Height ${image.height} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${image.bytes.length} >>`, image.bytes)
  const contentBytes = Uint8Array.from(content, (ch) => ch.charCodeAt(0) & 0xff)
  pdf.object(5, `<< /Length ${contentBytes.length} >>`, contentBytes)
  pdf.object(6, '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
  return pdf.finish(1)
}

/** Diagram pixels → millimetres at 96 dpi (for choosing the page format). */
export function pixelsToMm(pixels: number): number {
  return pixels / PX_PER_MM
}
