import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// Einmal je Anwendung: Designtoken (--fa-*), Hell-/Dunkelmodus und Komponentenstile.
import '@auditcore/ui-core/style.css'
import { App } from './App'

const root = document.getElementById('root')
if (!root) throw new Error('#root fehlt')
createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
