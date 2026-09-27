import type { ChangeEvent } from 'react'
import { runnerAbschnitte, runnerNurLesen, type RunnerController, type RunnerFeld } from '@auditcore/ui-core'
import { classes } from '../../store'
import type { BereichProps } from './types'

function Feld({ feld, uid, nurLesen, controller }: { feld: RunnerFeld; uid: string; nurLesen: boolean; controller: RunnerController }) {
  const id = `${uid}-${feld.id}`
  const fehler = feld.fehler ? { 'aria-invalid': 'true' as const, 'aria-describedby': `${id}-fehler` } : {}
  const eingabe = (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    controller.eingabe(feld.pfad, feld.art, feld.art === 'schalter' ? (event.target as HTMLInputElement).checked : event.target.value)
  return (
    <div className={classes('fa-runner__feld', feld.art === 'schalter' && 'fa-runner__feld--schalter')}>
      {feld.art === 'schalter' ? (
        <>
          <input id={id} type="checkbox" checked={feld.an} disabled={nurLesen} {...fehler} onChange={eingabe} />
          <label htmlFor={id}>{feld.label}</label>
        </>
      ) : (
        <>
          <label htmlFor={id}>{feld.label}</label>
          {feld.art === 'auswahl' ? (
            <select id={id} className="fa-runner__eingabe" value={feld.wert} disabled={nurLesen} {...fehler} onChange={eingabe}>
              {feld.optionen.map((option) => <option key={option.wert} value={option.wert}>{option.label}</option>)}
            </select>
          ) : (
            <input
              id={id}
              className="fa-runner__eingabe"
              type={feld.art === 'zahl' ? 'number' : 'text'}
              step={feld.art === 'zahl' ? feld.schritt : undefined}
              value={feld.wert}
              disabled={nurLesen}
              {...fehler}
              onChange={eingabe}
            />
          )}
        </>
      )}
      {feld.fehler ? <p id={`${id}-fehler`} className="fa-runner__feldfehler">{feld.fehler}</p> : null}
    </div>
  )
}

/** Formularabschnitte der Einstellungen (wie `RunnerFields.vue`). */
export function Felder({ state, controller, t, uid }: BereichProps & { uid: string }) {
  const nurLesen = runnerNurLesen(state)
  return (
    <>
      {runnerAbschnitte(state, t).map((abschnitt) => (
        <fieldset key={abschnitt.id} className="fa-runner__abschnitt">
          <legend>{abschnitt.titel}</legend>
          {abschnitt.felder.map((feld) => <Feld key={feld.id} feld={feld} uid={uid} nurLesen={nurLesen} controller={controller} />)}
        </fieldset>
      ))}
    </>
  )
}
