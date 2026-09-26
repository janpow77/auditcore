/** Legal bases of the selected element. */

import { useEditorContext, useSelectionState } from '../../context'
import { LegalBasisEditor } from '../legal/LegalBasisEditor'

export function LegalTab() {
  const { selection, ports, profile, readonly } = useEditorContext()
  const { extensions } = useSelectionState()
  return <LegalBasisEditor items={extensions.legalBases} port={ports.legalSearch} profileId={profile()?.id} disabled={readonly()} onUpdate={(legalBases) => selection.write({ legalBases })} />
}
