import { effectScope } from 'vue'
import { describe, expect, it } from 'vitest'
import { applyTheme, readTheme, resolvedTheme, useTheme } from '../src'

describe('Theme', () => {
  it('setzt und liest das Farbschema am Element', () => {
    const element = document.createElement('div')
    expect(readTheme(element)).toBe('system')
    applyTheme('dark', element)
    expect(element.getAttribute('data-fa-theme')).toBe('dark')
    expect(resolvedTheme(element)).toBe('dark')
    applyTheme('system', element)
    expect(element.hasAttribute('data-fa-theme')).toBe(false)
  })

  it('schaltet über das Composable um', () => {
    const element = document.createElement('div')
    const scope = effectScope()
    scope.run(() => {
      const theme = useTheme(element)
      theme.setMode('light')
      theme.toggle()
      expect(theme.mode.value).toBe('dark')
      expect(element.getAttribute('data-fa-theme')).toBe('dark')
    })
    scope.stop()
  })
})
