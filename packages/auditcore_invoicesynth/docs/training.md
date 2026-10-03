# Donut-Nachtraining (Etappe E3)

Stand 26.09.2026. Plan: `docs/architecture/DONUT_OCR_PLAN.md` 2c/2c-bis/2d,
Entscheidungen E1–E9 („Donut alle Empfehlungen“). Werkzeug, Job-Image,
Pilot- und Volldatensatz, Startmodell und FlowAgent-Job für den GPU-Rechner sind
vorbereitet (Abschnitt [Stand E3 auf dem GPU-Rechner](#stand-e3-auf-dem-gpu-rechner)).
Das Training selbst startet ausschließlich über den FlowAgent.

## Bausteine (`auditcore_invoicesynth.train`)

| Baustein | Inhalt |
|---|---|
| `profiles` | `donut_train_janpow_ai` (Batch 4 je GPU, Akkumulation 2, AdamW, bf16, ≥ 14 GiB frei je Karte), `donut_train_8gb` (Batch 1, Akkumulation 16, 8-bit-AdamW, Gradient Checkpointing, ≥ 6,5 GiB frei), `cpu_smoke`; Startmodell `naver-clova-ix/donut-base@a959cf33…`; `config_hash` |
| `choose_topology` | aus GPU-Telemetrie: gleiche Kartenklasse ≥ 16 GiB → DDP (`torchrun --nproc_per_node=2`), ungleiche Karten → zwei Läufe (1280×960 / 1536×1152, Seed+1), eine Karte → single, keine → `unavailable` (kein stiller Rückfall auf die Arbeitsstation) |
| `checkpoint` | atomar (`checkpoint-N.tmp` → fsync → `CHECKSUMS.sha256` → rename), alle 200 Schritte **oder** 15 Minuten, `save_total_limit=3`; beim Start neuester gültiger Checkpoint, Unvollständiges/Beschädigtes nach `rejected/` (mit Grund), Lauf-ID/Datensatz-/Konfigurations-Hash müssen passen |
| `loop` | deterministische Datenreihenfolge je Epoche (`Random(f"{seed}:{epoch}")`), Mikrobatches je Rang, JSON-Zeilen-Protokoll (Schritt, Epoche, Loss, VRAM-Spitze, Temperatur); Protokollzeilen nach dem letzten Checkpoint wandern beim Wiederaufnehmen nach `rejected/` |
| `torch_backend` (Extra `train`) | `VisionEncoderDecoderModel` nur aus lokalem Verzeichnis (`local_files_only`, optional SHA-256), Task-Token/Feld-Tags aus `schema.special_tokens()`, bf16-Autocast (CUDA), Gradient Checkpointing, AdamW/8-bit-AdamW, Cosinus-Scheduler mit Warm-up, DDP bei `WORLD_SIZE>1` (nur Rang 0 schreibt), Zustand: safetensors, Tokenizer, Prozessor, Optimierer, Scheduler, RNG |
| `guard` | `progress.json` (atomar; Felder `schritt`, `schritte_gesamt`, `epoche`, `loss`, `lr`, `vram_mb`, `gpu_temp_c`, `zustand` laeuft/fertig/fehler/abgebrochen, `fehler`, `letzter_checkpoint`, `aktualisiert`, zusätzlich `phase`, `uebersprungene_beispiele`); Herzschlag alle 30 s nur in Lade-/Checkpoint-Phasen (höchstens 30 min), damit ein echter Hänger auffällt; SIGTERM/SIGINT → nach dem laufenden Schritt Checkpoint, `zustand=abgebrochen`, Exit 0, sonst nach 90 s harter Abbruch (Exit 5); NaN/Inf-Loss (Exit 3) und CUDA-OOM (Exit 4) verwerfen den Schritt vor `optimizer.step` und sichern den letzten guten Stand; unlesbare Bilder werden übersprungen und gezählt, über 1 % → Exit 6 |
| `ops` | VRAM-Startprüfung (`nvidia-smi`), GPU-Temperatur (alle 30 s), systemd-Vorlage, FlowAgent-Jobbeschreibung (Schema `flowagent-job/2`: Kommando je Lauf mit Profil-Abweichungen, Einhängepunkte, Exit-Codes) |
| `evaluate` | ein Befehl für Kandidat (neuester gültiger Checkpoint) und Donut-CORD auf `test_synthetic` (T1) und `test_layout_holdout` (T2): Vorhersagen je Satz als JSONL, Kennzahlen und Abnahmeprüfung E6 als JSON |

## Aufrufe

```bash
# Rechenort planen (Telemetrie der Spokes als JSON) → FlowAgent-Job
auditcore-invoicesynth-train --profile donut_train_janpow_ai --dataset ds/ \
  --plan --gpus-json gpus.json > job.json
# Training; setzt automatisch am neuesten gültigen Checkpoint fort
torchrun --nproc_per_node=2 -m auditcore_invoicesynth.train.cli \
  --profile donut_train_janpow_ai --dataset ds/ --run-dir runs/r1 --base-model-dir base/donut-base
# Rückfall auf die Arbeitsstation nur ausdrücklich
auditcore-invoicesynth-train --profile donut_train_8gb --dataset ds/ --run-dir runs/r1-fallback \
  --base-model-dir base/donut-base
# systemd --user-Dienst (xtts wird für den Rückfall auf die Arbeitsstation pausiert, E7)
auditcore-invoicesynth-train --profile donut_train_8gb --systemd-unit --dataset ds/ \
  --run-dir runs/r1-fallback --base-model-dir base/donut-base \
  > ~/.config/systemd/user/auditcore-donut-train.service
```

Die Lauf-ID ist `sha256(Datensatz-Hash:Konfigurations-Hash)[:16]`; ein
Neustart desselben Auftrags findet dadurch seine Checkpoints wieder.

## Job-Image

`ghcr.io/janpow77/auditcore-donut-train:cu128` (zusätzlich `cu128-g<commit>`),
gebaut vom Workflow `.github/workflows/donut-train-image.yml` aus
`docker/train/Dockerfile`:

- Basis `nvidia/cuda:12.8.1-base-ubuntu24.04` per Digest (nur die
  Treiber-Umgebung; CUDA 12.8, cuDNN und NCCL bringt das torch-Rad mit);
- torch 2.11.0+cu128 (sm_120 für Blackwell), transformers 5.17.0 und die
  übrigen Laufzeitpakete exakt gepinnt (`docker/train/requirements-train.txt`);
- `auditcore_invoicesynth` als Rad aus dem Repository-Stand (lokale Version
  `0.1.2+g<commit>`), `auditcore_common`/`auditcore_invoicegenerator`/
  `auditcore_dummygenerator` hashgebunden aus v0.4.1;
- Schriften DejaVu, Liberation und Noto (Datensatzbau im Image möglich);
- `/licenses`: LICENSE/NOTICE, `docs/provenance/donut.json`,
  `THIRD_PARTY.md` und die beim Bau erzeugte Paketliste mit Lizenzen;
  Modelle, Datensätze und Checkpoints sind **nicht** enthalten;
- kein ENTRYPOINT: der Job gibt `python -m auditcore_invoicesynth.train.cli …`
  vor; `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `HOME=/tmp`.

## Nachweise dieser Runde (CPU, Arbeitsstation, ohne GPU)

| Prüfung | Ergebnis |
|---|---|
| Stromausfall mit Ersatzmodell: Abbruch nach Schritt 6, halb geschriebener Checkpoint 8 | Wiederaufnahme ab 4, Loss-Verlauf und Endzustand identisch mit ununterbrochenem Lauf (`test_power_loss_resume_matches_uninterrupted_run`) |
| `kill -9` während eines laufenden Prozesses | Wiederaufnahme ab letztem gültigem Checkpoint, Schritte 1–40 lückenlos, Loss je Schritt identisch (`test_kill_9_during_training_resumes_from_last_valid_checkpoint`) |
| Winziges Donut-Modell (Swin 2 Stufen, MBart 1 Schicht, Zeichen-Tokenizer), 6 Schritte CPU, Abbruch nach 3, Wiederaufnahme | Loss von Schritt 3 vor/nach Wiederaufnahme gleich; Checkpoint enthält `model.safetensors`, Optimierer, Scheduler, RNG, Prüfsummen (`test_cpu_smoke_with_tiny_donut_model`; übersprungen ohne Extra `train`) |
| DDP mit `torchrun --nproc_per_node=2` (gloo, CPU) | 2 Ränge, ein Checkpoint von Rang 0 (manuell ausgeführt) |
| Rauchtest-Checkpoint in `auditcore_documents.LocalDonut` geladen | SHA-256 geprüft, Inferenz läuft (Zufallsausgabe), falsche Prüfsumme → `DONUT_MODEL_HASH_MISMATCH` (manuell ausgeführt) |

Getestet mit torch 2.14.0+cpu, transformers 5.17.0.

## Stand E3 auf dem GPU-Rechner

Verzeichnisse auf dem GPU-Rechner (Host → Container):

| Host | Container | Inhalt |
|---|---|---|
| `$HOME/donut/datasets/pilot-192e329e531ba160` | `/data/192e329e…` (ro) | Pilot 2 000 Belege (1 600/150/150/100) |
| `$HOME/donut/datasets/full-34581be2880d00f4` | `/data/34581be2…005d` (ro) | Vollsatz 20 000/1 000/1 000/500 (22 487 Trainingsbilder, 8,1 GB) |
| `$HOME/donut/base/donut-base` | `/srv/auditcore/donut/base/donut-base` (ro) | Startmodell, Revision a959cf33…, `SOURCE.json`, `SHA256SUMS` |
| `$HOME/donut/base/donut-cord-v2` | `/srv/auditcore/donut/base/donut-cord-v2` (ro) | nur Vergleich (Revision 8003d433…) |
| `$HOME/donut/runs` | `/srv/auditcore/donut/runs` (rw) | Läufe `<lauf-id>-0` (GPU 0) und `<lauf-id>-1` (GPU 1) |
| `$HOME/donut/eval` | `/srv/auditcore/donut/eval` (rw) | Bewertungsberichte |
| Arbeitsstation `$HOME/donut/checkpoints-mirror/<lauf-id>/` | – | Checkpoint-Spiegel (rsync durch den FlowAgent) |

Ohne Telemetrie adressiert die Planung den Spoke aus `AUDITCORE_DONUT_SPOKE`
(Vorgabe `gpu-host`); das Spiegelziel kommt aus `AUDITCORE_DONUT_MIRROR`
(z. B. `<spiegel-host>:donut/checkpoints-mirror`, ohne Angabe kein Spiegel).

| Schritt | Stand |
|---|---|
| GPU-Rechner als Spoke, Telemetrie beider GPUs | RTX 5070 Ti (GPU 0) und RTX 5060 Ti (GPU 1), je 16 GB, Treiber 595.84 → `choose_topology`: **parallel** (zwei Läufe) |
| Job-Image | `ghcr.io/janpow77/auditcore-donut-train@sha256:fe43cb907c53cd6eedac1e0a167aceb283aaf00f3bf2d3cd411be5f15880d466` (Pilot-Stand `0.1.2+g54007a1606fc`, öffentlich, anonym ziehbar); spätere Builds verschieben nur den Tag `cu128`, der Job nennt den Digest (`--image`) |
| Startmodell | `pytorch_model.bin` SHA-256 `749f6e487d0cdbd7362d8b6a909174b93506d8631da0d15a6108bb6512ad5f48` (gleich dem Git-LFS-Objekt auf Hugging Face; `donut-base@a959cf33` hat keine safetensors-Datei) |
| Pilot-Datensatz | Hash `192e329e531ba16028c314f36007737637fdaaf59e0eb66095fb84a4056174f3`; zweimal unabhängig gebaut, gleicher Hash; `verify` ok |
| Vollsatz | Seed 42, Hash `34581be2880d00f4bb293fb0fc368770c2af61c7a748cdb55cf4c74a8324005d`, `verify` ok, Bauzeit 96 min (ein CPU-Kern) |
| FlowAgent-Jobs | `~/donut/job-pilot.json` (Lauf-ID `6cb8d70e0befc10e`, 3 Epochen, 675 Schritte je Lauf) und `~/donut/job-voll.json` (Lauf-ID `2835be42bd3c1e1a`, 6 Epochen, 16 866 Schritte je Lauf); Topologie jeweils `parallel`; Varianten `*-gpus-live.json` mit der Live-Telemetrie |
| Bewertung | `~/donut/tools/pilot-bewerten.sh [job.json]` (CPU; beide Läufe gegen T1/T2, Donut-CORD einmal; `LIMIT`/`MAXLEN`/`THREADS` optional) |
| FlowAgent-Seite (`train:donut`, GPU-Freigabe, Spiegel) | Session `flow-agent-f1`; Auftragsdateien `~/.config/flow-agent/gpu-auftraege/{donut-pilot,donut-voll}.json` |
| Morgenprüfung | `$HOME/donut/tools/morgen-pruefung.sh` (nur lesend: Zustand, Loss-Verlauf, Tempo, Restzeit, Stillstand, verworfene Checkpoints, GPUs, Dienste) |

Datensatz erzeugen (CPU, reproduzierbar; Umgebung aus den Release-Rädern v0.4.1,
Pillow 12.0.0, Schriften gepinnt):

```bash
cd ~/donut/tools
python3 -m venv synth-venv && synth-venv/bin/pip install -r requirements-synth.txt pillow==12.0.0
synth-venv/bin/auditcore-invoicesynth fonts   # → font-pins.json (Dateiname → SHA-256)
synth-venv/bin/auditcore-invoicesynth build --seed 42 --font-pins font-pins.json \
  --out ~/donut/datasets/_building-pilot-seed42          # Pilot (Standardaufteilung)
synth-venv/bin/auditcore-invoicesynth build --seed 42 --font-pins font-pins.json \
  --train 20000 --validation 1000 --test-synthetic 1000 --test-layout-holdout 500 \
  --out ~/donut/datasets/_building-full-seed42           # Vollsatz
synth-venv/bin/auditcore-invoicesynth verify ~/donut/datasets/pilot-192e329e531ba160
```

Job planen (echte Telemetrie, nur lesend; im Image, ohne GPU):

```bash
nvidia-smi --query-gpu=index,name,memory.total,memory.free --format=csv,noheader,nounits \
  | python3 -c 'import json,sys; print(json.dumps([dict(index=int(i), name=n.strip(), memory_total_mib=int(t), memory_free_mib=int(f), host="gpu-host") for i,n,t,f in (l.split(",") for l in sys.stdin)]))' \
  > ~/donut/gpus-live.json   # frei = gesamt − 512 MiB → gpus-nach-freigabe.json
docker run --rm --user 1000:1000 -v $HOME/donut:$HOME/donut \
  ghcr.io/janpow77/auditcore-donut-train@sha256:fe43cb907c53cd6eedac1e0a167aceb283aaf00f3bf2d3cd411be5f15880d466 \
  python -m auditcore_invoicesynth.train.cli --profile donut_train_janpow_ai \
  --dataset $HOME/donut/datasets/pilot-192e329e531ba160 --epochs 3 \
  --base-model-dir $HOME/donut/base/donut-base --run-dir $HOME/donut/runs \
  --base-model-sha256 749f6e487d0cdbd7362d8b6a909174b93506d8631da0d15a6108bb6512ad5f48 \
  --image ghcr.io/janpow77/auditcore-donut-train@sha256:fe43cb907c53cd6eedac1e0a167aceb283aaf00f3bf2d3cd411be5f15880d466 \\
  --plan --gpus-json $HOME/donut/gpus-nach-freigabe.json > ~/donut/job-pilot.json
```

Die Telemetrie zeigt belegte Karten (Ollama/Whisper); der Plan wird deshalb mit
dem Speicher **nach** der GPU-Freigabe durch den FlowAgent gerechnet (frei =
gesamt − 512 MiB). Mit belegten Karten meldet `--plan`
`WAITING_FOR_COMPUTE` (kein stiller Rückfall).

Ein Lauf im Container (so startet ihn der FlowAgent, je Karte ein Container):

```bash
docker run --rm --gpus device=1 --user 1000:1000 --ipc=host --stop-timeout 120 \
  -v $HOME/donut/datasets/pilot-192e329e531ba160:/data/<hash>:ro \
  -v $HOME/donut/base/donut-base:/srv/auditcore/donut/base/donut-base:ro \
  -v $HOME/donut/runs:/srv/auditcore/donut/runs \
  ghcr.io/janpow77/auditcore-donut-train@sha256:fe43cb907c53cd6eedac1e0a167aceb283aaf00f3bf2d3cd411be5f15880d466 <runs[1].command aus dem Job>
```

Bewertung nach dem Pilot (ein Befehl je Lauf; GPU-Nutzung ebenfalls nur über
den FlowAgent, auf der CPU langsam, aber zulässig):

```bash
docker run --rm --gpus device=0 --user 1000:1000 \
  -v $HOME/donut:$HOME/donut \
  ghcr.io/janpow77/auditcore-donut-train@sha256:fe43cb907c53cd6eedac1e0a167aceb283aaf00f3bf2d3cd411be5f15880d466 \
  python -m auditcore_invoicesynth.train.evaluate \
  --dataset $HOME/donut/datasets/pilot-192e329e531ba160 \
  --run-dir $HOME/donut/runs/<lauf-id>-0 \
  --cord-model-dir $HOME/donut/base/donut-cord-v2 \
  --out $HOME/donut/eval/pilot-<lauf-id>-0.json
```

Ausgabe: Kurzfassung je Modell und Satz (Belegquote, Feldgenauigkeit, Abnahme E6,
Sekunden je Seite); vollständiger Bericht und Vorhersagen (`*.jsonl`) neben
`--out`. Donut-CORD wird nur auf Gesamt-, Netto- und Steuerbetrag abgebildet
(CORD kennt Rechnungsnummer, Datum, IBAN und USt-IdNr. nicht).

Rauchtest im Image auf dem GPU-Rechner (CPU, 26.09.2026): echtes `donut-base`,
je ein Schritt bei 1280×960 und 1536×1152 (Loss ≈ 12,6 bzw. 12,1, ≈ 15 s),
Checkpoint geschrieben, `progress.json` `fertig`; `train.evaluate` mit
Kandidat und Donut-CORD läuft durch (CPU ≈ 3,5 s je Seite bei 128 Token).
Sehr kleine Bildgrößen (z. B. 320×240) scheitern an der Fenstergröße 10 des
Swin-Encoders; die beiden Profilgrößen sind geprüft.

## Nächster Lauf: IBAN-Training am 3./4. Oktober 2026

Geplantes Rechnerfenster (Europe/Berlin): **Samstag, 03.10.2026, 08:00 Uhr,
bis Sonntag, 04.10.2026, 20:00 Uhr**. Die Uhrzeiten konkretisieren die Angabe
„Samstagmorgen bis Sonntagabend“. Der Lauf wird vorab als persistenter
`systemd --user`-Timer eingerichtet; nach dem Einschalten genügt das Erreichen
des Startzeitpunkts. Ein Einschalten nach 08:00 Uhr holt den Start wegen
`Persistent=true` nach.

### Befund und Trainingsänderung

- Stufe 3 erkennt auf T2 insgesamt 204 von 487 IBANs korrekt. Die Verteilung
  ist nicht kontinuierlich: `holdout_briefkopf` erreicht 204/215 (94,9 %),
  `holdout_kompakt` dagegen 0/272; dort fehlt die IBAN ausnahmslos.
- `holdout_kompakt` setzt die Bankdaten mit `bank="sender"` in den
  Absenderkopf. Keine der bisherigen acht Trainingsvorlagen verwendete diese
  Position. Größere Bilder und ein anderer Seed änderten das Fehlermuster nicht.
- Drei neue, geometrisch eigenständige Trainingsvorlagen `bank_kopf_*`
  verwenden Bankdaten im linken, rechten beziehungsweise zweispaltigen
  Absenderkopf. Die elf Trainingslayouts verteilen sich damit auf fünf mit
  Bankdaten in der Fußzeile, drei unter dem Summenblock und drei im
  Absenderkopf (rund 45/27/27 %). Die gut funktionierende Fußzeilenposition
  bleibt also die größte Gruppe; keine Holdout-Vorlage wird kopiert.
- Gruppierte und kompakte IBANs, DE/AT, 150/200/300 dpi, Schriften und
  Verfremdungen bleiben wie bisher gemischt. Der T2-Holdout bleibt unverändert.

### Automatischer Ablauf

1. Vor dem Wochenende: neuen Datensatz mit Seed 42 und 20 000/1 000/1 000/500
   Belegen erzeugen, Hash prüfen und Auftragsdatei mit festem Image-Digest
   ablegen; einen kleinen Rauchtest durchführen.
2. Am Samstag: GPU-Dienste kontrolliert über den FlowAgent freigeben und auf
   beiden Karten unabhängige Läufe mit sechs Epochen starten. GPU 0 nutzt
   1280×960, Batch 4 × Akkumulation 2, Seed 42; GPU 1 nutzt 1536×1152,
   Batch 2 × Akkumulation 4, Seed 43. Checkpoints werden weiter auf die Arbeitsstation
   gespiegelt und nach Stromausfall fortgesetzt.
3. Nach beiden Läufen: Kandidaten auf unverändertem T1/T2 bewerten, Bericht
   und Diagramme neu erzeugen und als Branch/PR ablegen.
4. Spätestens Sonntag 20:00 Uhr: laufende Container per SIGTERM mit Checkpoint
   beenden, GPU-Dienste wiederherstellen und den Abschlusszustand protokollieren.

### Auswahl- und Sicherheitskriterien

- Primär: IBAN auf `holdout_kompakt` mindestens 90 %, danach Zielschwelle E6
  von 97 % auf T2.
- Kein Rückgang eines Pflichtfelds auf T1 um mehr als einen Prozentpunkt
  gegenüber Stufe 3 Lauf 1.
- Jede ausgegebene IBAN muss `iban_valid()` bestehen. In Stufe 3 waren alle
  elf falschen T2-Ausgaben prüfziffer-ungültig und damit sicher verwerfbar.
- Wird die Zielschwelle nicht erreicht, wird kein Modell automatisch
  ausgerollt; die Ergebnisse bleiben ein bewerteter Kandidat. Nächster Versuch
  wäre ein IBAN-OCR-Fallback mit Modulo-97-Prüfung.

T3 (ausgedruckt/gescannt) und die vollständige Abnahme E6 bleiben danach offen.
