/**
 * Eigene Textsatz-Logik: Zeilenumbruch, Ausrichtung und Messung von
 * Beschriftungen in SVG.
 *
 * Gemessen wird im Browser über ein Canvas-2D-Kontextobjekt. Steht keines
 * zur Verfügung (Testumgebung, Server), greift eine deterministische
 * Näherung je Zeichenklasse — so bleiben Snapshots stabil.
 */

import { append as svgAppend, attr as svgAttr, create as svgCreate } from 'tiny-svg'

export interface TextStyle {
  fontFamily: string
  fontSize: number
  fontWeight?: string | number
  lineHeight: number
}

export type TextAlign = 'center-middle' | 'center-top' | 'left-top' | 'left-middle'

export interface TextBoxOptions {
  box: { width: number; height: number }
  align?: TextAlign
  padding?: number | { top?: number; right?: number; bottom?: number; left?: number }
  fitBox?: boolean
  style?: Partial<TextStyle>
}

export interface LaidOutLine {
  text: string
  width: number
}

export interface TextLayoutResult {
  lines: LaidOutLine[]
  width: number
  height: number
}

export const DEFAULT_TEXT_STYLE: TextStyle = {
  fontFamily: 'Arial, "Helvetica Neue", Helvetica, sans-serif',
  fontSize: 12,
  lineHeight: 1.2,
}

type Measure = (text: string, style: TextStyle) => number

let canvasContext: CanvasRenderingContext2D | null | undefined

function browserMeasure(text: string, style: TextStyle): number | null {
  if (canvasContext === undefined) {
    canvasContext = null
    try {
      const isHappyOrJsdom =
        typeof navigator !== 'undefined' && /jsdom|HappyDOM/i.test(navigator.userAgent || '')
      if (!isHappyOrJsdom && typeof document !== 'undefined') {
        const canvas = document.createElement('canvas')
        canvasContext = (canvas.getContext && canvas.getContext('2d')) || null
      }
    } catch {
      canvasContext = null
    }
  }
  if (!canvasContext) return null
  canvasContext.font = `${style.fontWeight || 'normal'} ${style.fontSize}px ${style.fontFamily}`
  return canvasContext.measureText(text).width
}

/** Näherungsweise Zeichenbreite in em je Zeichenklasse. */
function approxCharWidth(char: string): number {
  if (/[\s]/.test(char)) return 0.28
  if (/[iIl.,;:!|'`jf()[\]]/.test(char)) return 0.28
  if (/[tr-]/.test(char)) return 0.34
  if (/[mwMW@%]/.test(char)) return 0.85
  if (/[0-9]/.test(char)) return 0.56
  if (/[A-ZÄÖÜ]/.test(char)) return 0.68
  if (/[ßäöüa-z]/.test(char)) return 0.52
  return 0.6
}

export const approximateMeasure: Measure = (text, style) => {
  let width = 0
  for (const char of text) width += approxCharWidth(char)
  return Math.round(width * style.fontSize * 100) / 100
}

let customMeasure: Measure | null = null

/** Erlaubt Tests oder Anwendungen, die Messfunktion auszutauschen. */
export function setTextMeasure(measure: Measure | null): void {
  customMeasure = measure
}

export function measureText(text: string, style: TextStyle = DEFAULT_TEXT_STYLE): number {
  if (customMeasure) return customMeasure(text, style)
  const measured = browserMeasure(text, style)
  return measured === null ? approximateMeasure(text, style) : measured
}

function normalizePadding(padding: TextBoxOptions['padding']) {
  if (typeof padding === 'number' || padding === undefined) {
    const value = padding || 0
    return { top: value, right: value, bottom: value, left: value }
  }
  return { top: padding.top || 0, right: padding.right || 0, bottom: padding.bottom || 0, left: padding.left || 0 }
}

/** Bricht ein zu langes Wort hart um. */
function splitLongWord(word: string, maxWidth: number, style: TextStyle): string[] {
  const parts: string[] = []
  let current = ''
  for (const char of word) {
    const candidate = current + char
    if (current && measureText(candidate, style) > maxWidth) {
      parts.push(current)
      current = char
    } else {
      current = candidate
    }
  }
  if (current) parts.push(current)
  return parts
}

/** Zerlegt Text in Zeilen, die in die angegebene Breite passen. */
export function wrapText(text: string, maxWidth: number, style: TextStyle = DEFAULT_TEXT_STYLE): LaidOutLine[] {
  const lines: LaidOutLine[] = []
  const paragraphs = (text || '').split(/\r?\n/)
  for (const paragraph of paragraphs) {
    // Bindestriche bleiben am Wortende, damit dort umgebrochen werden kann.
    const words = paragraph.split(/(?<=-)|\s+/).filter((word) => word.length > 0)
    if (words.length === 0) {
      lines.push({ text: '', width: 0 })
      continue
    }
    let current = ''
    const flush = () => {
      if (current) lines.push({ text: current, width: measureText(current, style) })
      current = ''
    }
    for (const word of words) {
      const joiner = current && !current.endsWith('-') ? ' ' : ''
      const candidate = current + joiner + word
      if (measureText(candidate, style) <= maxWidth || !current) {
        if (!current && measureText(word, style) > maxWidth) {
          const pieces = splitLongWord(word, maxWidth, style)
          for (let i = 0; i < pieces.length - 1; i++) {
            lines.push({ text: pieces[i], width: measureText(pieces[i], style) })
          }
          current = pieces[pieces.length - 1] || ''
        } else {
          current = candidate
        }
      } else {
        flush()
        if (measureText(word, style) > maxWidth) {
          const pieces = splitLongWord(word, maxWidth, style)
          for (let i = 0; i < pieces.length - 1; i++) {
            lines.push({ text: pieces[i], width: measureText(pieces[i], style) })
          }
          current = pieces[pieces.length - 1] || ''
        } else {
          current = word
        }
      }
    }
    flush()
  }
  return lines
}

export function resolveStyle(style?: Partial<TextStyle>): TextStyle {
  return { ...DEFAULT_TEXT_STYLE, ...(style || {}) }
}

/** Berechnet Zeilen und Abmessungen für einen Text in einer Box. */
export function layoutText(text: string, options: TextBoxOptions): TextLayoutResult {
  const style = resolveStyle(options.style)
  const padding = normalizePadding(options.padding)
  const maxWidth = Math.max(1, options.box.width - padding.left - padding.right)
  const lines = wrapText(text, maxWidth, style)
  const lineHeight = style.fontSize * style.lineHeight
  const width = lines.reduce((max, line) => Math.max(max, line.width), 0)
  return { lines, width, height: lines.length * lineHeight }
}

/**
 * Erzeugt ein SVG-`<text>` mit `<tspan>`-Zeilen innerhalb einer Box.
 * Die Box beginnt bei (0, 0); der Aufrufer positioniert über `transform`.
 */
export function createTextElement(text: string, options: TextBoxOptions, className = 'djs-label'): SVGTextElement {
  const style = resolveStyle(options.style)
  const padding = normalizePadding(options.padding)
  const align = options.align || 'center-middle'
  const layout = layoutText(text, options)
  const lineHeight = style.fontSize * style.lineHeight

  const textElement = svgCreate('text') as SVGTextElement
  svgAttr(textElement, {
    class: className,
    'font-family': style.fontFamily,
    'font-size': String(style.fontSize),
    ...(style.fontWeight ? { 'font-weight': String(style.fontWeight) } : {}),
  })

  let y: number
  if (align === 'center-middle' || align === 'left-middle') {
    y = padding.top + (options.box.height - padding.top - padding.bottom - layout.height) / 2
  } else {
    y = padding.top
  }

  const innerWidth = options.box.width - padding.left - padding.right
  layout.lines.forEach((line) => {
    y += lineHeight
    const tspan = svgCreate('tspan') as SVGTSpanElement
    let x: number
    if (align === 'left-top' || align === 'left-middle') {
      x = padding.left
    } else {
      x = padding.left + (innerWidth - line.width) / 2
    }
    // Grundlinie etwas oberhalb der Zeilenunterkante.
    svgAttr(tspan, { x: String(round(x)), y: String(round(y - lineHeight * 0.22)) })
    tspan.textContent = line.text
    svgAppend(textElement, tspan)
  })

  return textElement
}

function round(value: number): number {
  return Math.round(value * 100) / 100
}
