import { runnerNeueKlasse, runnerNurLesen, type RunnerController, type RunnerKlassenName } from '@auditcore/ui-core'
import { Button } from '../../base/Button'
import type { BereichProps } from './types'

/** Name einer Runner-Klasse ändern (wie `RunnerClassName.vue`). */
export function KlassenName({ klasse, controller, t, uid, nurLesen }: { klasse: RunnerKlassenName; controller: RunnerController; t: BereichProps['t']; uid: string; nurLesen: boolean }) {
  const id = `${uid}-klasse-${klasse.alt}-name`
  const fehler = klasse.fehler ? { 'aria-invalid': 'true' as const, 'aria-describedby': `${id}-fehler` } : {}
  return (
    <div className="fa-runner__feld fa-runner__klassenname">
      <label htmlFor={id}>{t('klasseName')}</label>
      <span className="fa-runner__aktionen">
        <input id={id} className="fa-runner__eingabe" type="text" maxLength={31} value={klasse.wert} disabled={nurLesen} {...fehler} onChange={(event) => controller.klassenNameEingabe(klasse.alt, event.target.value)} />
        <Button size="sm" disabled={nurLesen || !klasse.geaendert} onClick={() => controller.klasseUmbenennen(klasse.alt)}>{t('umbenennen')}</Button>
      </span>
      {klasse.fehler ? <p id={`${id}-fehler`} className="fa-runner__feldfehler">{klasse.fehler}</p> : null}
    </div>
  )
}

/** Neue Runner-Klasse anlegen (wie `RunnerNewClass.vue`). */
export function NeueKlasse({ state, controller, t, uid }: BereichProps & { uid: string }) {
  const neu = runnerNeueKlasse(state, t)
  const nurLesen = runnerNurLesen(state)
  const id = `${uid}-neue-klasse`
  const fehler = neu.fehler ? { 'aria-invalid': 'true' as const, 'aria-describedby': `${id}-fehler` } : {}
  return (
    <fieldset className="fa-runner__abschnitt">
      <legend>{t('neueKlasse')}</legend>
      <div className="fa-runner__feld fa-runner__klassenname">
        <label htmlFor={id}>{t('klasseName')}</label>
        <span className="fa-runner__aktionen">
          <input id={id} className="fa-runner__eingabe" type="text" maxLength={31} value={neu.wert} disabled={nurLesen} {...fehler} onChange={(event) => controller.neueKlasseEingabe(event.target.value)} />
          <Button size="sm" icon="plus" disabled={nurLesen || !neu.moeglich} onClick={() => controller.klasseHinzufuegen()}>{t('hinzufuegen')}</Button>
        </span>
        {neu.fehler ? <p id={`${id}-fehler`} className="fa-runner__feldfehler">{neu.fehler}</p> : null}
      </div>
    </fieldset>
  )
}
