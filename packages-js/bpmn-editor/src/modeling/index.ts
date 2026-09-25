import BaseModelingModule from 'diagram-js/lib/features/modeling'
import LabelSupportModule from 'diagram-js/lib/features/label-support'
import AttachSupportModule from 'diagram-js/lib/features/attach-support'
import AlignElementsModule from 'diagram-js/lib/features/align-elements'
import SpaceToolModule from 'diagram-js/lib/features/space-tool'
import CroppingConnectionDocking from 'diagram-js/lib/layout/CroppingConnectionDocking'

import RulesModule from '../rules'
import OrderingModule from '../ordering'
import BehaviorModule from './behavior'
import BpmnFactory from './BpmnFactory'
import BpmnUpdater from './BpmnUpdater'
import ElementFactory from './ElementFactory'
import Modeling from './Modeling'
import BpmnLayouter from '../layout/BpmnLayouter'

export default {
  __depends__: [
    BaseModelingModule,
    LabelSupportModule,
    AttachSupportModule,
    AlignElementsModule,
    SpaceToolModule,
    RulesModule,
    OrderingModule,
    BehaviorModule,
  ],
  __init__: ['modeling', 'bpmnUpdater'],
  modeling: ['type', Modeling],
  bpmnFactory: ['type', BpmnFactory],
  bpmnUpdater: ['type', BpmnUpdater],
  elementFactory: ['type', ElementFactory],
  layouter: ['type', BpmnLayouter],
  connectionDocking: ['type', CroppingConnectionDocking],
}
