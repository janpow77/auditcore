/**
 * Folder cards of the collection overview: per subfolder its name,
 * description and the diagrams it contains (recursively), plus one card for
 * the diagrams lying directly in the shown folder. Descriptions of diagrams
 * come from the diagram info (`flowaudit:diagrammInfo`, field
 * `beschreibung`), the only place the library keeps them.
 */

import type { DiagramCollection } from './collection'
import type { DiagramEntry, Folder } from './collectionData'

export interface CardDiagram {
  id: string
  name: string
  description: string
  status: string
  /** Activities and those with a legal basis (list view). */
  activities: number
  withLegalBasis: number
  /** Valid from, otherwise approval date (ISO, may be empty). */
  date: string
}

export interface FolderCard {
  /** `null` for the diagrams lying directly in the shown folder. */
  folderId: string | null
  name: string
  description: string
  count: number
  diagrams: CardDiagram[]
}

function cardDiagram(entry: DiagramEntry): CardDiagram {
  const info = entry.info
  return {
    id: entry.id,
    name: entry.name,
    description: info?.description?.trim() ?? '',
    status: String(info?.status ?? ''),
    activities: entry.excerpt.activities,
    withLegalBasis: entry.excerpt.activitiesWithLegalBasis,
    date: info?.validFrom || info?.approvedOn || '',
  }
}

function folderCard(collection: DiagramCollection, folder: Folder): FolderCard {
  const diagrams = collection.diagramsIn(folder.id, true).map(cardDiagram)
  return { folderId: folder.id, name: folder.name, description: folder.description?.trim() ?? '', count: diagrams.length, diagrams }
}

/**
 * Cards for the folder `folderId` (`null` = top level): one per subfolder,
 * then – if present – one for the diagrams directly in the folder. `name`
 * of that last card is empty; the view labels it („Ohne Ordner“ on the top
 * level, otherwise the folder itself).
 */
export function folderCards(collection: DiagramCollection, folderId: string | null): FolderCard[] {
  const cards = collection.subfolders(folderId).map((folder) => folderCard(collection, folder))
  const own = collection.inFolder(folderId).map(cardDiagram)
  if (own.length) cards.push({ folderId: null, name: '', description: '', count: own.length, diagrams: own })
  return cards
}
