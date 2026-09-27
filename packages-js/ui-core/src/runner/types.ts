/** Eintrag der Liste (Vertrag des Ports; an den REST-Vertrag des Backends anpassen). */
export interface RunnerItem {
  id: string
  label: string
}

/** Fachlogik hinter der Oberfläche; Vue und React rufen nur diesen Port auf. */
export interface RunnerPort {
  list: () => Promise<readonly RunnerItem[]>
}
