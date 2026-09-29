/** Opt-in Kamera, keine Aufnahme ohne Benutzeraktion, Tracks immer schließen. */
export function createAccountCamera() {
  let stream: MediaStream | null = null
  let generation = 0
  const stop = () => { generation++; stream?.getTracks().forEach((track) => track.stop()); stream = null }
  return {
    stop,
    async start(video: HTMLVideoElement) {
      stop()
      const current = generation
      const acquired = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false })
      if (generation !== current) { acquired.getTracks().forEach((track) => track.stop()); return }
      stream = acquired
      video.srcObject = stream
      try { await video.play() } catch (error) { stop(); throw error }
    },
    async capture(video: HTMLVideoElement): Promise<Blob> {
      if (!stream || !video.videoWidth) throw new Error('Kamera noch nicht bereit.')
      const canvas = document.createElement('canvas')
      const edge = Math.min(video.videoWidth, video.videoHeight)
      canvas.width = canvas.height = Math.min(edge, 1024)
      const context = canvas.getContext('2d')
      if (!context) throw new Error('Bildaufnahme nicht verfügbar.')
      context.drawImage(video, (video.videoWidth - edge) / 2, (video.videoHeight - edge) / 2, edge, edge, 0, 0, canvas.width, canvas.height)
      const blob = await new Promise<Blob>((resolve, reject) => canvas.toBlob((result) => result ? resolve(result) : reject(new Error('Bildaufnahme fehlgeschlagen.')), 'image/png'))
      stop()
      video.srcObject = null
      return blob
    },
  }
}

/** Quadratischer Zuschnitt: Position 0..1 und Zoom 1..4, Metadaten übernimmt der Server nicht. */
export async function cropAccountImage(file: Blob, zoom: number, x: number, y: number): Promise<Blob> {
  if (![zoom, x, y].every(Number.isFinite) || zoom < 1 || zoom > 4 || x < 0 || x > 1 || y < 0 || y > 1) throw new Error('Ungültiger Bildausschnitt.')
  const image = await createImageBitmap(file)
  try {
    const edge = Math.min(image.width, image.height) / zoom
    const canvas = document.createElement('canvas')
    canvas.width = canvas.height = Math.min(1024, Math.round(edge))
    const context = canvas.getContext('2d')
    if (!context) throw new Error('Bildbearbeitung nicht verfügbar.')
    context.drawImage(image, (image.width - edge) * x, (image.height - edge) * y, edge, edge, 0, 0, canvas.width, canvas.height)
    return await new Promise<Blob>((resolve, reject) => canvas.toBlob((blob) => blob ? resolve(blob) : reject(new Error('Zuschnitt fehlgeschlagen.')), 'image/png'))
  } finally { image.close() }
}
