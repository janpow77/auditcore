import { runnerNurLesen, runnerWerkzeugeGeaendert, runnerWerkzeugGruppen } from '@auditcore/ui-core'
import { Button } from '../../base/Button'
import type { BereichProps } from './types'

/** Bereich „Werkzeuge“ (wie `RunnerToolsPanel.vue`). */
export function WerkzeugBereich({ state, controller, t }: BereichProps) {
  const nurLesen = runnerNurLesen(state)
  const gruppen = runnerWerkzeugGruppen(state, t)
  return (
    <>
      {!gruppen.length ? <p className="fa-runner__muted">{t('keineWerkzeuge')}</p> : null}
      {gruppen.map((gruppe) => (
        <table key={gruppe.profil} className="fa-runner__tabelle">
          <caption>{gruppe.titel}</caption>
          <thead>
            <tr>
              <th scope="col">{t('spalteWerkzeug')}</th>
              <th scope="col">{t('spalteBereich')}</th>
              <th scope="col">{t('spalteImage')}</th>
              <th scope="col">{t('spalteAktiv')}</th>
              <th scope="col">{t('spalteZeitlimit')}</th>
              <th scope="col">{t('spaltePrioritaet')}</th>
            </tr>
          </thead>
          <tbody>
            {gruppe.zeilen.map((zeile) => (
              <tr key={zeile.id}>
                <th scope="row">{zeile.werkzeug}</th>
                <td>{zeile.bereich}</td>
                <td>{zeile.imImage}</td>
                <td><input type="checkbox" checked={zeile.aktiv} disabled={nurLesen} aria-label={`${t('spalteAktiv')}: ${zeile.werkzeug}`} onChange={(event) => controller.werkzeug(gruppe.profil, zeile.werkzeug, { aktiv: event.target.checked })} /></td>
                <td><input className="fa-runner__eingabe fa-runner__schmal" type="number" min="1" value={zeile.zeitlimit} disabled={nurLesen} aria-label={`${t('spalteZeitlimit')}: ${zeile.werkzeug}`} onChange={(event) => controller.werkzeugZahl(gruppe.profil, zeile.werkzeug, 'zeitlimit_s', event.target.value)} /></td>
                <td><input className="fa-runner__eingabe fa-runner__schmal" type="number" min="0" value={zeile.prioritaet} disabled={nurLesen} aria-label={`${t('spaltePrioritaet')}: ${zeile.werkzeug}`} onChange={(event) => controller.werkzeugZahl(gruppe.profil, zeile.werkzeug, 'prioritaet', event.target.value)} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      ))}
      <div className="fa-runner__aktionen">
        <Button variant="primary" disabled={nurLesen || !runnerWerkzeugeGeaendert(state)} loading={state.busy === 'werkzeuge'} onClick={() => void controller.werkzeugeSpeichern()}>{t('speichern')}</Button>
      </div>
    </>
  )
}
