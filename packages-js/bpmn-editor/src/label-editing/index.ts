import LabelEditing from './LabelEditing'

export default {
  __init__: ['labelEditing'],
  labelEditing: ['type', LabelEditing],
  directEditing: ['factory', (labelEditing: LabelEditing) => labelEditing, ['labelEditing']],
  labelEditingProvider: ['factory', (labelEditing: LabelEditing) => labelEditing, ['labelEditing']],
}
