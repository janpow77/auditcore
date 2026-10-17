/** Alle Blattbeschreibungen der Zufallsfälle: Blattname → Startwert, Anzahl und Fallerzeugung. */
import { sheets as legacy } from './legacy.mjs'
import { sheets as musSingle } from './mus-single.mjs'
import { sheets as mus } from './mus.mjs'
import { sheets as ns } from './ns.mjs'
import { sheets as srs } from './srs.mjs'

export const sheets = { ...musSingle, ...mus, ...srs, ...ns, ...legacy }
