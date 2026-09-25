import BpmnRenderer from './BpmnRenderer'
import TextRenderer from './TextRenderer'

export default {
  __init__: ['bpmnRenderer'],
  bpmnRenderer: ['type', BpmnRenderer],
  textRenderer: ['type', TextRenderer],
}
