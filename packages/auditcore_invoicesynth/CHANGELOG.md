# Changelog auditcore_invoicesynth

Rekonstruiert aus der Git-Historie (Pull Requests #46, #48, #79).

## Unreleased

`train.cli --plan --image` schreibt das Job-Image (am besten per Digest) in den FlowAgent-Job.

Etappe E3 (janpow-ai): neues Modul `train.guard` (`ProgressFile` –
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
Pflichtabhängigkeit `auditcore_common==0.1.1`.

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
