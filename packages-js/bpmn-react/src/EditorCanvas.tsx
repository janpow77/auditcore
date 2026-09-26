/**
 * Canvas area of the editor: the host of the core editor with page grid and
 * the popover for colour and role choice from the context pad.
 */

import { label, PALETTE_COLORS, rolesFor, type PaletteColor, type ProfileData } from '@auditcore/bpmn-flowaudit'
import { choosePopoverColor, choosePopoverRole } from '@auditcore/bpmn-flowaudit/ui'
import { ColorSwatches } from './base/ColorSwatches'
import { CanvasPopover, PageGrid } from './canvas/CanvasParts'
import { classes, useStoreState } from './hooks'
import { useI18n } from './i18n'
import type { EditorRuntime, HostRef } from './useEditorSession'

export interface EditorCanvasProps {
  host: HostRef
  runtime: EditorRuntime | null
  pageView: string
  readonly: boolean
  profile: ProfileData | null
  palette?: readonly PaletteColor[]
}

function Popover({ runtime, profile, palette }: { runtime: EditorRuntime; profile: ProfileData | null; palette?: readonly PaletteColor[] }) {
  const { t, locale } = useI18n()
  const { popover, size } = useStoreState(runtime.session.canvas)
  if (!popover) return null
  return (
    <CanvasPopover x={popover.x} y={popover.y} width={size.width} height={size.height} title={popover.kind === 'color' ? t('color.title') : t('role.choose')} onClose={runtime.session.closePopover}>
      {popover.kind === 'color' ? (
        <ColorSwatches colors={palette ?? PALETTE_COLORS} onChoose={(color) => choosePopoverColor(runtime.session, color)} />
      ) : (
        rolesFor(profile).map((role) => (
          <button key={role.code} type="button" className="fa-menu-item" onClick={() => choosePopoverRole(runtime.session, profile, role.code)}>
            {role.short} – {label(role.label, locale)}
          </button>
        ))
      )}
    </CanvasPopover>
  )
}

function Grid({ runtime, view }: { runtime: EditorRuntime; view: string }) {
  const { viewbox, size } = useStoreState(runtime.session.canvas)
  return <PageGrid view={view} viewbox={viewbox} width={size.width} height={size.height} />
}

export function EditorCanvas({ host, runtime, pageView, readonly, profile, palette }: EditorCanvasProps) {
  const { t } = useI18n()
  return (
    <div ref={host} className={classes('fa-canvas-host', readonly && 'fa-canvas-host--readonly')} tabIndex={0} aria-label={t('editor.label')}>
      {runtime ? <Grid runtime={runtime} view={pageView} /> : null}
      {runtime ? <Popover runtime={runtime} profile={profile} palette={palette} /> : null}
    </div>
  )
}
