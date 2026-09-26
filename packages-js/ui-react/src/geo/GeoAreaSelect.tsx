import { displayName } from '@flowaudit/ui-core'
import { useGeo } from './context'

export function GeoAreaSelect({ testid }: { testid: string }) {
  const { state, selection, controller, t } = useGeo()
  return (
    <label className="fa-geo__field fa-geo__grow">
      <span className="fa-geo__label">{t('area')}</span>
      <select className="fa-geo__input" data-testid={testid} value={state.areaId ?? ''} onChange={(event) => controller.selectArea(event.target.value || null)}>
        <option value="">{t('choose')}</option>
        {selection.areas.map((area) => (
          <option key={area.id} value={area.id}>{displayName(area)}</option>
        ))}
      </select>
    </label>
  )
}
