/** A diagram (or version) the current diagram can be compared with. */
export interface CompareSource {
  id: string
  name: string
  load: () => Promise<string>
}
