/**
 * Standardmodule des Editors (Reihenfolge ist relevant: spätere Module
 * überschreiben gleichnamige Dienste früherer Module).
 */

import SelectionModule from 'diagram-js/lib/features/selection'
import OverlaysModule from 'diagram-js/lib/features/overlays'
import ChangeSupportModule from 'diagram-js/lib/features/change-support'
import TooltipsModule from 'diagram-js/lib/features/tooltips'
import MoveModule from 'diagram-js/lib/features/move'
import ResizeModule from 'diagram-js/lib/features/resize'
import BendpointsModule from 'diagram-js/lib/features/bendpoints'
import ConnectionPreviewModule from 'diagram-js/lib/features/connection-preview'
import OutlineModule from 'diagram-js/lib/features/outline'
import InteractionEventsModule from 'diagram-js/lib/features/interaction-events'
import HoverFixModule from 'diagram-js/lib/features/hover-fix'
import AutoScrollModule from 'diagram-js/lib/features/auto-scroll'
import ZoomScrollModule from 'diagram-js/lib/navigation/zoomscroll'
import MoveCanvasModule from 'diagram-js/lib/navigation/movecanvas'

import DrawModule from './draw'
import ImportModule from './import'
import ModelingModule from './modeling'
import PaletteModule from './palette'
import ContextPadModule from './context-pad'
import PopupMenuModule from './popup-menu'
import LabelEditingModule from './label-editing'
import CopyPasteModule from './copy-paste'
import SearchModule from './search'
import MinimapModule from './minimap'
import KeyboardModule from './keyboard'
import GridModule from './grid'
import SnappingModule from './snapping'
import AutoPlaceModule from './auto-place'
import AutoResizeModule from './auto-resize'
import DrilldownModule from './drilldown'

export const CORE_MODULES: unknown[] = [
  SelectionModule,
  OverlaysModule,
  ChangeSupportModule,
  InteractionEventsModule,
  OutlineModule,
  DrawModule,
  ImportModule,
]

export const MODELING_MODULES: unknown[] = [
  ModelingModule,
  TooltipsModule,
  MoveModule,
  ResizeModule,
  BendpointsModule,
  ConnectionPreviewModule,
  HoverFixModule,
  AutoScrollModule,
  ZoomScrollModule,
  MoveCanvasModule,
  PaletteModule,
  ContextPadModule,
  PopupMenuModule,
  LabelEditingModule,
  CopyPasteModule,
  SearchModule,
  KeyboardModule,
  GridModule,
  SnappingModule,
  AutoPlaceModule,
  AutoResizeModule,
  DrilldownModule,
  MinimapModule,
]

export const DEFAULT_MODULES: unknown[] = [...CORE_MODULES, ...MODELING_MODULES]
