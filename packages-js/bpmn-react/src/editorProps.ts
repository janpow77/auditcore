/** Props and ref handle of the React `FlowauditEditor` (same contract as the Vue component). */

import type { Approval, Comment, DiagramInfo, KeyKind, PaletteColor, ProfileData, ProfileSummary, RoleAlias, ValidationPort } from '@flowaudit/bpmn-flowaudit'
import type { CompareSource, EditorCore, EditorFactory, EditorPorts, Locale, Theme, ToolbarAction, ValidationCore } from '@flowaudit/bpmn-flowaudit/ui'

export interface FlowauditEditorProps {
  /** BPMN XML (controlled; changes are reported through `onXmlChange`). */
  xml: string
  name?: string
  diagramId?: string
  profile?: ProfileData | null
  profiles?: ProfileSummary[]
  ports?: EditorPorts & { validation?: ValidationPort }
  locale?: Locale
  readonly?: boolean
  /** Approved diagrams are read-only (default on). */
  lockApproved?: boolean
  comments?: Comment[]
  approvals?: Approval[]
  author?: string
  compareSources?: CompareSource[]
  palette?: readonly PaletteColor[]
  roleAliases?: RoleAlias[]
  replacements?: Record<string, string>
  hiddenActions?: ToolbarAction[]
  saving?: boolean
  editorFactory?: EditorFactory
  theme?: Theme
  className?: string
  /** Vue `update:xml`. */
  onXmlChange?: (xml: string) => void
  /** Vue `update:name`. */
  onNameChange?: (name: string) => void
  /** Vue `update:comments`. */
  onCommentsChange?: (comments: Comment[]) => void
  onSave?: (payload: { xml: string; info: DiagramInfo | null }) => void
  onNew?: () => void
  onAnalysis?: () => void
  onShare?: () => void
  onExportExcel?: () => void
  onApprove?: (payload: { xml: string; info: DiagramInfo }) => void
  onSelectionChange?: (elementId: string | null) => void
  onError?: (message: string) => void
  onReady?: () => void
  onInfoChange?: (info: DiagramInfo | null) => void
}

/** Methods available through the ref (Vue: `defineExpose`). */
export interface FlowauditEditorHandle {
  getXml(): Promise<string | undefined>
  getSvg(): Promise<string | undefined>
  select(id: string): boolean
  highlightKey(kind: KeyKind, value: string): void
  editor: EditorCore | null
  validation: ValidationCore | null
}
