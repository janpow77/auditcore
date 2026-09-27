import { runnerVorschau, runnerWert, type RunnerVorschau } from '@auditcore/ui-core'
import { Badge } from '../../base/Badge'
import { Button } from '../../base/Button'
import type { BereichProps } from './types'

function Konflikt({ state, controller, t }: BereichProps) {
  const konflikt = state.konflikt
  if (!konflikt) return null
  const quelle = String(runnerWert(konflikt.gespeichert.profil, ['aenderung', 'quelle']) ?? '–')
  return (
    <section className="fa-runner__konflikt" role="alert">
      <p>{t('konflikt', { meldung: konflikt.meldung })}</p>
      <table className="fa-runner__tabelle">
        <thead>
          <tr>
            <th scope="col">{t('konfliktFeld')}</th>
            <th scope="col">{t('konfliktEntwurf')}</th>
            <th scope="col">{t('konfliktGespeichert', { quelle })}</th>
          </tr>
        </thead>
        <tbody>
          {konflikt.unterschiede.map((unterschied) => (
            <tr key={unterschied.pfad}>
              <th scope="row"><code>{unterschied.pfad}</code></th>
              <td><code>{unterschied.entwurf}</code></td>
              <td><code>{unterschied.gespeichert}</code></td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="fa-runner__aktionen">
        <Button onClick={() => controller.gespeichertUebernehmen()}>{t('gespeichertUebernehmen')}</Button>
        <Button variant="primary" onClick={() => void controller.entwurfTrotzdemAnwenden()}>{t('entwurfAnwenden')}</Button>
      </div>
    </section>
  )
}

function Vorschau({ vorschau, t }: { vorschau: RunnerVorschau; t: BereichProps['t'] }) {
  return (
    <section className="fa-runner__vorschau" aria-label={t('vorschau')}>
      <h3 className="fa-runner__zwischen">{t('vorschau')} <Badge tone={vorschau.gueltig ? 'success' : 'danger'}>{vorschau.gueltig ? t('gueltig') : t('ungueltig')}</Badge></h3>
      {!vorschau.aenderungen.length ? <p className="fa-runner__muted">{t('keineAenderung')}</p> : null}
      {vorschau.aenderungen.map((aenderung) => (
        <details key={aenderung.datei} className="fa-runner__diff">
          <summary>{aenderung.datei}</summary>
          <pre>{aenderung.diff}</pre>
        </details>
      ))}
      {vorschau.schritte.length ? (
        <>
          <h4 className="fa-runner__zwischen">{t('schritte')}</h4>
          <ol className="fa-runner__schritte">
            {vorschau.schritte.map((schritt) => <li key={schritt}>{schritt}</li>)}
          </ol>
        </>
      ) : null}
      {vorschau.rootBefehl ? (
        <>
          <p className="fa-runner__muted">{t('rootBefehl')}</p>
          <pre className="fa-runner__befehl"><code>{vorschau.rootBefehl}</code></pre>
        </>
      ) : null}
    </section>
  )
}

/** Ergebnis nach Prüfen/Anwenden: Konflikt mit beiden Ständen oder Vorschau (wie `RunnerReview.vue`). */
export function Pruefung(props: BereichProps) {
  const vorschau = runnerVorschau(props.state)
  return (
    <>
      <Konflikt {...props} />
      {vorschau ? <Vorschau vorschau={vorschau} t={props.t} /> : null}
    </>
  )
}
