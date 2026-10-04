# Zuordnungsregeln und Profilpflege

## Ablauf `zuordnen(kennziffer, beschreibung)`

1. Kennziffer normalisieren (`kennziffer_normalisieren`): Ränder und
   geschützte Leerzeichen entfernen; leer, „-“ und „/“ werden zu
   „ohne Kennziffer“. Danach exakter Textvergleich („1.1“ ≠ „1.10“).
2. Kennziffer nicht in der Tabelle → „nicht zugeordnet“, keine Regel.
3. Gold-plating zunächst aus der Tabellenzeile.
4. Ist die Kennziffer *mehrdeutig*, werden ihre Schlüsselwortregeln der Reihe
   nach geprüft: Suchwort als Teilzeichenkette in der klein geschriebenen
   Beschreibung. Der erste Treffer gewinnt (Weg „Schlüsselwort“); „!GP“ im
   VBA-Ziel setzt Gold-plating (`gold_plating: true` im Profil).
5. Sonst gilt die Unterkategorie der Tabellenzeile (Weg „Kennziffer“); fehlt
   sie (8.3, 16 ohne Treffer, „ohne Kennziffer“), bleibt der Fall
   „nicht zugeordnet“.

`formal_zuordnen(beschreibung)` prüft die Formalregeln in derselben Weise;
erster Treffer gewinnt, sonst „nicht zugeordnet“. Die Kategorie ist der Text
vor dem ersten Punkt der Unterkategorie (`kategorie`).

## Kennziffertabelle (Profil 2026.10.1)

| Kennziffer | Unterkategorie | mehrdeutig | Schlüsselwortregeln |
|---|---|---|---|
| 8.1 | 4.1 | nein | – |
| 8.2 | 4.2 | nein | – |
| 8.5 | 4.5 | nein | – |
| 8.8 | 4.18 | nein | – |
| 7.1 | 10.1 | nein | – |
| 5.2 | 9.2 | nein | – |
| 5.1 | 4.16 | nein | – |
| 8.3 | offen | nein | – |
| 8.9 | 4.18 | ja | skonto, nachlass, rabatt → 4.2; tagegeld, frühstück, hotel → 4.15; aktivier → 4.18 |
| 16 | offen | ja | 1.720 stunden, stunden, personal → 4.14; unter 50 → 4.16 (Gold-plating) |
| ohne Kennziffer | offen | nein | – |

Die Formalregeln (30, Reihenfolge maßgeblich) stehen im Profil unter
`formalregeln`.

## Neue Profilversion

1. VBA-Modul ändern bzw. fachliche Änderung beschließen.
2. Profildatei mit neuer Version kopieren
   (`profile_data/efre.tof_2021_2027-<version>.json`), Metadaten anpassen.
3. Katalog und Regeln erzeugen: `python tools/vba_profil.py <modAKB_ToF.bas> --write`
   (schreibt in das in `PROFIL` genannte Profil) und mit `--check` prüfen.
4. Fingerabdruck in Tests und README nachziehen, Paritätstest lokal laufen
   lassen, neue Paketversion.

Veröffentlichte Profilversionen werden nie verändert.
