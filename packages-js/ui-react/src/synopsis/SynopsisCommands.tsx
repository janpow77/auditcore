import { Fragment } from 'react'
import type { SynopsisTranslate, SynopsisView } from '@flowaudit/ui-core'

function Consolidated({ view, t }: { view: SynopsisView; t: SynopsisTranslate }) {
  return (
    <details className="fa-synopsis-commands fa-synopsis-commands--consolidated">
      <summary>{t('consolidated')}</summary>
      <dl>
        {view.consolidated.map((entry) => (
          <Fragment key={`${entry.section}-${entry.paragraph}-${entry.inserted}`}>
            <dt>
              {t('consolidatedEntry', { section: entry.section, paragraph: entry.paragraph })}{' '}
              {entry.repealed ? <span>{t('repealed')}</span> : entry.inserted ? <span>{t('inserted')}</span> : null}
            </dt>
            <dd className={entry.repealed ? 'fa-synopsis-commands__repealed' : undefined}>{entry.text}</dd>
          </Fragment>
        ))}
      </dl>
    </details>
  )
}

/** Gesetzessynopse: offene Änderungsbefehle und konsolidierte Arbeitsfassung. */
export function SynopsisCommands({ view, t }: { view: SynopsisView; t: SynopsisTranslate }) {
  return (
    <>
      {view.openCommands.length ? (
        <section className="fa-synopsis-commands" aria-label={t('openCommands')}>
          <h3>{t('openCommands')}</h3>
          <ol>
            {view.openCommands.map((command) => <li key={command}>{command}</li>)}
          </ol>
        </section>
      ) : null}
      {view.consolidated.length ? <Consolidated view={view} t={t} /> : null}
    </>
  )
}
