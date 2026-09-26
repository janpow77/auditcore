/// <reference types="vite/client" />
/**
 * Profiles shipped with the Python package `auditcore_bpmn`.
 *
 * The JSON files exist exactly once in the repository
 * (`packages/auditcore_bpmn/src/auditcore_bpmn/profiles/data/`). Vite reads
 * them at build time and bundles them into `dist/profiles.js`; the sources
 * of this package contain no copy. Entry point:
 * `import { bundledProfiles } from '@auditcore/bpmn-flowaudit/profiles'`.
 */

import { DEFAULT_PROFILE, latestProfiles, validateProfile, type ProfileData } from './profile'

const files = import.meta.glob('../../../../packages/auditcore_bpmn/src/auditcore_bpmn/profiles/data/*.json', {
  eager: true,
  import: 'default',
}) as Record<string, unknown>

/** All versions of all bundled profiles. */
export const allBundledProfiles: ProfileData[] = Object.keys(files)
  .sort()
  .map((path) => validateProfile(files[path]))

/** Latest version of each bundled profile. */
export function bundledProfiles(): ProfileData[] {
  return latestProfiles(allBundledProfiles)
}

export function defaultProfile(): ProfileData | undefined {
  return bundledProfiles().find((profile) => profile.id === DEFAULT_PROFILE)
}

export { DEFAULT_PROFILE }
