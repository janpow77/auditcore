import { runnerNurLesen, runnerPrioritaetZeilen, runnerWeichtZuerstText } from '@auditcore/ui-core'
import { Button } from '../../base/Button'
import type { BereichProps } from './types'

/** Rangfolge der Klassen und Prüfprofile mit Vorschau „weicht zuerst“ (wie `RunnerPriorityList.vue`). */
export function Prioritaeten({ state, controller, t, uid }: BereichProps & { uid: string }) {
  const zeilen = runnerPrioritaetZeilen(state, t)
  const weichtZuerst = runnerWeichtZuerstText(state, t)
  const nurLesen = runnerNurLesen(state)
  return (
    <>
      <p className="fa-runner__muted">{t('prioritaetenHinweis')}</p>
      {!zeilen.length ? <p className="fa-runner__muted">{t('keinePrioritaeten')}</p> : (
        <ol className="fa-runner__prioritaeten">
          {zeilen.map((zeile) => (
            <li key={zeile.klasse} className="fa-runner__prioritaet">
              <span className="fa-runner__rang">{zeile.rangText}</span>
              <strong className="fa-runner__klasse">{zeile.klasse}</strong>
              <Button size="sm" icon="chevron-up" iconOnly label={zeile.hoch} disabled={nurLesen || zeile.ersteZeile} onClick={() => controller.verschiebe(zeile.index, -1)} />
              <Button size="sm" icon="chevron-down" iconOnly label={zeile.runter} disabled={nurLesen || zeile.letzteZeile} onClick={() => controller.verschiebe(zeile.index, 1)} />
              <span className="fa-runner__feld fa-runner__feld--schalter">
                <input id={`${uid}-prio-${zeile.index}-verdraengbar`} type="checkbox" checked={zeile.verdraengbar} disabled={nurLesen} onChange={(event) => controller.prioritaet(zeile.index, { verdraengbar: event.target.checked })} />
                <label htmlFor={`${uid}-prio-${zeile.index}-verdraengbar`}>{t('verdraengbar')}</label>
              </span>
              <span className="fa-runner__feld fa-runner__feld--schalter">
                <label htmlFor={`${uid}-prio-${zeile.index}-min`}>{t('mindestens')}</label>
                <input id={`${uid}-prio-${zeile.index}-min`} className="fa-runner__eingabe fa-runner__schmal" type="number" min="0" value={String(zeile.min)} disabled={nurLesen} onChange={(event) => controller.prioritaet(zeile.index, { min: Number(event.target.value) || 0 })} />
              </span>
            </li>
          ))}
        </ol>
      )}
      {weichtZuerst ? <p className="fa-runner__muted">{weichtZuerst}</p> : null}
    </>
  )
}
