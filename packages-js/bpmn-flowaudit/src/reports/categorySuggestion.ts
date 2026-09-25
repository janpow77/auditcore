/**
 * **Suggestion** of a functioning category per key requirement (the
 * decision stays with the auditor). Same heuristic as `auditcore_bpmn`:
 * no basis → no suggestion; evidence without finding → 1; only formal,
 * minor findings or failed audit steps → 2; financial or moderate → 3;
 * serious → 4. Withdrawn findings do not count.
 */

import type { ProcessModel } from '../model/processModel'
import { keyRequirements, localized, type ProfileData } from '../profile/profile'
import type { AuditFinding, AuditReference, AuditStep } from '../schema/types'
import { FUNCTIONING_CATEGORIES, label } from '../schema/vocabulary'

export interface CategorySuggestion {
  keyRequirement: number
  title: string
  category: number | null
  categoryText: string | null
  reason: string
  findings: string[]
  note: string
}

interface Tally {
  evidence: Map<number, number>
  findings: Map<number, AuditFinding[]>
  failed: Map<number, number>
}

const increment = (map: Map<number, number>, key: number, by = 1) => map.set(key, (map.get(key) ?? 0) + by)

function tallyHolder(tally: Tally, references: AuditReference[], findings: AuditFinding[], steps: AuditStep[]): void {
  const numbers = new Set(references.map((ref) => Number(ref.keyRequirement)).filter(Number.isInteger))
  for (const number of numbers) {
    increment(tally.evidence, number)
    increment(tally.failed, number, steps.filter((step) => step.result === 'nicht_erfuellt').length)
  }
  for (const finding of findings) {
    const number = Number(String(finding.keyRequirement ?? '').trim())
    if (finding.status === 'entfallen' || !finding.keyRequirement || !Number.isInteger(number)) continue
    tally.findings.set(number, [...(tally.findings.get(number) ?? []), finding])
    increment(tally.evidence, number)
  }
}

function classify(findings: AuditFinding[], failed: number): [number, string] {
  if (findings.some((f) => f.severity === 'schwerwiegend')) return [4, 'Mindestens eine schwerwiegende Feststellung.']
  if (findings.some((f) => f.findingType === 'finanziell' || f.severity === 'mittel')) return [3, 'Finanzielle oder mittlere Feststellung(en).']
  if (findings.length || failed) return [2, 'Nur formelle, geringe Feststellung(en) oder nicht erfüllte Prüfschritte.']
  return [1, 'Prüfbezüge ohne Feststellung.']
}

const NOTE = 'Vorschlag – die Einstufung entscheidet der Prüfer.'

export function suggestCategories(models: ProcessModel[], profile: ProfileData | null): CategorySuggestion[] {
  const tally: Tally = { evidence: new Map(), findings: new Map(), failed: new Map() }
  for (const model of models) {
    for (const element of model.elements) {
      const ext = element.extensions
      tallyHolder(tally, ext.auditReferences, ext.findings, ext.auditSteps)
    }
    if (model.info) tallyHolder(tally, model.info.auditReferences ?? [], model.info.findings ?? [], [])
  }
  return keyRequirements(profile).map((requirement) => {
    const number = requirement.nummer
    const findings = tally.findings.get(number) ?? []
    const title = localized(requirement.titel)
    const base = { keyRequirement: number, title, findings: findings.map((f) => f.reference || f.id || 'Feststellung'), note: NOTE }
    if (!tally.evidence.get(number)) {
      return { ...base, category: null, categoryText: null, reason: 'Keine Prüfbezüge oder Feststellungen zu dieser KA.' }
    }
    const [category, reason] = classify(findings, tally.failed.get(number) ?? 0)
    return { ...base, category, categoryText: label(FUNCTIONING_CATEGORIES[String(category)]), reason }
  })
}
