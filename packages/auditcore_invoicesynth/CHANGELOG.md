# Changelog auditcore_invoicesynth

## 0.1.1 – Refaktorierung ohne Verhaltensänderung

Keine fachliche Änderung: alle bestehenden Tests laufen unverändert grün; ein
Datensatz (Seed 11, 58 Belege, alle Vorlagen, Scanrauschen) ist mit 0.1.0 und
0.1.1 erzeugt Datei für Datei bytegleich (Bilder, Ziel-JSON, Manifest).

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

| Messung | 0.1.0 | 0.1.1 |
|---|---|---|
| Funktionen mit McCabe > 10 | 6 | 0 |
| Module > 400 Zeilen | 1 | 0 |
| `Any`-Vorkommen | 67 | 60 |
| mypy --strict | sauber | sauber |
| Testabdeckung | 86 % | 88 % |

Keine Umbenennungen öffentlicher Namen.
