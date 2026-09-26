import { describe, it } from 'vitest'
import VueBaseDialog from '../../../bpmn-vue/src/components/base/BaseDialog.vue'
import VueFaIcon from '../../../bpmn-vue/src/components/base/FaIcon.vue'
import { DIALOG_BASE_CASES, ICON_CASES } from '../../../bpmn-flowaudit/test/parity/cases-base'
import { BaseDialog } from '../../src/base/BaseDialog'
import { FaIcon } from '../../src/base/FaIcon'
import { expectParity, renderBoth } from './setup'

describe('parity: FaIcon', () => {
  for (const item of ICON_CASES) {
    it(item.name, async () => {
      const props = item.props()
      expectParity(await renderBoth(VueFaIcon, props, <FaIcon {...props} />), item.expect)
    })
  }
})

describe('parity: BaseDialog', () => {
  for (const item of DIALOG_BASE_CASES) {
    it(item.name, async () => {
      const props = item.props()
      expectParity(await renderBoth(VueBaseDialog, props, <BaseDialog {...props} />), item.expect)
    })
  }
})
