/**
 * Data source of the embeddable editor in React: XML, profile and ports from
 * the props, resolved by the framework-free `elementSource` functions of the
 * UI core (same rules as the Vue web component) and reloaded on change.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { loadSource, persistSource, sourcePorts, sourceRest, type ElementSourceInput } from '@flowaudit/bpmn-flowaudit/ui'
import type { ProfileData } from '@flowaudit/bpmn-flowaudit'

export function useElementSource(input: ElementSourceInput, onError: (message: string) => void) {
  const [xml, setXml] = useState('')
  const [profile, setProfile] = useState<ProfileData | null>(null)
  const latest = useRef({ input, onError })
  useEffect(() => {
    latest.current = { input, onError }
  })

  const reload = useCallback(async (): Promise<void> => {
    try {
      const next = await loadSource(latest.current.input)
      setProfile(next.profile)
      if (next.xml) setXml(next.xml)
    } catch (error) {
      latest.current.onError((error as Error).message)
    }
  }, [])

  const { xml: givenXml, src, apiBase, diagramId, profile: profileId, profileData, storage } = input
  useEffect(() => {
    void reload()
  }, [reload, givenXml, src, apiBase, diagramId, profileId, profileData, storage])

  const ports = useMemo(() => sourcePorts({ apiBase, ports: input.ports }, sourceRest({ apiBase })), [apiBase, input.ports])
  const persist = useCallback((content: string) => persistSource(latest.current.input, content), [])
  return { xml, setXml, profile, ports, persist, reload }
}
