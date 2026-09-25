/**
 * Headless mode: read and write BPMN XML without a canvas.
 *
 * Used for everything that is not a running editor – collection overview,
 * neutralisation, reports, comparison of two versions. Based on
 * `bpmn-moddle` (MIT) with the FlowAudit descriptor.
 */

import { BpmnModdle } from 'bpmn-moddle'
import type { ModdleElement } from '../diagram/services'
import { flowauditModdleDescriptor } from '../schema/descriptor'
import { protectUnknownElements, restoreUnknownElements } from './unknownElements'

export interface ModdleInstance {
  create(type: string, attrs?: Record<string, unknown>): ModdleElement
  fromXML(xml: string, options?: Record<string, unknown>): Promise<{ rootElement: ModdleElement; warnings?: { message: string }[] }>
  toXML(element: ModdleElement, options?: Record<string, unknown>): Promise<{ xml: string }>
}

export interface LoadedDefinitions {
  definitions: ModdleElement
  moddle: ModdleInstance
  warnings: string[]
}

type ModdleConstructor = new (packages: Record<string, unknown>) => ModdleInstance

export function createModdle(extra: Record<string, unknown> = {}): ModdleInstance {
  const Constructor = BpmnModdle as unknown as ModdleConstructor
  return new Constructor({ flowaudit: flowauditModdleDescriptor, ...extra })
}

export async function loadDefinitions(xml: string, moddle: ModdleInstance = createModdle()): Promise<LoadedDefinitions> {
  const result = await moddle.fromXML(protectUnknownElements(xml), { lax: true })
  return {
    definitions: result.rootElement,
    moddle,
    warnings: (result.warnings ?? []).map((warning) => warning.message),
  }
}

export async function saveDefinitions(loaded: LoadedDefinitions, format = true): Promise<string> {
  const { xml } = await loaded.moddle.toXML(loaded.definitions, { format })
  return restoreUnknownElements(xml)
}

/** Empty diagram as in the audit_designer (`EMPTY_BPMN_XML`). */
export const EMPTY_DIAGRAM = `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                  xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
                  id="Definitions_1"
                  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_1" isExecutable="false">
    <bpmn:startEvent id="StartEvent_1" name="Start">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:task id="Task_1" name="Aufgabe bearbeiten">
      <bpmn:incoming>Flow_1</bpmn:incoming>
      <bpmn:outgoing>Flow_2</bpmn:outgoing>
    </bpmn:task>
    <bpmn:endEvent id="EndEvent_1" name="Ende">
      <bpmn:incoming>Flow_2</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Task_1" />
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="EndEvent_1" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1">
      <bpmndi:BPMNShape id="StartEvent_1_di" bpmnElement="StartEvent_1">
        <dc:Bounds x="180" y="160" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Task_1_di" bpmnElement="Task_1">
        <dc:Bounds x="270" y="138" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="EndEvent_1_di" bpmnElement="EndEvent_1">
        <dc:Bounds x="432" y="160" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_1_di" bpmnElement="Flow_1">
        <di:waypoint x="216" y="178" />
        <di:waypoint x="270" y="178" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_2_di" bpmnElement="Flow_2">
        <di:waypoint x="370" y="178" />
        <di:waypoint x="432" y="178" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>`
