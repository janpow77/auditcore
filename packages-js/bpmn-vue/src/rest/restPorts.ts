/**
 * Ports over the REST contract of `docs/bpmn/rest-api.md` (used by the web
 * component and the standalone app; the library itself never calls the
 * network). JSON bodies use the data model of `auditcore_bpmn` (snake_case).
 */

import {
  fromWire,
  issueFromWire,
  toWire,
  validateProfile,
  type CataloguePort,
  type CollectionData,
  type Comment,
  type EsiPort,
  type KeyRequirementEntry,
  type LegalSearchHit,
  type LegalSearchOptions,
  type LegalSearchPort,
  type ProfileData,
  type ProfilePort,
  type ProfileSummary,
  type StoragePort,
  type ValidationIssue,
  type ValidationPort,
} from '@flowaudit/bpmn-flowaudit'

export interface RestOptions {
  /** Base URL, e.g. `https://intranet.example/api/bpmn`. */
  baseUrl: string
  fetch?: typeof fetch
  /** Extra headers (e.g. authorisation) or a function returning them. */
  headers?: Record<string, string> | (() => Record<string, string>)
  credentials?: RequestCredentials
}

export class RestClient {
  constructor(private readonly options: RestOptions) {}

  private url(path: string, query?: Record<string, string | number | undefined>): string {
    const base = this.options.baseUrl.replace(/\/+$/, '')
    const params = Object.entries(query ?? {}).filter(([, value]) => value !== undefined && value !== '')
    const search = params.length ? `?${new URLSearchParams(params.map(([key, value]) => [key, String(value)])).toString()}` : ''
    return `${base}${path}${search}`
  }

  async request(
    method: string,
    path: string,
    init: { body?: string; type?: string; query?: Record<string, string | number | undefined>; signal?: AbortSignal; headers?: Record<string, string> } = {},
  ): Promise<Response> {
    const extra = typeof this.options.headers === 'function' ? this.options.headers() : this.options.headers ?? {}
    const headers: Record<string, string> = { Accept: 'application/json, application/xml;q=0.9', ...extra, ...init.headers }
    if (init.body !== undefined) headers['Content-Type'] = init.type ?? 'application/json'
    const response = await (this.options.fetch ?? fetch)(this.url(path, init.query), { method, headers, body: init.body, credentials: this.options.credentials ?? 'same-origin', signal: init.signal })
    if (response.status === 412) throw new Error('Die Daten wurden zwischenzeitlich geändert; bitte neu laden.')
    if (!response.ok) throw new Error(await errorText(response))
    return response
  }

  async json<T>(method: string, path: string, body?: unknown, query?: Record<string, string | number | undefined>, signal?: AbortSignal): Promise<T> {
    const response = await this.request(method, path, { body: body === undefined ? undefined : JSON.stringify(body), query, signal })
    return response.status === 204 ? (undefined as T) : ((await response.json()) as T)
  }

  async text(method: string, path: string, body?: string): Promise<string> {
    return (await this.request(method, path, { body, type: 'application/xml; charset=utf-8' })).text()
  }
}

/** Error text from a JSON `detail`/`message` or the status line (as `extractErrorMessage` did). */
async function errorText(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: unknown; message?: unknown }
    if (typeof data.detail === 'string') return data.detail
    if (Array.isArray(data.detail)) return data.detail.map((item) => (item && typeof item === 'object' && 'msg' in item ? String(item.msg) : String(item))).join(', ')
    if (typeof data.message === 'string') return data.message
  } catch {
    // no JSON body
  }
  return `${response.status} ${response.statusText}`.trim()
}

const encode = encodeURIComponent

/**
 * Storage over REST. The collection is one JSON document; an `ETag` of the
 * server is sent back as `If-Match`, so concurrent changes fail with 412
 * instead of overwriting each other.
 */
export class RestStorage implements StoragePort {
  private collectionTag: string | null = null

  constructor(private readonly client: RestClient) {}

  async loadCollection(): Promise<CollectionData | null> {
    const response = await this.client.request('GET', '/collection')
    this.collectionTag = response.headers.get('ETag')
    if (response.status === 204) return null
    const data = (await response.json()) as Record<string, unknown> | null
    return data ? fromWire<CollectionData>(data) : null
  }
  async saveCollection(collection: CollectionData): Promise<void> {
    const headers: Record<string, string> = this.collectionTag ? { 'If-Match': this.collectionTag } : {}
    const response = await this.client.request('PUT', '/collection', { body: JSON.stringify(toWire(collection)), headers })
    this.collectionTag = response.headers.get('ETag') ?? this.collectionTag
  }
  loadDiagram(id: string): Promise<string> {
    return this.client.text('GET', `/diagrams/${encode(id)}/xml`)
  }
  async saveDiagram(id: string, xml: string): Promise<void> {
    await this.client.text('PUT', `/diagrams/${encode(id)}/xml`, xml)
  }
  async deleteDiagram(id: string): Promise<void> {
    await this.client.request('DELETE', `/diagrams/${encode(id)}`)
  }
  async saveApproval(id: string, version: string, xml: string): Promise<void> {
    await this.client.text('PUT', `/diagrams/${encode(id)}/approvals/${encode(version)}`, xml)
  }
  loadApproval(id: string, version: string): Promise<string> {
    return this.client.text('GET', `/diagrams/${encode(id)}/approvals/${encode(version)}`)
  }
  async loadComments(id: string): Promise<Comment[]> {
    return ((await this.client.json<Record<string, unknown>[]>('GET', `/diagrams/${encode(id)}/comments`)) ?? []).map((entry) => fromWire<Comment>(entry))
  }
  async saveComments(id: string, comments: Comment[]): Promise<void> {
    await this.client.json('PUT', `/diagrams/${encode(id)}/comments`, comments.map((comment) => toWire(comment)))
  }
}

export class RestLegalSearch implements LegalSearchPort {
  constructor(private readonly client: RestClient) {}
  async search(query: string, options: LegalSearchOptions = {}): Promise<LegalSearchHit[]> {
    const hits = await this.client.json<Record<string, unknown>[]>('GET', '/legal-bases', undefined, { q: query, limit: options.limit, profile: options.profile, locale: options.locale }, options.signal)
    return (hits ?? []).map((hit) => fromWire<LegalSearchHit>(hit))
  }
}

export class RestProfiles implements ProfilePort {
  constructor(private readonly client: RestClient) {}
  async profiles(): Promise<ProfileSummary[]> {
    return ((await this.client.json<Record<string, unknown>[]>('GET', '/profiles')) ?? []).map((entry) => fromWire<ProfileSummary>(entry))
  }
  async loadProfile(id: string, version?: string): Promise<ProfileData> {
    return validateProfile(await this.client.json('GET', `/profiles/${encode(id)}`, undefined, { version }))
  }
}

export class RestCatalogue implements CataloguePort {
  constructor(private readonly client: RestClient) {}
  async keyRequirements(profileId: string, locale: 'de' | 'en' = 'de'): Promise<KeyRequirementEntry[]> {
    return ((await this.client.json<Record<string, unknown>[]>('GET', `/profiles/${encode(profileId)}/key-requirements`, undefined, { locale })) ?? []).map((entry) => fromWire<KeyRequirementEntry>(entry))
  }
}

export class RestValidation implements ValidationPort {
  constructor(private readonly client: RestClient) {}
  async validate(xml: string, options: { profile?: string; referenceDate?: string; locale?: 'de' | 'en' } = {}): Promise<ValidationIssue[]> {
    const report = await this.client.json<{ issues?: Record<string, unknown>[] }>('POST', '/validation', { xml, profile: options.profile, reference_date: options.referenceDate, locale: options.locale })
    return (report?.issues ?? []).map(issueFromWire)
  }
}

export class RestEsi implements EsiPort {
  constructor(private readonly client: RestClient) {}
  requirements(xml: string, diagramId?: string): Promise<unknown> {
    return this.client.json('POST', '/esi-requirements', { xml, diagram_id: diagramId })
  }
}

/** All ports for one REST base URL. */
export function restPorts(options: RestOptions) {
  const client = new RestClient(options)
  return {
    client,
    storage: new RestStorage(client),
    legalSearch: new RestLegalSearch(client),
    profiles: new RestProfiles(client),
    catalogue: new RestCatalogue(client),
    validation: new RestValidation(client),
    esi: new RestEsi(client),
  }
}
