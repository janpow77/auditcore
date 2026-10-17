/**
 * Stufe des Zwischenstands im Web Storage: `off` – nichts wird abgelegt;
 * `session` – nur für diese Sitzung (`sessionStorage`); `device` – auf diesem
 * Gerät behalten (`localStorage`).
 */
export type DraftMode = 'off' | 'session' | 'device'

/** Einträge des Menüs „Arbeitsstand“. */
export type MenuAction = 'open' | 'save' | 'new' | 'sample' | 'clearDraft'
