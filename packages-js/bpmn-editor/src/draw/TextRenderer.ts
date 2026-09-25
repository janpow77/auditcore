/**
 * Dienst `textRenderer`: Textsatz für Beschriftungen und Maße externer
 * Beschriftungen. Kapselt die eigene Textsatz-Logik (TextLayout).
 */

import { createTextElement, layoutText, type TextBoxOptions } from './TextLayout'
import { getExternalLabelSize, EXTERNAL_LABEL_FONT_SIZE } from '../util/LabelUtil'

export default class TextRenderer {
  static $inject: string[] = []

  createText(text: string, options: TextBoxOptions): SVGTextElement {
    return createTextElement(text, options)
  }

  getDimensions(text: string, options: TextBoxOptions): { width: number; height: number } {
    const layout = layoutText(text, options)
    return { width: layout.width, height: layout.height }
  }

  getExternalLabelSize(text: string): { width: number; height: number } {
    return getExternalLabelSize(text)
  }

  getExternalStyle(): { fontSize: number } {
    return { fontSize: EXTERNAL_LABEL_FONT_SIZE }
  }

  getDefaultStyle(): { fontSize: number } {
    return { fontSize: 12 }
  }
}
