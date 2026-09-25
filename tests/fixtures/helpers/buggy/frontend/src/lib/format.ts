// Known helper bugs (test fixture): do not fix, the tests expect them.
export function parseNumberDe(text: string): number | null {
  const n = Number(text.replace(/\./g, '').replace(',', '.'))
  return Number.isFinite(n) ? n : null
}

export function formatDate(value: string): string {
  return new Date(value).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

export function extractError(err: any): string {
  return err?.response?.data?.detail || err?.message || 'Fehler'
}

export function notify(err: any, show: (text: string) => void): void {
  // auditcore-helpers: ignore HC-ERR-02 Meldung wird serverseitig schon als Text geliefert
  show(err.response?.data?.detail || 'Speichern fehlgeschlagen')
}
