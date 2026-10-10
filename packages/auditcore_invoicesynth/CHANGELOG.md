# Changelog auditcore_invoicesynth

## Unveröffentlicht

Diagnosesatz T2d (`test_layout_holdout_d`, `build-diagnostics --sets holdout_d`):
versiegelter Unbekannt-Test mit zwei neuen Vorlagen (`holdout_d_zahlinfo`,
Kennungen in einer Tabelle neben dem Titel und Summen als Steuertabelle;
`holdout_d_ueberweisung`, Fuß nach Art eines Überweisungsträgers mit
QR-Platzhalter) – IBAN, BIC, USt-IdNr. und Gesamtbetrag an Orten, die keine
andere Vorlage nutzt – und eigener Schrift IBM Plex Serif (SIL OFL 1.1,
Debian `fonts-ibm-plex`). Vorlagen und Schrift kommen in keinem `build`-Plan
und keinem anderen Diagnosesatz vor (Tests). Plan-Hashes v1–v4, Plan-Hash
T2-gemischt + T2b (`ecf8ef57…`) und T2c (`42acfce4…`) sowie Datensatz-Hashes
kleiner Probesätze gegen `main` unverändert; die Standardauswahl von
`build-diagnostics` bleibt T2-gemischt + T2b. Der volle Satz (Seed 42, 500
Belege) ist gebaut und mit seinem Hash in `docs/donut-verlauf/holdout-d.json`
festgehalten. **T2d ist ab jetzt der maßgebliche Unbekannt-Test; T2c gilt ab
Stufe 8 als bekannt. T2d erst zur Abschlussbewertung von Stufe 8 ansehen bzw.
bewerten.**

Generatorvariante `v4` (`build --variety v4`; `v1`, `v2`, `v3` bleiben bitgleich,
Plan-Hashes `3da7d6e1…`, `c50af53a…`, `1250705c…` und Datensatz-Hashes kleiner
Probesätze gegen `main` geprüft; T2 und die Diagnosesätze unverändert): `v3` plus,
aus eigenen Zufallsfolgen je Beleg und als Konzepte statt Nachbau von T2b,
(1) hervorgehobener Rechnungsbetrag (rund 20 %): groß und fett, Beschriftung
(„Rechnungsbetrag“, „Zu zahlen“, „Zahlbetrag“, „Gesamtbetrag“, „Amount due“,
„Total due“) über oder vor dem Wert, oben rechts im Kopf, rechts neben dem
Empfänger, mittig unter der Tabelle oder unten links im Kasten; Netto und USt
bleiben im Summenblock; (2) gemischte Summenfolge (rund 25 %): Gesamtbetrag
zuerst mit „davon Netto/USt“, USt vor Netto oder Gesamtbetrag in der Mitte,
Beschriftung links vom oder über dem Wert; (3) Kennungen klein in 2–3
Fußzeilenspalten (rund 20 %): Steuernummer, USt-IdNr., Bank, IBAN mit oder ohne
Gruppierung und Beschriftung „IBAN“, „Konto (IBAN)“ oder „IBAN-Nr.“;
(4) weitere Ziffernschriften Nimbus Sans, URW Bookman und P052
(`fonts-urw-base35`, nur `v4`, rund 30 % der Belege, nie Holdout). Neue Module
`variety_v4` und `layout_v4`; Plan-Hash `v4` (Seed 42, 20000/1000/1000/500, alle
Katalogschriften) `42a03538…`.

Diagnosesatz T2c (`test_layout_holdout_c`, `build-diagnostics --sets holdout_c`):
versiegelter Unbekannt-Test mit zwei neuen Vorlagen (`holdout_c_brief`,
Geschäftsbrief mit Kopfdaten im Fließtext; `holdout_c_balken`, farbiger
Seitenbalken) – Gesamtbetrag anders platziert als in allen übrigen Vorlagen –
und eigener Schrift C059 (`fonts-urw-base35`, AGPL-3.0 mit Schrift-Ausnahme).
Vorlagen und Schrift kommen in keinem `build`-Plan und keinem anderen
Diagnosesatz vor (Tests). Plan- und Datensatz-Hashes von v1/v2/v3 sowie der
Diagnosesatz T2-gemischt + T2b (Seed 42, je 500: `997a04c1104f073d…`) bleiben
gleich; die Standardauswahl von `build-diagnostics` bleibt T2-gemischt + T2b.
Der volle Satz (Seed 42, 500 Belege) ist gebaut und mit seinem Hash in
`docs/donut-verlauf/holdout-c.json` festgehalten. **T2c ist ab jetzt der
maßgebliche Unbekannt-Test; T2 und T2b gelten ab Stufe 7 als bekannt (ihre
Konzepte fließen ins Training ein). T2c erst zur Abschlussbewertung von Stufe 7
ansehen bzw. bewerten.**

Training: Lernrate und Warm-up für Weitertraining einstellbar
(`--learning-rate`, `--warmup-steps`; `OVERRIDABLE`/`override_args` geben sie
an den FlowAgent-Job weiter). `TrainConfig.validate` verlangt
`0 < learning_rate ≤ 1e-2` und `warmup_steps ≥ 0`. Beide Werte stecken wie
bisher im `config_hash`, eine Wiederaufnahme mit abweichender Lernrate oder
abweichendem Warm-up scheitert daher mit `ResumeMismatch`. Die Hashes der
Profile ohne Schalter bleiben unverändert (Test mit festen Sollwerten). Das
Job-Image muss für die neuen Schalter neu gebaut sein.

Generatorvariante `v3` (`build --variety v3`; `v1` und `v2` bleiben bitgleich,
Plan- und Datensatz-Hashes gegen `main` geprüft): `v2` plus, aus eigener
Zufallsfolge je Beleg, (1) Summenorte – wie die Vorlage, unten links, umrahmter
Kasten rechts zwischen Kopfdaten und Positionstabelle oder waagerechter Streifen
Netto | USt | Gesamtbetrag (Beschriftung über dem Wert, ohne Hinterlegung)
zwischen Kopf und Tabelle, je rund 12 % der Belege; (2) waagerechte Kopfdaten
(neues Modul `layout_extra`): 3–5 Spalten mit Beschriftung über dem Wert, mit
oder ohne Rahmen, ein- oder zweizeilig, Reihenfolge wie `v2`, Kundennummer und
Seite als Zierzellen ohne Zielfeld, rund 16 % der Belege; (3) die
Positionsspalte heißt nie „Gesamt“, damit nur der Gesamtbetrag so beschriftet
ist. Der Layout-Holdout T2 bleibt bitgleich zu `v1`/`v2`; Holdout- und
Diagnosevorlagen und -schriften kommen in train/validation/T1 nicht vor.
**Ab v3 ist T2 (holdout_kompakt) kein reiner Unbekannt-Test mehr; maßgeblich
sind T2b und T2-gemischt.**

Plausibilität: Beträge (netto, USt, brutto) gelten nur noch als plausibel, wenn alle
drei lesbar sind und `netto + USt = brutto` stimmt. Fehlt einer, geht der Beleg zur
Prüfung (Befund Diagnosesatz T2b: falsche Gesamtbeträge ohne Steuerzeile wurden
sonst übernommen).

Diagnosesätze (nur Bewertung, nie Training): neues Kommando
`build-diagnostics` (Modul `diagnostics`) schreibt ausschließlich
`test_layout_holdout_shuffled` (T2-gemischt: T2-Vorlagen und DejaVu Serif,
Kopfdaten-Reihenfolge und Weglassen des Lieferdatums aus
`variety.choose_variety`, Beschriftungen wie T2) und `test_layout_holdout_b`
(T2b: neue Vorlage `holdout_b_tabelle` – Absender mittig, Kopfdaten als
umrahmte Tabelle rechts neben dem Empfänger mit Beschriftung links vom Wert in
eigener Reihenfolge, Summenstreifen über der Positionstabelle – und Schrift
URW Gothic aus `fonts-urw-base35`, AGPL-3.0 mit Schrift-Ausnahme) in ein
eigenes Verzeichnis mit eigenem Manifest. `verify` und
`train.evaluate --dataset <dir> --splits <satz>` lesen es unverändert.
Diagnosevorlage und -schrift sind aus allen Plänen von `build` ausgeschlossen;
Plan- und Datensatz-Hashes von v1 und v2 bleiben gleich. Die Schriftsuche
findet zusätzlich `.otf`-Dateien. Ein Test hält die Plan-Hashes von v1 und v2
(Seed 42, 20000/1000/1000/500) gegen den Stand vor den Diagnosesätzen fest.

Bewertung (Runde A nach Stufe 4): `train.evaluate` repariert ein ausgelassenes
`<s_supplier>` (`schema.repair_structure`), misst die Falschwert-Quote nach
Plausibilität über das neue Modul `plausibility` (Prüfziffern IBAN und
USt-IdNr. DE/AT, Datum, Rechnungsnummer, netto + USt = brutto; Regeln wie in
`auditcore_documents`) und bewertet mit `--from-predictions` gespeicherte
Vorhersagen ohne Modell und ohne GPU neu.

Generatorvariante `v2` für Stufe 5 (`build --variety v2`, Standard bleibt
`v1` bitgleich): Kopfdaten in wechselnder Reihenfolge, Lieferdatum teils
weggelassen, Fälligkeit öfter im Fließtext, weitere Beschriftungssynonyme,
neue Trainingsvorlagen `kopf_zeile` und `kopf_kasten`, USt-IdNr. teils unter
dem Absendernamen, seltene Bildverschlechterung (`augment.degrade_page`) und
Schrift Lato. Der Layout-Holdout (T2) bleibt bitgleich zu `v1`.

## 0.2.1 – 2026-10-03

Gemeinsamer Release v0.6.0 mit aktuellem Paketstand, Dokumentation und
exakt gebundenen internen Abhängigkeiten.

Rekonstruiert aus der Git-Historie (Pull Requests #46, #48, #79).

## 0.2.0 – 2026-09-26 – Paketstand für Release v0.4.2

`train.cli --plan --image` schreibt das Job-Image (am besten per Digest) in den FlowAgent-Job.

Etappe E3 (GPU-Rechner): neues Modul `train.guard` (`ProgressFile` –
`progress.json` atomar, Herzschlag in Lade-/Checkpoint-Phasen;
`StopRequest` – SIGTERM/SIGINT → Checkpoint und Exit 0, harte Frist 90 s;
`NonFiniteLoss`, `OutOfMemory`, `TooManyBadSamples` mit Exit-Codes 3/4/6).
Der Torch-Adapter verwirft NaN/OOM-Schritte vor `optimizer.step`, überspringt
unlesbare Bilder (höchstens 1 %) und akzeptiert `pytorch_model.bin` als
Startgewichte. Neue Schalter `--image-size`, `--seed`, `--epochs`,
`--per-device-batch`, `--grad-accum`, `--stop-deadline`; der FlowAgent-Job
(Schema `flowagent-job/2`) trägt je Lauf das vollständige Kommando,
`--base-model-sha256`, Einhängepunkte und Exit-Codes. Neu
`train.evaluate` (Kandidat + Donut-CORD auf T1/T2) und
`docker/train` (Job-Image).

Keine Verhaltensänderung. Datei-SHA-256 (`fonts.sha256_file`,
`train.torch_backend.sha256_file`, Checkpoint- und Datensatzprüfsummen),
Datensatz-Hash, Plan-Hash, Konfigurations-Hash, Lauf-ID sowie `parse_rate`
und `normalize_identifier` kommen aus `auditcore_common` (`hashing`,
`numeric.parse_percent_rate`, `text.compact_upper`). Alle Hashes und
Ergebnisse unverändert (`tests/test_common_parity.py`). Neue
Pflichtabhängigkeit `auditcore_common==0.2.0`.

Pins: `auditcore_invoicegenerator==0.2.3`.

## 0.1.2 – 2026-09-26 – Paketstand für Release v0.4.1

Keine Verhaltensänderung. Pin `auditcore_invoicegenerator==0.2.2`; README-Installationshinweis auf v0.4.0.

## 0.1.1 – Refaktorierung ohne Verhaltensänderung

Keine fachliche Änderung: alle bestehenden Tests laufen unverändert grün; ein
Datensatz (Seed 11, 58 Belege, alle Vorlagen, Scanrauschen) ist mit 0.1.0 und
0.1.1 erzeugt Datei für Datei bytegleich (Bilder, Ziel-JSON, Manifest); nach
den weiteren Schnitten erneut geprüft (Seed 11, 58 Belege, DPI 72/96: 71
Dateien SHA-256-gleich, darunter 53 verfremdete Seiten, 16 zweiseitige Belege
und alle drei Fehlerfälle).

- `layouts.py` (575 Zeilen) nach Verantwortung geschnitten:
  `layout_model.py` (Zeichenfläche, Vorlagenparameter, Formatwahl),
  `layout_head.py` (Kennzeichnung, Absender, Empfänger, Kopfdaten),
  `layout_body.py` (Tabelle, Summen, Zahlung, Bank, Fußzeile). `layouts`
  re-exportiert alle bisherigen Namen und enthält `render_layout`.
- Summenblock in spaltenförmige und untenliegende Anordnung getrennt
  (Spaltenlage als Tabelle), `augment_page`, `evaluate`, `discover_fonts`,
  `train.cli.main` und `TorchDonutBackend.setup` in kurze Schritte zerlegt.
- Typen: Pillow-Bilder als `PIL.Image.Image`, Modulobjekte als `ModuleType`,
  `render_pages` mit `SynthInvoice`/`Variant` statt `Any`.
- Neue Tests für die Schritte des Trainings-CLI im Prozess.
- Funktionen über 60 Zeilen geteilt: `build_dataset` (`_write_sample`,
  `_manifest`), `enrich` (`_positions`, `_vat_lines`, `_printed_total`,
  `_dates`, `_source`), `cli.main` (`_parser`, `_plan_or_build`, `_verify`,
  `_evaluate`), `run_training` (`_resume`, `_log_step`); Reihenfolge der
  Zufallsziehungen und Dateischreibvorgänge unverändert.
- Eingaben von `flatten`, `evaluate` und des Sequenz-Encoders `object` statt
  `Any`.

| Messung (nur `src/`) | 0.1.0 | 0.1.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 6 | 0 |
| Module > 400 Zeilen | 1 | 0 |
| Funktionen > 60 Zeilen (Code-Gate) | 7 | 0 |
| `Any` (Textvorkommen / Code-Gate `any_usages`) | 67 / 54 | 55 / 41 |
| mypy --strict | sauber | sauber |
| Testabdeckung | 86 % | 88 % |

Code-Gate-Baseline (`quality/baseline.json`) für das Paket abgesenkt.

Keine Umbenennungen öffentlicher Namen.

## 0.1.0 – 2026-09-24

- Neues Paket (Entscheidung E1): Anreicherung der Datensätze aus
  `auditcore_invoicegenerator` mit prüfziffer-gültigen fiktiven IBAN/BIC und
  USt-IdNr./UID (E5), Steuerschemata DE/AT, zehn Vorlagen (zwei nur im
  Layout-Holdout), Beschriftungs-Synonyme, deutsche Zahlen- und Datumsformate,
  freie Systemschriften mit SHA-256 im Manifest (nicht eingebettet),
  seed-bestimmtes Scanrauschen, Donut-Ausgabe (`metadata.jsonl`, Manifest,
  Datensatz-Hash), Ziel-JSON `auditcore_invoice_v1` nur mit Kopf- und
  Summenfeldern (E8) und Bewertung mit den Abnahmeschwellen aus E6 (#46).
- Beschriftung und Wert überlappen in Kopfspalte und Summenblock nicht mehr
  (Sichtprüfung des Piloten, #46).
- Donut-Nachtraining vorbereitet, ohne echtes Training (Etappe E3):
  `auditcore_invoicesynth.train` mit Profilen, Rechenortwahl,
  Checkpoints und Wiederaufnahme, Extra `[train]` (#48).
- 2026-09-25: Abhängigkeit auf `auditcore_invoicegenerator==0.2.1` angehoben
  (#79), ohne Versionsänderung dieses Pakets.
