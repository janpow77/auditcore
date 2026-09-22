# Legacyverhalten und korrigierter Vertrag: Stichproben

Quellen, tatsächlich ausgeführt mit numpy 1.26.2, pandas 2.1.3, scipy 1.11.4
(`tools/capture_sampling_legacy.py`, 8883 Fälle):
`janpow77/flowstat@d665ac2` und `janpow77/audit-portal@d8eefa4`,
jeweils `sampling_service.py`. `auditcore_sampling.legacy` reproduziert alle
Fälle exakt: MUS-/SRS-Umfänge beider Anwendungen einschließlich Fehlern,
systematische MUS-Auswahl bei aufgezeichnetem Startwert, geschichtete MUS
und die Aufteilung der geschichteten SRS. Die Zufallsziehung selbst
(NumPy-Generator) bleibt beim Consumer.

| ID | Original | Neuer Vertrag | Begründung |
|---|---|---|---|
| SA-C01 | flowstat: `n = ceil(V·z²(1-r) / (M² + z²(1-r)))` – bei 515.000 € und Wesentlichkeit 50.000 € ist n = 1. audit-portal ersetzt das durch Poisson-Faktoren (n = 30) und nennt die alte Formel „mathematisch falsch“. | Beide als benannte Methoden `flowstat.mus_z_attribute` und `portal.mus_poisson`; keine Standardmethode; Warnhinweis bei der flowstat-Formel. | **HUMAN_DECISION_REQUIRED**: Welche Methode gilt, entscheidet die Fachseite. |
| SA-C02 | Unbekannte Konfidenzniveaus werden still als 95 % (z = 1,96) gerechnet. | Nur in der Methode definierte Niveaus; sonst Fehler. | Keine stillen Ersatzwerte. |
| SA-C03 | Negative Grundgesamtheit, Fehlerrate ≥ 1, Wesentlichkeit 0 ergeben Fehler, negative oder unsinnige Umfänge (flowstat). | Validierung der Eingaben in beiden Methoden. | Definierter Wertebereich. |
| SA-C04 | Zufall aus globalem NumPy-Zustand (flowstat ohne Seed; portal optional). | Zufall nur über ausdrücklich übergebenes `random.Random`; mit Seed reproduzierbar. | F-17 Reproduzierbarkeit. |
| SA-C05 | flowstat nimmt negative Werte in die kumulierte Summe und führt Positionen mehrfach. | Variante wählbar: `flowstat` (unverändert) oder `portal` (nur positive Werte, Ausschlüsse ausgewiesen, jede Position einmal). | Varianten nicht still vereinheitlicht. |

`statistics` und `sampling` sind getrennte Distributionen ohne gegenseitige
Abhängigkeit: Es gibt keinen gemeinsamen Vertrag. Die kleine
Summierungshilfe bleibt intern in `sampling` (Paketplan: „sampling →
statistics nur bei tatsächlich gemeinsamem numerischem Vertrag“).

Nicht übernommen (weitere Characterization nötig): Zwei-Perioden-Verfahren,
Differenzschätzung, Fehlerprojektion, nicht-statistische Auswahl.
