import { useState, type ChangeEvent, type FormEvent } from 'react'
import { Button } from '../base/Button'
import { useElementId } from '../store'
import { useGeo } from './context'

function PackageResultView() {
  const { state, t } = useGeo()
  const result = state.gpkgResult
  if (!result) return null
  return (
    <div className="fa-geo__stack" aria-live="polite" data-testid="geo-gpkg-result">
      <p className="fa-geo__summary">
        {t('gpkgResult', { count: result.flaechen.length, table: result.tabelle, srs: result.srs_id })}{' '}
        {result.umgerechnet ? <span className="fa-geo__muted">({t('gpkgConverted')})</span> : null}
      </p>
      {result.abgeschnitten ? <p className="fa-geo__notice">{t('gpkgTruncated')}</p> : null}
      {result.fehler.length ? (
        <details className="fa-geo__details">
          <summary>{t('gpkgErrors', { count: result.fehler.length })}</summary>
          <ul className="fa-geo__list">{result.fehler.map((entry) => <li key={entry.id}>{`${entry.id}: ${entry.meldung}`}</li>)}</ul>
        </details>
      ) : null}
    </div>
  )
}

function Sources({ names }: { names: readonly string[] }) {
  const { state, controller, t } = useGeo()
  const [source, setSource] = useState('')
  if (!names.length) return null
  const load = (event: FormEvent): void => {
    event.preventDefault()
    if (source) void controller.loadSource(source)
  }
  return (
    <form className="fa-geo__row" noValidate onSubmit={load}>
      <label className="fa-geo__field fa-geo__grow">
        <span className="fa-geo__label">{t('gpkgSource')}</span>
        <select className="fa-geo__input" data-testid="geo-gpkg-source" value={source} onChange={(event) => setSource(event.target.value)}>
          <option value="">{t('choose')}</option>
          {names.map((name) => <option key={name} value={name}>{name}</option>)}
        </select>
      </label>
      <Button type="submit" disabled={!source} loading={state.busy === 'gpkg'} testId="geo-gpkg-load">{t('gpkgLoad')}</Button>
    </form>
  )
}

/** GeoPackage hochladen oder aus einer Serverquelle laden (nur, wenn der Port es anbietet). */
export function GeoPackageLoader({ upload, sources }: { upload: boolean; sources: boolean }) {
  const { state, controller, t } = useGeo()
  const id = useElementId('fa-geo-gpkg')
  const onFile = async (event: ChangeEvent<HTMLInputElement>): Promise<void> => {
    const input = event.target
    const file = input.files?.[0]
    if (file) await controller.loadFile(file)
    input.value = ''
  }
  return (
    <section className="fa-geo__card" aria-labelledby={`${id}-h`}>
      <h3 id={`${id}-h`} className="fa-geo__heading">{t('gpkg')}</h3>
      {upload ? (
        <label className="fa-geo__field">
          <span className="fa-geo__label">{t('gpkgFile')}</span>
          <input className="fa-geo__file" type="file" accept=".gpkg,application/geopackage+sqlite3" data-testid="geo-gpkg-file" onChange={(event) => void onFile(event)} />
        </label>
      ) : null}
      <Sources names={sources ? state.catalogue?.gpkg_quellen ?? [] : []} />
      <PackageResultView />
    </section>
  )
}
