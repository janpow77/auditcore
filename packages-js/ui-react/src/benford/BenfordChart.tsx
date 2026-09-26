import { benfordBarTitle, benfordChartTitle, benfordTickText, chartGeometry, type BenfordTranslate, type Conformity, type Locale } from '@auditcore/ui-core'
import { classes, useElementId } from '../store'

export interface BenfordChartProps {
  conformity: Conformity
  testLabel: string
  t: BenfordTranslate
  locale: Locale
}

/** Diagramm beobachteter und erwarteter Anteile als SVG (wie `BenfordChart.vue`). */
export function BenfordChart({ conformity, testLabel, t, locale }: BenfordChartProps) {
  const id = useElementId('fa-benford-chart')
  const geometry = chartGeometry(conformity.rows)
  const { plot, box } = geometry
  const baseline = plot.y + plot.height
  return (
    <figure className="fa-benford__figure">
      <svg className="fa-benford__chart" viewBox={`0 0 ${box.width} ${box.height}`} role="img" aria-labelledby={`${id}-title`} data-testid="benford-chart">
        <title id={`${id}-title`}>{benfordChartTitle(conformity, testLabel, t)}</title>
        <g className="fa-benford__grid">
          {geometry.yTicks.map((tick) => (
            <g key={tick.value}>
              <line x1={plot.x} x2={plot.x + plot.width} y1={tick.y} y2={tick.y} />
              <text x={plot.x - 8} y={tick.y} textAnchor="end" dominantBaseline="middle">{benfordTickText(tick.value, geometry.tickDigits, locale)}</text>
            </g>
          ))}
        </g>
        <g>
          {geometry.bars.map((bar, index) => (
            <rect key={bar.digit} className={classes('fa-benford__bar', bar.exceeds && 'fa-benford__bar--exceeds')} data-digit={bar.digit} x={bar.x} y={bar.y} width={bar.width} height={bar.height} rx="2">
              <title>{benfordBarTitle(conformity, index, t, locale)}</title>
            </rect>
          ))}
        </g>
        <path className="fa-benford__expected" d={geometry.expectedPath} />
        {geometry.expected.map((point, index) => (
          <circle key={index} className="fa-benford__expected-dot" cx={point.x} cy={point.y} r={geometry.bars.length > 20 ? 1.8 : 3.5} />
        ))}
        <g className="fa-benford__axis">
          <line x1={plot.x} x2={plot.x + plot.width} y1={baseline} y2={baseline} />
          {geometry.xLabels.map((label) => <text key={label.digit} x={label.x} y={baseline + 18} textAnchor="middle">{label.digit}</text>)}
        </g>
      </svg>
      <figcaption className="fa-benford__legend">
        <span><i className="fa-benford__swatch" />{t('legendObserved')}</span>
        <span><i className="fa-benford__swatch fa-benford__swatch--exceeds" />{t('legendExceeds')}</span>
        <span><i className="fa-benford__swatch fa-benford__swatch--expected" />{t('legendExpected')}</span>
      </figcaption>
    </figure>
  )
}
