/** Rendert ein Szenario mit Vue (`?fw=vue`) oder React (`?fw=react`) in `#buehne`. */
import '@auditcore/ui-core/style.css'
import { FaButton, FaTextField } from '@auditcore/ui'
import { createRoot } from 'react-dom/client'
import { createApp, h } from 'vue'
import { buttonCases, textFieldCases } from '../../ui-core/test/parity/cases-base'
import { Button, TextField } from '../src'

const params = new URLSearchParams(location.search)
const [art, nummer] = (params.get('fall') ?? 'schaltflaeche-0').split(/-(?=\d+$)/)
const index = Number(nummer)
const buehne = document.getElementById('buehne') as HTMLElement

const knopf = buttonCases[index]
const feld = textFieldCases[index]
if (!knopf && !feld) throw new Error(`unbekannter Fall: ${params.get('fall') ?? ''}`)

function vue(): void {
  const props = art === 'eingabefeld' ? feld?.props() : knopf?.props()
  createApp({ render: () => h(art === 'eingabefeld' ? FaTextField : FaButton, { ...props }) }).mount(buehne)
}

function react(): void {
  if (art === 'eingabefeld') {
    const { modelValue = '', ...rest } = feld?.props() ?? { label: '' }
    createRoot(buehne).render(<TextField {...rest} value={modelValue} onChange={() => undefined} />)
  } else {
    createRoot(buehne).render(<Button {...knopf?.props()} />)
  }
}

if (params.get('fw') === 'react') react()
else vue()
document.body.dataset.bereit = '1'
