/**
 * Kanten: Sequenzfluss (Standard, bedingt, Default), Nachrichtenfluss,
 * Assoziation und Datenassoziationen.
 */

import { createLine } from 'diagram-js/lib/util/RenderUtil'

import * as G from '../Glyphs'
import { append, svgPath, type SvgAttrs } from '../svg'
import { getBusinessObject, getDi, is, isAny } from '../../util/ModelUtil'
import type { ModdleElement, Point } from '../../types'
import type { DrawContext } from './context'

type StyleBuilder = (context: DrawContext) => SvgAttrs

function sequenceFlowStyle(context: DrawContext): SvgAttrs {
  const { fill, stroke, markers } = context
  const bo = getBusinessObject(context.element)
  const attrs: SvgAttrs = { 'marker-end': markers.url('sequence-end', fill, stroke) }
  const source = bo.sourceRef
  if (!source) return attrs
  if (source.default === bo && isAny(source, ['bpmn:Gateway', 'bpmn:Activity'])) {
    attrs['marker-start'] = markers.url('default-start', fill, stroke)
  } else if (bo.conditionExpression && is(source, 'bpmn:Activity')) {
    attrs['marker-start'] = markers.url('conditional-start', fill, stroke)
  }
  return attrs
}

function associationStyle(context: DrawContext): SvgAttrs {
  const { fill, stroke, markers } = context
  const direction = getBusinessObject(context.element).associationDirection
  return {
    'stroke-dasharray': '1,4',
    'stroke-linecap': 'round',
    'marker-end': direction === 'One' || direction === 'Both' ? markers.url('association-end', fill, stroke) : undefined,
    'marker-start': direction === 'Both' ? markers.url('association-start', fill, stroke) : undefined,
  }
}

/** Linienstil je Kantentyp (deklarative Tabelle). */
const CONNECTION_STYLES: [string, StyleBuilder][] = [
  ['bpmn:SequenceFlow', sequenceFlowStyle],
  [
    'bpmn:MessageFlow',
    ({ fill, stroke, markers }) => ({
      'stroke-dasharray': '9,5',
      'marker-start': markers.url('message-start', fill, stroke),
      'marker-end': markers.url('message-end', fill, stroke),
    }),
  ],
  ['bpmn:Association', associationStyle],
  [
    'bpmn:DataAssociation',
    ({ fill, stroke, markers }) => ({
      'stroke-dasharray': '1,4',
      'stroke-linecap': 'round',
      'marker-end': markers.url('association-end', fill, stroke),
    }),
  ],
]

function drawMessageOnFlow(parent: SVGElement, context: DrawContext, points: Point[]): void {
  const index = Math.floor((points.length - 1) / 2)
  const a = points[index]
  const b = points[index + 1] || a
  if (!a || !b) return
  const envelope = G.envelopePaths((a.x + b.x) / 2, (a.y + b.y) / 2, 1.25)
  const di = getDi(context.element) as ModdleElement | undefined
  const initiating = !di || di.get('messageVisibleKind') !== 'non_initiating'
  svgPath(parent, envelope.body, { fill: initiating ? context.fill : '#d9d9d9', stroke: context.stroke, 'stroke-width': 1 })
  svgPath(parent, envelope.flap, { fill: 'none', stroke: context.stroke, 'stroke-width': 1 })
}

export function drawConnection(parent: SVGElement, context: DrawContext): SVGElement {
  const entry = CONNECTION_STYLES.find(([type]) => is(context.element, type))
  const style = entry ? entry[1](context) : {}
  const attrs: Record<string, string | number> = { fill: 'none', stroke: context.stroke, 'stroke-width': 1.5, 'stroke-linejoin': 'round' }
  for (const [key, value] of Object.entries(style)) {
    if (value !== undefined && value !== null) attrs[key] = value
  }
  const points = (context.element as unknown as { waypoints: Point[] }).waypoints
  const line = createLine(points, attrs, 5) as SVGElement
  append(parent, line)
  if (is(context.element, 'bpmn:MessageFlow') && getBusinessObject(context.element).messageRef && points.length >= 2) {
    drawMessageOnFlow(parent, context, points)
  }
  return line
}
