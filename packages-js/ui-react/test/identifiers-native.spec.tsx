import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { BATCH_CSV, batchAnswer, fakeIdentifiersPort, validAnswer } from '../../ui-core/test/identifiers/fake-port'
import { FlowauditIdentifierCheck } from '../src/identifiers/FlowauditIdentifierCheck'

const flush = () => act(() => new Promise<void>((resolve) => setTimeout(resolve, 0)))

afterEach(() => cleanup())

describe('FlowauditIdentifierCheck (nativ)', () => {
  it('prüft eine USt-IdNr. mit Land und meldet das Ergebnis', async () => {
    const port = fakeIdentifiersPort()
    const onIdentifierChecked = vi.fn()
    render(<FlowauditIdentifierCheck port={port} onIdentifierChecked={onIdentifierChecked} />)
    await flush()
    fireEvent.change(screen.getByTestId('ident-kind'), { target: { value: 'vat_id' } })
    fireEvent.change(screen.getByTestId('ident-value'), { target: { value: '136695976' } })
    fireEvent.change(screen.getByTestId('ident-country'), { target: { value: 'de' } })
    fireEvent.submit(screen.getByTestId('ident-check').closest('form') as HTMLFormElement)
    await flush()
    expect(port.calls.check).toEqual([{ kind: 'vat_id', value: '136695976', profile: 'strict', country: 'DE' }])
    expect(screen.getByTestId('ident-result').textContent).toContain('Die Kennung erfüllt alle Prüfungen des Profils „Streng (Standard)“.')
    expect(onIdentifierChecked).toHaveBeenCalledWith(validAnswer.result)
  })

  it('verlangt eine Kennungsart und ein Profil', async () => {
    const port = fakeIdentifiersPort()
    render(<FlowauditIdentifierCheck port={port} />)
    await flush()
    fireEvent.change(screen.getByTestId('ident-kind'), { target: { value: '' } })
    fireEvent.submit(screen.getByTestId('ident-check').closest('form') as HTMLFormElement)
    await flush()
    expect(screen.getByRole('alert').textContent).toBe('Kennungsart wählen.')
    expect(port.calls.check).toEqual([])
  })

  it('prüft eine Tabelle als Stapel mit fester Art und filtert Auffälligkeiten', async () => {
    const port = fakeIdentifiersPort()
    const onBatchChecked = vi.fn()
    render(<FlowauditIdentifierCheck port={port} onBatchChecked={onBatchChecked} />)
    await flush()
    fireEvent.change(screen.getByTestId('ident-file'), { target: { files: [new File([BATCH_CSV], 'kennungen.csv')] } })
    await flush()
    await flush()
    fireEvent.change(screen.getByTestId('ident-col-value'), { target: { value: '2' } })
    fireEvent.submit(screen.getByTestId('ident-batch-run').closest('form') as HTMLFormElement)
    await flush()
    expect((port.calls.batch[0] as { items: { kind: string; ref: string }[] }).items.map((item) => [item.ref, item.kind])[0]).toEqual(['2', 'iban'])
    expect(onBatchChecked).toHaveBeenCalledWith(batchAnswer)
    fireEvent.click(screen.getByTestId('ident-only-issues'))
    expect(document.querySelectorAll('.fa-ident__table tbody tr')).toHaveLength(3)
  })

  it('meldet Fehler des Ports', async () => {
    const onError = vi.fn()
    render(<FlowauditIdentifierCheck port={fakeIdentifiersPort('catalogue')} onError={onError} />)
    await flush()
    expect(onError).toHaveBeenCalledWith('Dienst nicht erreichbar')
    expect(screen.getByRole('alert').textContent).toContain('Dienst nicht erreichbar')
  })
})
