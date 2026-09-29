/** Frameworkunabhängiger Formularvertrag; Feldrechte kommen vom Server. */
export interface AccountItem { id: string; label: string; group?: string }
export interface AccountField {
  id: string
  label: string
  type?: 'text' | 'email' | 'url' | 'password' | 'textarea' | 'select' | 'multiselect' | 'color' | 'image'
  required?: boolean
  readonly?: boolean
  hint?: string
  options?: readonly { value: string; label: string }[]
  autocomplete?: string
}
export interface AccountDocument {
  id: string
  title: string
  description: string
  kind: 'profile' | 'branding' | 'welcome' | 'security' | 'admin' | 'extension'
  revision: number
  fields: readonly AccountField[]
  values: Readonly<Record<string, string>>
  submitLabel?: string
  editable: boolean
}
export interface AccountImage { id: string; url: string }
export interface AccountPort {
  list: () => Promise<readonly AccountItem[]>
  read: (id: string) => Promise<AccountDocument>
  save: (id: string, revision: number, values: Readonly<Record<string, string>>) => Promise<AccountDocument>
  /** Host autorisiert Dokument und Feld und liefert eine zugriffsgeschützte Bild-URL. */
  upload?: (documentId: string, fieldId: string, file: Blob) => Promise<AccountImage>
  imageUrl?: (assetId: string) => string
}
