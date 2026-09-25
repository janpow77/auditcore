/**
 * Brotkrumen-Navigation über den Ebenen (Prozess › Teilprozess › …).
 */

import { getLabel } from '../util/LabelUtil'
import { is } from '../util/ModelUtil'
import type { BpmnElement, Translate } from '../types'

export function renderBreadcrumbs(
  container: HTMLElement,
  chain: BpmnElement[],
  translate: Translate,
  onSelect: (root: BpmnElement) => void,
): void {
  container.innerHTML = ''
  container.style.display = chain.length > 1 ? '' : 'none'
  chain.forEach((root, index) => {
    const isCurrent = index === chain.length - 1
    const item = document.createElement(isCurrent ? 'span' : 'button')
    item.className = 'fa-breadcrumb'
    item.textContent = getLabel(root) || translate(is(root, 'bpmn:SubProcess') ? 'Sub-process' : 'Process')
    if (isCurrent) {
      item.setAttribute('aria-current', 'page')
    } else {
      ;(item as HTMLButtonElement).type = 'button'
      item.addEventListener('click', () => onSelect(root))
    }
    container.appendChild(item)
  })
}
