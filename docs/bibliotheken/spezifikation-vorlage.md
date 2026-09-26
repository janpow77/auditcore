# Vorlage: fachliche Spezifikation eines Pakets (Status „spezifiziert“)

Ein *charakterisiertes* Paket bildet das Verhalten seiner Quellanwendungen
nach und weist es mit aufgezeichneten Fällen nach. Das sagt, **was** das Paket
tut, aber nicht, **was es tun soll**. Die Spezifikation schreibt den gewollten
Vertrag fest: Sie trennt fachliche Regeln von zufällig mitgenommenem
Altverhalten und macht die Regeln als Eigenschaften prüfbar.

Status „spezifiziert“ im Paketkatalog heißt: charakterisiert **und**

1. `docs/spezifikation.md` im Paket mit den sechs Abschnitten unten,
2. jede Invariante als Hypothesis-Eigenschaftstest,
3. bekannte Altfehler als benannte, dokumentierte Legacy-Varianten,
4. ein `specification`-Block in `provenance.json` (Paketwurzel und die Kopie
   unter `src/<paket>/`), den `scripts/docs/specification.py` prüft.

Der Katalog-Generator (`python scripts/docs/catalog.py --write`) setzt den
Status nur, wenn der Block hält; ein Block, der nicht hält, lässt
`catalog.py --check` (und damit `tests/test_readmes.py`) scheitern.

## `provenance.json`

```json
"specification": {
  "document": "docs/spezifikation.md",
  "property_tests": ["tests/test_spezifikation.py"],
  "invariants": ["I1", "I2", "I3"],
  "legacy_variants": ["zvg.legacy_parse_de_number"]
}
```

- `invariants`: Kennungen `I<Zahl>`; jede steht im Dokument und in mindestens
  einer Testdatei (Testname oder Docstring, z. B. `def test_i3_...` mit
  „I3“ im Docstring).
- `legacy_variants`: Namen der Funktionen, Profile oder Schalter, die ein
  bekanntes Altverhalten bewusst weiterführen; jeder Name steht im Dokument.
  Leere Liste, wenn es keine gibt.
- Die Testdateien importieren Hypothesis (`hypothesis` im Extra `dev`).

## Aufbau von `docs/spezifikation.md`

```markdown
# Spezifikation <paket>

Stand: <Datum>, Paketversion <x.y.z>. Charakterisierung: <Verweis auf
Fixtures/Replay-Tests>.

## Zweck
Wofür das Paket da ist, für wen (Prüfbehörden aller ESI-Fonds, Anwendungen),
in zwei bis fünf Sätzen.

## Verträge
Je öffentliche Funktion/Klasse: Eingabe (Typen, Einheiten, Wertebereiche),
Ausgabe, Nebenwirkungen (Netz, Dateien, keine), Determinismus, Profile und
Versionen. Tabellarisch, wo es passt.

## Invarianten
Nummeriert I1, I2, …; jede als prüfbare Aussage mit Verweis auf den Test:
| Nr. | Invariante | Test |
|---|---|---|
| I1 | … | `tests/test_spezifikation.py::test_i1_…` |

## Fehlerfälle
Welche Eingaben mit welcher Fehlerklasse und Meldung abgelehnt werden; was
bewusst `None`/leer liefert statt zu raten.

## Abgrenzung
Was das Paket nicht tut und wer es stattdessen tut (Anwendung, anderes Paket).

## Bewusste Abweichungen vom Altverhalten
Tabelle: Altverhalten → gewolltes Verhalten → Legacy-Variante (Name) →
Nachweis. Altfehler, die aus Kompatibilitätsgründen weiter angeboten werden,
stehen hier mit ihrem Namen (z. B. `zvg.legacy_parse_de_number`) und dem
Hinweis, dass sie nicht für neue Aufrufer gedacht sind.
```

## Eigenschaftstests

- Eine Datei `tests/test_spezifikation.py` je Paket (mehrere erlaubt).
- `pytest.importorskip("hypothesis")` ist nicht nötig: Hypothesis gehört zum
  Extra `dev`, die CI installiert es.
- Keine Netzzugriffe, keine echten personenbezogenen Daten; Strategien
  erzeugen synthetische Werte.
- `@settings(deadline=None)` bei rechenintensiven Funktionen; die Zahl der
  Beispiele so wählen, dass die Paket-Suite schnell bleibt.
