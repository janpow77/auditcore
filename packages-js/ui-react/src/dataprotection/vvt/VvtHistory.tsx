import type { VersionSummary } from '@auditcore/ui-core'
import { statusLabel, useDataProtectionText } from '../shared'

/** Fassungen des Verzeichnisses (wie VvtHistory.vue). */
export function VvtHistory({ versions = [] }: { versions?: readonly VersionSummary[] }) {
  const { t, when } = useDataProtectionText()
  const at = (value: string | null): string => when(value) || t('empty')
  return (
    <section className="fa-dataprotection__panel" data-testid="vvt-history" aria-label={t('history')}>
      <h3>{t('history')}</h3>
      <table className="fa-dataprotection__table">
        <thead>
          <tr>
            <th scope="col">{t('colVersion')}</th>
            <th scope="col">{t('colStatus')}</th>
            <th scope="col">{t('colCreated')}</th>
            <th scope="col">{t('colReleased')}</th>
            <th scope="col">{t('colActivities')}</th>
          </tr>
        </thead>
        <tbody>
          {versions.map((entry) => (
            <tr key={entry.version}>
              <td>{entry.version}</td>
              <td>{statusLabel(t, entry.status)}</td>
              <td>{`${entry.created_by}, ${at(entry.created_at)}`}</td>
              <td>{entry.released_by ? `${entry.released_by}, ${at(entry.released_at)}` : t('empty')}</td>
              <td>{entry.activities}</td>
            </tr>
          ))}
          {versions.length ? null : (
            <tr>
              <td colSpan={5} className="fa-dataprotection__muted">{t('noHistory')}</td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  )
}
