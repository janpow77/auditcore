/**
 * Vite plugin for the self-contained bundles: moves the emitted CSS into the
 * JavaScript entry, which adds it once as `<style data-flowaudit-bpmn>` to the
 * document. No separate stylesheet, no CDN.
 */

import type { Plugin } from 'vite'

export function injectCss(): Plugin {
  return {
    name: 'flowaudit-inject-css',
    apply: 'build',
    enforce: 'post',
    generateBundle(_options, bundle) {
      const cssFiles = Object.values(bundle).filter((file) => file.type === 'asset' && file.fileName.endsWith('.css'))
      const css = cssFiles.map((file) => (file.type === 'asset' ? String(file.source) : '')).join('\n')
      for (const file of cssFiles) delete bundle[file.fileName]
      const entry = Object.values(bundle).find((file) => file.type === 'chunk' && file.isEntry)
      if (!css || !entry || entry.type !== 'chunk') return
      const code = `(()=>{if(typeof document==='undefined'||document.querySelector('style[data-flowaudit-bpmn]'))return;const s=document.createElement('style');s.setAttribute('data-flowaudit-bpmn','');s.textContent=${JSON.stringify(css)};document.head.appendChild(s)})();\n`
      entry.code = code + entry.code
    },
  }
}
