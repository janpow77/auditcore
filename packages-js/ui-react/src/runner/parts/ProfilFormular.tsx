import { runnerIstGeaendert, runnerNurLesen, runnerProbleme } from '@auditcore/ui-core'
import { Badge } from '../../base/Badge'
import { Button } from '../../base/Button'
import { Felder } from './Felder'
import { Prioritaeten } from './Prioritaeten'
import { Pruefung } from './Pruefung'
import type { BereichProps } from './types'

/** Formular der Bereiche „Einstellungen“ und „Prioritäten“ (wie `RunnerProfileForm.vue`). */
export function ProfilFormular(props: BereichProps & { uid: string }) {
  const { state, controller, t } = props
  const probleme = runnerProbleme(state)
  const nurLesen = runnerNurLesen(state)
  const geaendert = runnerIstGeaendert(state)
  return (
    <form className="fa-runner__formular" noValidate onSubmit={(event) => { event.preventDefault(); void controller.pruefen() }}>
      {probleme.length ? (
        <ul className="fa-runner__probleme" aria-label={t('probleme')}>
          {probleme.map((problem) => <li key={`${problem.feld}-${problem.meldung}`}>{problem.feld}: {problem.meldung}</li>)}
        </ul>
      ) : null}
      {state.ansicht === 'einstellungen' ? <Felder {...props} /> : <Prioritaeten {...props} />}
      <div className="fa-runner__aktionen">
        <Button type="submit" disabled={nurLesen} loading={state.busy === 'pruefen'}>{t('pruefen')}</Button>
        <Button variant="primary" disabled={nurLesen || !geaendert} loading={state.busy === 'anwenden'} onClick={() => void controller.anwenden()}>{t('anwenden')}</Button>
        <Button disabled={!geaendert} onClick={() => controller.verwerfen()}>{t('verwerfen')}</Button>
        {geaendert ? <Badge tone="warning">{t('ungespeichert')}</Badge> : null}
      </div>
      <Pruefung state={state} controller={controller} t={t} />
    </form>
  )
}
