import { createElement, forwardRef, useImperativeHandle, useLayoutEffect, useRef, type CSSProperties, type ReactNode } from 'react'

/** Ereignis-Handler einer Hülle erhalten das erste Argument des Vue-emit (CustomEvent.detail[0]). */
export type EventHandlers<E extends Record<string, string>> = {
  [H in keyof E]?: (payload: unknown, event: CustomEvent<unknown[]>) => void
}

export interface BaseElementProps {
  className?: string
  style?: CSSProperties
  id?: string
  children?: ReactNode
}

export interface ElementComponentOptions<P, E extends Record<string, string>> {
  /** Props, die als JS-Eigenschaften (nicht als Attribute) gesetzt werden – Objekte, Listen, Zahlen. */
  properties: readonly (keyof P & string)[]
  /** Zuordnung React-Handler → DOM-Ereignisname, z. B. `{ onRowClick: 'row-click' }`. */
  events: E
}

/** Liest das erste emit-Argument aus Vue-CustomEvents (detail ist ein Argument-Array). */
export function eventPayload(event: Event): unknown {
  const detail = (event as CustomEvent<unknown>).detail
  return Array.isArray(detail) ? detail[0] : detail
}

/**
 * Erzeugt eine React-18-Komponente für ein Custom Element. React 18 setzt an
 * Custom Elements nur Attribute; Objekte und Ereignisse verdrahtet diese Hülle
 * deshalb selbst über eine Ref.
 */
export function createElementComponent<P extends object, E extends Record<string, string>>(
  tag: `flowaudit-${string}`,
  options: ElementComponentOptions<P, E>,
) {
  type Props = P & EventHandlers<E> & BaseElementProps
  const Component = forwardRef<HTMLElement | null, Props>(function FlowauditElement(props, forwarded) {
    const element = useRef<HTMLElement | null>(null)
    useImperativeHandle<HTMLElement | null, HTMLElement | null>(forwarded, () => element.current, [])
    const values = props as Record<string, unknown>
    const base = props as BaseElementProps

    useLayoutEffect(() => {
      const node = element.current
      if (!node) return
      for (const name of options.properties) {
        if (values[name] !== undefined) Reflect.set(node, name, values[name])
      }
    })

    useLayoutEffect(() => {
      const node = element.current
      if (!node) return undefined
      const listeners = Object.entries(options.events).map(([handler, type]) => {
        const listener = (event: Event): void => {
          const callback = values[handler]
          if (typeof callback === 'function') callback(eventPayload(event), event)
        }
        node.addEventListener(type, listener)
        return () => node.removeEventListener(type, listener)
      })
      return () => listeners.forEach((remove) => remove())
    })

    return createElement(tag, { ref: element, class: base.className, style: base.style, id: base.id }, base.children)
  })
  Component.displayName = tag
  return Component
}
