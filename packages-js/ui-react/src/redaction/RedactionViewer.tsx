import { useRef, type KeyboardEvent, type PointerEvent, type RefObject } from 'react'
import { isRedactionArrow, redactionPoint, type RedactionAreaView, type RedactionController, type RedactionReviewView } from '@auditcore/ui-core'
import { Button } from '../base/Button'
import { classes } from '../store'
import type { UseRedaction } from './useRedaction'

interface Part {
  hook: UseRedaction
  view: RedactionReviewView
}

const stop = (event: PointerEvent): void => event.stopPropagation()

/** Zeigergesten auf der Seite: Punkte in Anteilen 0…1 der Überlagerung. */
function usePointer(controller: RedactionController) {
  const overlay = useRef<HTMLDivElement | null>(null)
  const point = (event: PointerEvent): [number, number] => {
    const bounds = overlay.current?.getBoundingClientRect()
    return bounds ? redactionPoint(bounds, event.clientX, event.clientY) : [0, 0]
  }
  const capture = (event: PointerEvent): void => overlay.current?.setPointerCapture?.(event.pointerId)
  return {
    overlay,
    onDown(event: PointerEvent): void {
      if (event.button !== 0) return
      controller.pointerDown(point(event))
      capture(event)
    },
    onMove: (event: PointerEvent) => controller.pointerMove(point(event)),
    onUp: (event: PointerEvent) => controller.pointerUp(point(event)),
    onResizeStart(areaId: string, event: PointerEvent): void {
      event.stopPropagation()
      controller.startResize(areaId)
      capture(event)
    },
  }
}

function areaKey(controller: RedactionController, areaId: string, mode: 'move' | 'resize', event: KeyboardEvent): void {
  if (mode === 'move' && (event.key === 'Delete' || event.key === 'Backspace')) {
    event.preventDefault()
    controller.removeArea(areaId)
    return
  }
  if (!isRedactionArrow(event.key)) return
  event.preventDefault()
  controller.nudgeArea(areaId, event.key, mode, event.shiftKey)
}

function Pager({ hook, view }: Part) {
  const { controller, t } = hook
  return (
    <div className="fa-redaction__pager">
      <Button size="sm" icon="chevron-left" iconOnly label={t('previousPage')} disabled={view.page <= 1} testId="redaction-previous" onClick={() => void controller.showPage(view.page - 1)} />
      <span className="fa-redaction__pager-text" aria-live="polite">{view.pageText}</span>
      <Button size="sm" icon="chevron-right" iconOnly label={t('nextPage')} disabled={view.page >= view.pageCount} testId="redaction-next" onClick={() => void controller.showPage(view.page + 1)} />
      <Button size="sm" testId="redaction-add-area" onClick={() => controller.addDefaultArea()}>{t('addArea')}</Button>
    </div>
  )
}

function PageImage({ hook, view }: Part) {
  const { state, t } = hook
  if (state.preview) return <img className="fa-redaction__image" src={state.preview} alt={t('pageImage', { page: view.page })} draggable={false} />
  if (state.previewError) return <p className="fa-redaction__error" role="alert">{t('previewFailed', { message: state.previewError })}</p>
  return <p className="fa-redaction__muted" role="status">{t('previewLoading')}</p>
}

function Area({ area, controller, onResizeStart }: { area: RedactionAreaView; controller: RedactionController; onResizeStart: (id: string, event: PointerEvent) => void }) {
  return (
    <div className="fa-redaction__area" style={area.style} data-area={area.number} onPointerDown={stop}>
      <button type="button" className="fa-redaction__area-move" aria-label={area.label} onKeyDown={(event) => areaKey(controller, area.id, 'move', event)} />
      <button type="button" className="fa-redaction__area-remove" aria-label={area.removeLabel} title={area.removeLabel} onClick={() => controller.removeArea(area.id)}>×</button>
      <button type="button" className="fa-redaction__area-resize" aria-label={area.resizeLabel} title={area.resizeLabel} onPointerDown={(event) => onResizeStart(area.id, event)} onKeyDown={(event) => areaKey(controller, area.id, 'resize', event)} />
    </div>
  )
}

function Overlay({ hook, view, pointer }: Part & { pointer: ReturnType<typeof usePointer> }) {
  const { controller } = hook
  return (
    <div ref={pointer.overlay as RefObject<HTMLDivElement>} className="fa-redaction__overlay" data-testid="redaction-overlay" onPointerDown={pointer.onDown} onPointerMove={pointer.onMove} onPointerUp={pointer.onUp} onPointerCancel={() => controller.cancelGesture()}>
      {view.boxes.map((box) => (
        <button key={box.key} type="button" className={classes('fa-redaction__box', box.on ? 'fa-redaction__box--on' : 'fa-redaction__box--off')} style={box.style} aria-pressed={box.on} aria-label={box.label} title={box.label} data-candidate={box.id} onPointerDown={stop} onClick={() => controller.toggle(box.id)} />
      ))}
      {view.areas.map((area) => <Area key={area.id} area={area} controller={controller} onResizeStart={pointer.onResizeStart} />)}
      {view.draft ? <div className="fa-redaction__draft" style={view.draft} /> : null}
    </div>
  )
}

function PageLinks({ hook, view }: Part) {
  if (!view.pageButtons.length) return null
  return (
    <p className="fa-redaction__pages">
      <span>{hook.t('pagesWithFindings')}</span>
      {view.pageButtons.map((number) => (
        <button key={number} type="button" className="fa-redaction__page-link" aria-current={number === view.page ? 'page' : undefined} onClick={() => void hook.controller.showPage(number)}>{number}</button>
      ))}
      {view.morePages ? <span>…</span> : null}
    </p>
  )
}

/** Seitenbild mit Markierungen, Zeigergesten und Seitenwechsel. */
export function RedactionViewer({ hook, view }: Part) {
  const pointer = usePointer(hook.controller)
  return (
    <section className="fa-redaction__viewer" aria-label={hook.t('pageView')}>
      <p className="fa-redaction__muted">{hook.t('reviewHelp')}</p>
      <Pager hook={hook} view={view} />
      <div className="fa-redaction__page" style={{ aspectRatio: view.aspect }}>
        <PageImage hook={hook} view={view} />
        <Overlay hook={hook} view={view} pointer={pointer} />
      </div>
      {view.areaLimit ? <p className="fa-redaction__error" role="status">{view.areaLimit}</p> : null}
      <PageLinks hook={hook} view={view} />
    </section>
  )
}
