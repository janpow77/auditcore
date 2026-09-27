import { runnerHardware, runnerHatWarteschlange, runnerKlassenZeilen, runnerUeberblick } from '@auditcore/ui-core'
import { Badge } from '../../base/Badge'
import { Button } from '../../base/Button'
import type { BereichProps } from './types'

/** Bereich „Status“: Überblick, Klassen, Hardware (wie `RunnerStatusPanel.vue`). */
export function StatusBereich({ state, controller, t }: BereichProps) {
  const klassen = runnerKlassenZeilen(state.status)
  const warteschlange = runnerHatWarteschlange(state.status)
  return (
    <>
      {state.status ? (
        <>
          <h3 className="fa-runner__zwischen">{t('ueberblick')}</h3>
          <dl className="fa-runner__daten">
            {runnerUeberblick(state.status, t).map((eintrag) => <div key={eintrag.label} className="fa-runner__datum"><dt>{eintrag.label}</dt><dd>{eintrag.wert}</dd></div>)}
          </dl>
          {klassen.length ? (
            <table className="fa-runner__tabelle">
              <caption>{t('klassen')}</caption>
              <thead>
                <tr>
                  <th scope="col">{t('spalteKlasse')}</th>
                  <th scope="col">{t('spalteSoll')}</th>
                  <th scope="col">{t('spalteMax')}</th>
                  <th scope="col">{t('spalteInstanzen')}</th>
                  <th scope="col">{t('spalteRegistriert')}</th>
                  <th scope="col">{t('spalteBelegt')}</th>
                  {warteschlange ? <th scope="col">{t('spalteWarteschlange')}</th> : null}
                  <th scope="col">{t('spalteGruende')}</th>
                </tr>
              </thead>
              <tbody>
                {klassen.map((zeile) => (
                  <tr key={zeile.name}>
                    <th scope="row">{zeile.name} {zeile.aktiv ? null : <Badge>{t('inaktiv')}</Badge>}</th>
                    <td>{zeile.soll}</td>
                    <td>{zeile.max}</td>
                    <td>{zeile.instanzen}</td>
                    <td>{zeile.registriert}</td>
                    <td>{zeile.belegt}</td>
                    {warteschlange ? <td>{zeile.warteschlange}</td> : null}
                    <td>{zeile.gruende}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="fa-runner__muted">{t('keineKlassen')}</p>}
          <h3 className="fa-runner__zwischen">{t('hardware')}</h3>
          <dl className="fa-runner__daten">
            {runnerHardware(state.status.hardware).map((eintrag) => <div key={eintrag.label} className="fa-runner__datum"><dt>{eintrag.label}</dt><dd>{eintrag.wert}</dd></div>)}
          </dl>
        </>
      ) : null}
      <div className="fa-runner__aktionen">
        <Button icon="clock" loading={state.busy === 'load'} onClick={() => void controller.load()}>{t('refresh')}</Button>
      </div>
    </>
  )
}
