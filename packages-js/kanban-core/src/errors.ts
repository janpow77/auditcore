/** Fehler- und Entscheidungsvertrag, gleich zu `auditcore_kanban.errors`. */

export type ErrorCode =
  | 'VALIDATION_ERROR'
  | 'INVALID_PERMISSION'
  | 'SELF_SHARE'
  | 'UNKNOWN_COLUMN'
  | 'UNAUTHENTICATED'
  | 'FORBIDDEN'
  | 'NOT_VISIBLE'
  | 'BOARD_NOT_FOUND'
  | 'CARD_NOT_FOUND'
  | 'SHARE_NOT_FOUND'
  | 'USER_NOT_FOUND'
  | 'ROUTE_NOT_FOUND'
  | 'METHOD_NOT_ALLOWED'
  | 'TRANSITION_NOT_ALLOWED'
  | 'COLUMN_LOCKED'
  | 'ORDER_FIXED'
  | 'WIP_LIMIT_REACHED'
  | 'VERSION_CONFLICT'
  | 'BOARD_EXISTS'
  | 'INVALID_REQUEST'
  | 'INVALID_DOCUMENT'

/** HTTP-Status je Code (REST-Vertrag docs/kanban/rest-api.md). */
export const STATUS_BY_CODE: Readonly<Record<ErrorCode, number>> = {
  VALIDATION_ERROR: 400,
  INVALID_PERMISSION: 400,
  SELF_SHARE: 400,
  UNKNOWN_COLUMN: 400,
  UNAUTHENTICATED: 401,
  FORBIDDEN: 403,
  NOT_VISIBLE: 404,
  BOARD_NOT_FOUND: 404,
  CARD_NOT_FOUND: 404,
  SHARE_NOT_FOUND: 404,
  USER_NOT_FOUND: 404,
  ROUTE_NOT_FOUND: 404,
  METHOD_NOT_ALLOWED: 405,
  TRANSITION_NOT_ALLOWED: 409,
  COLUMN_LOCKED: 409,
  ORDER_FIXED: 409,
  WIP_LIMIT_REACHED: 409,
  VERSION_CONFLICT: 409,
  BOARD_EXISTS: 409,
  INVALID_REQUEST: 422,
  INVALID_DOCUMENT: 422,
}

export class KanbanError extends Error {
  constructor(
    readonly code: ErrorCode | string,
    message: string,
  ) {
    super(message)
    this.name = 'KanbanError'
  }

  get status(): number {
    return STATUS_BY_CODE[this.code as ErrorCode] ?? 400
  }
}

/** Ergebnis einer Regelprüfung; `warnings` trägt nicht blockierende Codes (WIP-Warnmodus). */
export interface Decision {
  allowed: boolean
  code: string
  message: string
  warnings: string[]
}

export const ALLOWED: Decision = Object.freeze({ allowed: true, code: 'OK', message: '', warnings: [] }) as Decision

export function deny(code: ErrorCode, message: string): Decision {
  return { allowed: false, code, message, warnings: [] }
}

export function raiseIfDenied(decision: Decision): void {
  if (!decision.allowed) throw new KanbanError(decision.code, decision.message)
}

/** JSON-Form der Paritätsfixtures. */
export function decisionToJson(decision: Decision): { allowed: boolean; code: string | null; warnings: string[] } {
  return {
    allowed: decision.allowed,
    code: decision.allowed && decision.code === 'OK' ? null : decision.code,
    warnings: [...decision.warnings],
  }
}
