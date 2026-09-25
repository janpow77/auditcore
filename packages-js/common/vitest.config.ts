import { defineConfig } from 'vitest/config'

// Standard: Node ohne DOM (der Kern darf kein DOM brauchen); Browser-Helfer-Tests wählen
// happy-dom per Dateikommentar `@vitest-environment happy-dom`.
export default defineConfig({
  test: { environment: 'node', include: ['test/**/*.spec.ts'] },
})
