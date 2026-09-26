# Donut-Nachtraining (Etappe E3)

Stand 26.09.2026. Plan: `docs/architecture/DONUT_OCR_PLAN.md` 2c/2c-bis/2d,
Entscheidungen E1–E9 („Donut alle Empfehlungen“). Werkzeug, Job-Image,
Pilot- und Volldatensatz, Startmodell und FlowAgent-Job für janpow-ai sind
vorbereitet (Abschnitt [Stand E3 auf janpow-ai](#stand-e3-auf-janpow-ai)).
Das Training selbst startet ausschließlich über den FlowAgent.

## Bausteine (`auditcore_invoicesynth.train`)

| Baustein | Inhalt |
|---|---|
| `profiles` | `donut_train_janpow_ai` (Batch 4 je GPU, Akkumulation 2, AdamW, bf16, ≥ 14 GiB frei je Karte), `donut_train_8gb` (Batch 1, Akkumulation 16, 8-bit-AdamW, Gradient Checkpointing, ≥ 6,5 GiB frei), `cpu_smoke`; Startmodell `naver-clova-ix/donut-base@a959cf33…`; `config_hash` |
| `choose_topology` | aus GPU-Telemetrie: gleiche Kartenklasse ≥ 16 GiB → DDP (`torchrun --nproc_per_node=2`), ungleiche Karten → zwei Läufe (1280×960 / 1536×1152, Seed+1), eine Karte → single, keine → `unavailable` (kein stiller NUC-Rückfall) |
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
# NUC-Rückfall nur ausdrücklich
auditcore-invoicesynth-train --profile donut_train_8gb --dataset ds/ --run-dir runs/r1-nuc \
  --base-model-dir base/donut-base
# systemd --user-Dienst (xtts wird für den NUC-Rückfall pausiert, E7)
auditcore-invoicesynth-train --profile donut_train_8gb --systemd-unit --dataset ds/ \
  --run-dir runs/r1-nuc --base-model-dir base/donut-base \
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

## Nachweise dieser Runde (CPU, NUC, ohne GPU)

| Prüfung | Ergebnis |
|---|---|
| Stromausfall mit Ersatzmodell: Abbruch nach Schritt 6, halb geschriebener Checkpoint 8 | Wiederaufnahme ab 4, Loss-Verlauf und Endzustand identisch mit ununterbrochenem Lauf (`test_power_loss_resume_matches_uninterrupted_run`) |
| `kill -9` während eines laufenden Prozesses | Wiederaufnahme ab letztem gültigem Checkpoint, Schritte 1–40 lückenlos, Loss je Schritt identisch (`test_kill_9_during_training_resumes_from_last_valid_checkpoint`) |
| Winziges Donut-Modell (Swin 2 Stufen, MBart 1 Schicht, Zeichen-Tokenizer), 6 Schritte CPU, Abbruch nach 3, Wiederaufnahme | Loss von Schritt 3 vor/nach Wiederaufnahme gleich; Checkpoint enthält `model.safetensors`, Optimierer, Scheduler, RNG, Prüfsummen (`test_cpu_smoke_with_tiny_donut_model`; übersprungen ohne Extra `train`) |
| DDP mit `torchrun --nproc_per_node=2` (gloo, CPU) | 2 Ränge, ein Checkpoint von Rang 0 (manuell ausgeführt) |
| Rauchtest-Checkpoint in `auditcore_documents.LocalDonut` geladen | SHA-256 geprüft, Inferenz läuft (Zufallsausgabe), falsche Prüfsumme → `DONUT_MODEL_HASH_MISMATCH` (manuell ausgeführt) |

Getestet mit torch 2.14.0+cpu, transformers 5.17.0.

## Stand E3 auf janpow-ai

Verzeichnisse auf janpow-ai (Host → Container):

| Host | Container | Inhalt |
|---|---|---|
| `/home/janpow/donut/datasets/pilot-192e329e531ba160` | `/data/192e329e…` (ro) | Pilot 2 000 Belege (1 600/150/150/100) |
| `/home/janpow/donut/datasets/full-34581be2880d00f4` | `/data/34581be2…005d` (ro) | Vollsatz 20 000/1 000/1 000/500 (22 487 Trainingsbilder, 8,1 GB) |
| `/home/janpow/donut/base/donut-base` | `/srv/auditcore/donut/base/donut-base` (ro) | Startmodell, Revision a959cf33…, `SOURCE.json`, `SHA256SUMS` |
| `/home/janpow/donut/base/donut-cord-v2` | `/srv/auditcore/donut/base/donut-cord-v2` (ro) | nur Vergleich (Revision 8003d433…) |
| `/home/janpow/donut/runs` | `/srv/auditcore/donut/runs` (rw) | Läufe `<lauf-id>-0` (GPU 0) und `<lauf-id>-1` (GPU 1) |
| `/home/janpow/donut/eval` | `/srv/auditcore/donut/eval` (rw) | Bewertungsberichte |
| NUC `/home/janpow/donut/checkpoints-mirror/<lauf-id>/` | – | Checkpoint-Spiegel (rsync durch den FlowAgent) |

| Schritt | Stand |
|---|---|
| janpow-ai als Spoke, Telemetrie beider GPUs | RTX 5070 Ti (GPU 0) und RTX 5060 Ti (GPU 1), je 16 GB, Treiber 595.84 → `choose_topology`: **parallel** (zwei Läufe) |
| Job-Image | `ghcr.io/janpow77/auditcore-donut-train@sha256:fe43cb907c53cd6eedac1e0a167aceb283aaf00f3bf2d3cd411be5f15880d466` (Pilot-Stand `0.1.2+g54007a1606fc`, öffentlich, anonym ziehbar); spätere Builds verschieben nur den Tag `cu128`, der Job nennt den Digest (`--image`) |
| Startmodell | `pytorch_model.bin` SHA-256 `749f6e487d0cdbd7362d8b6a909174b93506d8631da0d15a6108bb6512ad5f48` (gleich dem Git-LFS-Objekt auf Hugging Face; `donut-base@a959cf33` hat keine safetensors-Datei) |
| Pilot-Datensatz | Hash `192e329e531ba16028c314f36007737637fdaaf59e0eb66095fb84a4056174f3`; zweimal unabhängig gebaut, gleicher Hash; `verify` ok |
| Vollsatz | Seed 42, Hash `34581be2880d00f4bb293fb0fc368770c2af61c7a748cdb55cf4c74a8324005d`, `verify` ok, Bauzeit 96 min (ein CPU-Kern) |
| FlowAgent-Jobs | `~/donut/job-pilot.json` (Lauf-ID `6cb8d70e0befc10e`, 3 Epochen, 675 Schritte je Lauf) und `~/donut/job-voll.json` (Lauf-ID `2835be42bd3c1e1a`, 6 Epochen, 16 866 Schritte je Lauf); Topologie jeweils `parallel`; Varianten `*-gpus-live.json` mit der Live-Telemetrie |
| Bewertung | `~/donut/tools/pilot-bewerten.sh [job.json]` (CPU; beide Läufe gegen T1/T2, Donut-CORD einmal; `LIMIT`/`MAXLEN`/`THREADS` optional) |
| FlowAgent-Seite (`train:donut`, GPU-Freigabe, Spiegel) | Session `flow-agent-f1`; Auftragsdateien `~/.config/flow-agent/gpu-auftraege/{donut-pilot,donut-voll}.json` |
| Morgenprüfung | `/home/janpow/donut/tools/morgen-pruefung.sh` (nur lesend: Zustand, Loss-Verlauf, Tempo, Restzeit, Stillstand, verworfene Checkpoints, GPUs, Dienste) |

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
  | python3 -c 'import json,sys; print(json.dumps([dict(index=int(i), name=n.strip(), memory_total_mib=int(t), memory_free_mib=int(f), host="janpow-ai") for i,n,t,f in (l.split(",") for l in sys.stdin)]))' \
  > ~/donut/gpus-live.json   # frei = gesamt − 512 MiB → gpus-nach-freigabe.json
docker run --rm --user 1000:1000 -v /home/janpow/donut:/home/janpow/donut \
  ghcr.io/janpow77/auditcore-donut-train@sha256:fe43cb907c53cd6eedac1e0a167aceb283aaf00f3bf2d3cd411be5f15880d466 \
  python -m auditcore_invoicesynth.train.cli --profile donut_train_janpow_ai \
  --dataset /home/janpow/donut/datasets/pilot-192e329e531ba160 --epochs 3 \
  --base-model-dir /home/janpow/donut/base/donut-base --run-dir /home/janpow/donut/runs \
  --base-model-sha256 749f6e487d0cdbd7362d8b6a909174b93506d8631da0d15a6108bb6512ad5f48 \
  --image ghcr.io/janpow77/auditcore-donut-train@sha256:fe43cb907c53cd6eedac1e0a167aceb283aaf00f3bf2d3cd411be5f15880d466 \\
  --plan --gpus-json /home/janpow/donut/gpus-nach-freigabe.json > ~/donut/job-pilot.json
```

Die Telemetrie zeigt belegte Karten (Ollama/Whisper); der Plan wird deshalb mit
dem Speicher **nach** der GPU-Freigabe durch den FlowAgent gerechnet (frei =
gesamt − 512 MiB). Mit belegten Karten meldet `--plan`
`WAITING_FOR_COMPUTE` (kein stiller Rückfall).

Ein Lauf im Container (so startet ihn der FlowAgent, je Karte ein Container):

```bash
docker run --rm --gpus device=1 --user 1000:1000 --ipc=host --stop-timeout 120 \
  -v /home/janpow/donut/datasets/pilot-192e329e531ba160:/data/<hash>:ro \
  -v /home/janpow/donut/base/donut-base:/srv/auditcore/donut/base/donut-base:ro \
  -v /home/janpow/donut/runs:/srv/auditcore/donut/runs \
  ghcr.io/janpow77/auditcore-donut-train@sha256:fe43cb907c53cd6eedac1e0a167aceb283aaf00f3bf2d3cd411be5f15880d466 <runs[1].command aus dem Job>
```

Bewertung nach dem Pilot (ein Befehl je Lauf; GPU-Nutzung ebenfalls nur über
den FlowAgent, auf der CPU langsam, aber zulässig):

```bash
docker run --rm --gpus device=0 --user 1000:1000 \
  -v /home/janpow/donut:/home/janpow/donut \
  ghcr.io/janpow77/auditcore-donut-train@sha256:fe43cb907c53cd6eedac1e0a167aceb283aaf00f3bf2d3cd411be5f15880d466 \
  python -m auditcore_invoicesynth.train.evaluate \
  --dataset /home/janpow/donut/datasets/pilot-192e329e531ba160 \
  --run-dir /home/janpow/donut/runs/<lauf-id>-0 \
  --cord-model-dir /home/janpow/donut/base/donut-cord-v2 \
  --out /home/janpow/donut/eval/pilot-<lauf-id>-0.json
```

Ausgabe: Kurzfassung je Modell und Satz (Belegquote, Feldgenauigkeit, Abnahme E6,
Sekunden je Seite); vollständiger Bericht und Vorhersagen (`*.jsonl`) neben
`--out`. Donut-CORD wird nur auf Gesamt-, Netto- und Steuerbetrag abgebildet
(CORD kennt Rechnungsnummer, Datum, IBAN und USt-IdNr. nicht).

Rauchtest im Image auf janpow-ai (CPU, 26.09.2026): echtes `donut-base`,
je ein Schritt bei 1280×960 und 1536×1152 (Loss ≈ 12,6 bzw. 12,1, ≈ 15 s),
Checkpoint geschrieben, `progress.json` `fertig`; `train.evaluate` mit
Kandidat und Donut-CORD läuft durch (CPU ≈ 3,5 s je Seite bei 128 Token).
Sehr kleine Bildgrößen (z. B. 320×240) scheitern an der Fenstergröße 10 des
Swin-Encoders; die beiden Profilgrößen sind geprüft.

## Was für E3 noch offen ist

1. FlowAgent: Runner `train:donut` mit GPU-Freigabe (whisper auf GPU 0,
   Ollama/ComfyUI auf GPU 1), Auftragsdateien, Checkpoint-Spiegel auf die NUC
   (flow-agent-f1).
2. Pilot 3 Epochen × 2 000 auf beiden Karten, VRAM-Spitze messen (Lauf 1:
   1536×1152, Batch 4; bei OOM Exit 4 → `--per-device-batch 2 --grad-accum 4`).
3. Stromausfall-Test auf der GPU (`kill -9` und SIGTERM während eines
   Checkpoints), danach Wiederaufnahme prüfen.
4. Bewertung des Piloten gegen Donut-CORD auf T1/T2 (Befehl oben); danach
   Volltraining (6 Epochen × 20 000) über Nacht. Frühes Anhalten auf der
   Validierung ist noch nicht eingebaut; ausgewählt wird per Bewertung.
5. T3 (ausgedruckt/gescannt) und die Abnahme E6 folgen nach dem Volltraining.
