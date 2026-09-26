/** Application ports of the editor UI (shared by the Vue and React packages). */

import type { CataloguePort, EsiPort, LegalSearchPort, ValidationPort } from '../index'

export interface EditorPorts {
  legalSearch?: LegalSearchPort
  catalogue?: CataloguePort
  esi?: EsiPort
}

/** Ports including the optional server validation. */
export type EditorPortsWithValidation = EditorPorts & { validation?: ValidationPort }
