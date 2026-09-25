# Changelog auditcore_invoicesynth

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
