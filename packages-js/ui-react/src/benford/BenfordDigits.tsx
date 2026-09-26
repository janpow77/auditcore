import { benfordDigitColumns, benfordDigitRows, type BenfordTranslate, type Conformity, type Locale } from '@flowaudit/ui-core'
import { FlowauditTable } from '../table/FlowauditTable'

export interface BenfordDigitsProps {
  conformity: Conformity
  t: BenfordTranslate
  locale: Locale
  /** Sprache der Tabelle wie in Vue (Prop der Hauptkomponente). */
  tableLocale?: Locale
}

/** Zifferntabelle, bei bis zu zehn Ziffern aufgeklappt (wie `BenfordDigits.vue`). */
export function BenfordDigits({ conformity, t, locale, tableLocale }: BenfordDigitsProps) {
  return (
    <details className="fa-benford__digits" open={conformity.rows.length <= 10}>
      <summary>{t('table')}</summary>
      <FlowauditTable
        columns={benfordDigitColumns(t, locale)}
        rows={benfordDigitRows(conformity)}
        caption={t('table')}
        locale={tableLocale}
        testId="benford-table"
        renderCell={(column, _row, value) => (column.key === 'exceeds' ? (value === true ? <span className="fa-benford__flag">{t('yes')}</span> : <></>) : undefined)}
      />
    </details>
  )
}
