/**
 * Rechtemodell als reine Logik: Rollen owner/edit/read wie audit_designer.
 * Ohne Rolle ist das Board unsichtbar (NOT_VISIBLE, REST 404); fehlt einer
 * sichtbaren Rolle das Recht, gilt FORBIDDEN (403).
 */
import { ALLOWED, deny, type Decision } from './errors'
import { shareFor, type Board, type Role } from './model'

export type Action =
  | 'read'
  | 'create_card'
  | 'edit_card'
  | 'move_card'
  | 'delete_card'
  | 'rename'
  | 'configure'
  | 'share'
  | 'delete_board'
  | 'pin'

export const ACTIONS: readonly Action[] = ['read', 'create_card', 'edit_card', 'move_card', 'delete_card', 'rename', 'configure', 'share', 'delete_board', 'pin']

const CARD_WORK: readonly Action[] = ['read', 'create_card', 'edit_card', 'move_card', 'delete_card']

/** Deklarative Rollentabelle; configure, share, delete_board und pin nur für den Eigentümer. */
export const ROLE_ACTIONS: Readonly<Record<Role, readonly Action[]>> = {
  owner: ACTIONS,
  edit: [...CARD_WORK, 'rename'],
  read: ['read'],
}

export const PERMISSIONS: readonly Role[] = ['read', 'edit']

function isRole(value: string | undefined): value is Role {
  return value === 'owner' || value === 'edit' || value === 'read'
}

/** Rolle: Eigentümer, eigene Freigabe, sonst geerbte Freigabe (z. B. Notizbuch). */
export function roleOf(board: Board, userId: string, inherited?: Readonly<Record<string, string>>): string | null {
  if (userId === board.owner_id) return 'owner'
  const share = shareFor(board, userId)
  if (share) return share.permission
  return inherited?.[userId] ?? null
}

export function allowedActions(role: string | null): readonly Action[] {
  return role !== null && isRole(role) ? ROLE_ACTIONS[role] : []
}

export function authorize(board: Board, userId: string, action: Action, inherited?: Readonly<Record<string, string>>): Decision {
  const role = roleOf(board, userId, inherited)
  if (role === null || !isRole(role)) return deny('NOT_VISIBLE', 'Board nicht gefunden')
  if (ROLE_ACTIONS[role].includes(action)) return ALLOWED
  if (role === 'read') return deny('FORBIDDEN', 'Nur Lesezugriff auf dieses Board')
  return deny('FORBIDDEN', 'Nur der Eigentümer darf das')
}

/** Aktionen, die der Nutzer ausführen darf (für die Oberfläche). */
export function capabilities(board: Board, userId: string, inherited?: Readonly<Record<string, string>>): Readonly<Record<Action, boolean>> {
  const granted = allowedActions(roleOf(board, userId, inherited))
  return Object.fromEntries(ACTIONS.map((action) => [action, granted.includes(action)])) as Record<Action, boolean>
}

export function checkShare(board: Board, actor: string, targetUser: string, permission: string): Decision {
  const decision = authorize(board, actor, 'share')
  if (!decision.allowed) return decision
  if (permission !== 'read' && permission !== 'edit') {
    return deny('INVALID_PERMISSION', "Ungültige Berechtigung. Erlaubt: ['edit', 'read']")
  }
  if (targetUser === actor || targetUser === board.owner_id) {
    return deny('SELF_SHARE', 'Kann nicht mit sich selbst geteilt werden')
  }
  return ALLOWED
}

export function checkRevoke(board: Board, actor: string, targetUser: string): Decision {
  if (!shareFor(board, targetUser)) return deny('SHARE_NOT_FOUND', 'Freigabe nicht gefunden')
  if (actor === board.owner_id || actor === targetUser) return ALLOWED
  return deny('FORBIDDEN', 'Keine Berechtigung')
}
