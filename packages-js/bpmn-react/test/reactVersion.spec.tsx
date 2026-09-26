import { version } from 'react'
import { version as domVersion } from 'react-dom'
import { describe, expect, it } from 'vitest'

describe('React under test', () => {
  it('is React 19 by default and React 18 with REACT_DIR (npm run test:react18)', () => {
    const major = process.env.REACT_DIR ? '18' : '19'
    expect(version.split('.')[0]).toBe(major)
    expect(domVersion).toBe(version)
  })
})
