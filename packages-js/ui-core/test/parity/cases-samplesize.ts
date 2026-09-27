/**
 * Paritätsfälle von SampleSizePlanner (Vue `SampleSizePlanner` ↔ React
 * `FlowauditSampleSizePlanner`). Port mit Antworten des echten Python-Backends
 * (auditcore_sampling.web), synthetische Daten aus den Leitfaden-Beispielen.
 */
import type { SampleSizeRequest, SamplesizePort } from '../../src'
import { conservativeRequest, fakeSamplesizePort, stratifiedRequest } from '../samplesize/fake-port'
import type { ParityCase } from './cases'

export interface SamplesizeCaseProps {
  port?: SamplesizePort | null
  request?: SampleSizeRequest | null
  locale?: 'de' | 'en'
}

export { conservativeRequest, fakeSamplesizePort, stratifiedRequest }

export const samplesizeCases: ReadonlyArray<ParityCase<SamplesizeCaseProps>> = [
  {
    name: 'Katalog geladen, keine Methode vorgewählt',
    props: () => ({ port: fakeSamplesizePort() }),
    expect: {
      texts: ['Verfahren', 'MUS – konservativer Ansatz'],
      roles: [['combobox', 'Verfahren']],
      counts: { option: 9, '[data-testid="samplesize-calculate"]': 0 },
    },
  },
  {
    name: 'vorbelegt: MUS konservativ',
    props: () => ({ port: fakeSamplesizePort(), request: conservativeRequest }),
    expect: {
      texts: ['Faktorprofil', 'Wesentlichkeit (%)', 'EGESIF_16-0014-01, Abschn. 6.3.5.2'],
      roles: [['button', 'Umfang berechnen'], ['combobox', 'Konfidenzniveau'], ['textbox', 'Buchwert der Grundgesamtheit (BV, €)']],
      counts: { '[data-testid="samplesize-strata"]': 0, '[data-testid="samplesize-result"]': 0 },
    },
  },
  {
    name: 'vorbelegt: geschichtete Zufallsstichprobe mit Vollerhebung',
    props: () => ({ port: fakeSamplesizePort(), request: stratifiedRequest }),
    expect: {
      texts: ['Schichten', 'Endlichkeitskorrektur (Fußnote 25)'],
      roles: [['textbox', 'Name, Zeile 3'], ['checkbox', 'Vollerhebung, Zeile 3'], ['button', 'Schicht 1 entfernen']],
      counts: { '[data-testid="samplesize-strata"] tbody tr': 3 },
    },
  },
  {
    name: 'Fehler beim Laden, englisch',
    props: () => ({ port: fakeSamplesizePort('profiles', 'offline'), locale: 'en' }),
    expect: { texts: ['Request rejected: offline'], counts: { '[role="alert"]': 1, select: 0 } },
  },
]
