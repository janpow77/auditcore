import ConnectionBehavior from './ConnectionBehavior'
import EventBehavior from './EventBehavior'
import LabelBehavior from './LabelBehavior'
import LaneBehavior from './LaneBehavior'
import ParticipantBehavior from './ParticipantBehavior'
import ShapeBehavior from './ShapeBehavior'
import ReplaceModule from '../../replace'

export default {
  __depends__: [ReplaceModule],
  __init__: [
    'laneBehavior',
    'participantBehavior',
    'eventBehavior',
    'labelBehavior',
    'connectionBehavior',
    'shapeBehavior',
  ],
  laneBehavior: ['type', LaneBehavior],
  participantBehavior: ['type', ParticipantBehavior],
  eventBehavior: ['type', EventBehavior],
  labelBehavior: ['type', LabelBehavior],
  connectionBehavior: ['type', ConnectionBehavior],
  shapeBehavior: ['type', ShapeBehavior],
}
