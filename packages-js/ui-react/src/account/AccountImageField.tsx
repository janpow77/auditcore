import { useEffect, useRef, useState } from 'react'
import { accountMessages, createAccountCamera, cropAccountImage, type Locale } from '@auditcore/ui-core'
import { useTranslation } from '../i18n'
export function AccountImageField(props: { label: string; url: string; disabled: boolean; allowCamera: boolean; locale?: Locale; onUpload: (file: Blob) => void; onRemove: () => void }) {
  const { t } = useTranslation(accountMessages, props.locale)
  const [camera] = useState(createAccountCamera)
  const [active, setActive] = useState(false)
  const [error, setError] = useState(false)
  const [original, setOriginal] = useState<Blob | null>(null)
  const [zoom, setZoom] = useState(1)
  const [x, setX] = useState(0.5)
  const [y, setY] = useState(0.5)
  const video = useRef<HTMLVideoElement>(null)
  const stop = () => { camera.stop(); setActive(false) }
  useEffect(() => {
    if (active && video.current) void camera.start(video.current).catch(() => { setError(true); setActive(false) })
    return () => camera.stop()
  }, [active, camera])
  async function capture() {
    try { if (video.current) props.onUpload(await camera.capture(video.current)); stop() }
    catch { setError(true); stop() }
  }
  return <div className="fa-account__image">
    {props.url ? <img src={props.url} alt={props.label} width="96" height="96" /> : <div className="fa-account__avatar" aria-hidden="true">◎</div>}
    <label>{t('upload')}<input type="file" accept="image/png,image/jpeg,image/webp" disabled={props.disabled} onChange={(event) => {
      const file = event.target.files?.[0]; if (file) { setOriginal(file); setZoom(1); setX(0.5); setY(0.5); props.onUpload(file) }; event.target.value = ''
    }} /></label>
    {props.allowCamera ? <button type="button" disabled={props.disabled} onClick={() => { setError(false); setActive(true) }}>{t('camera')}</button> : null}
    {props.url ? <button type="button" disabled={props.disabled} onClick={props.onRemove}>{t('remove')}</button> : null}
    {original ? <div className="fa-account__crop">
      <label>{t('zoom')}<input type="range" min="1" max="4" step="0.1" value={zoom} onChange={(e) => setZoom(Number(e.target.value))} /></label>
      <label>{t('horizontal')}<input type="range" min="0" max="1" step="0.01" value={x} onChange={(e) => setX(Number(e.target.value))} /></label>
      <label>{t('vertical')}<input type="range" min="0" max="1" step="0.01" value={y} onChange={(e) => setY(Number(e.target.value))} /></label>
      <button type="button" disabled={props.disabled} onClick={() => { void cropAccountImage(original, zoom, x, y).then(props.onUpload).catch(() => setError(true)) }}>{t('crop')}</button>
    </div> : null}
    {active ? <div className="fa-account__camera">
      <video ref={video} muted playsInline aria-label={props.label} />
      <button type="button" disabled={props.disabled} onClick={() => void capture()}>{t('capture')}</button>
      <button type="button" onClick={stop}>{t('stop')}</button>
    </div> : null}
    {error ? <p role="alert">{t('cameraFailed')}</p> : null}
  </div>
}
