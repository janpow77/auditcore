/**
 * `@auditcore/common/browser`: Helfer mit DOM-Zugriff. Beim Import wird nichts
 * ausgeführt (SSR-tauglich); die Funktionen greifen erst beim Aufruf auf
 * `document`, `navigator` und Web Storage zu.
 */
export { saveFile, downloadBlob, type DownloadOptions } from './browser/download'
export { copyText } from './browser/clipboard'
export { safeStorage, type SafeStorage, type SafeStorageOptions } from './browser/storage'
export { matchesMediaQuery, subscribeMediaQuery, onClickOutside, type ElementSource } from './browser/dom'
