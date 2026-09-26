/** Keyboard shortcut help (declarative table). */

import { SHORTCUTS } from '@flowaudit/bpmn-flowaudit/ui'
import { BaseDialog } from '../base/BaseDialog'
import { useI18n } from '../i18n'

export function ShortcutHelp({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const { t } = useI18n()
  return (
    <BaseDialog open={open} title={t('shortcuts.title')} width="480px" onOpenChange={onOpenChange}>
      <table className="fa-table">
        <tbody>
          {SHORTCUTS.map(([keys, label]) => (
            <tr key={label}>
              <td className="fa-shortcut__keys">
                {keys.map((key, index) => <kbd key={index} className="fa-kbd">{key.startsWith('@') ? t(`key.${key.slice(1)}`) : key}</kbd>)}
              </td>
              <td>{t(label)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </BaseDialog>
  )
}
